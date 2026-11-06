"""
backend/app/agents/pipeline.py
Pipeline Orchestrator State Machine for ClauseLens.
Executes the 10-stage compliance pipeline and yields real-time SSE progress events.
"""

from __future__ import annotations
import os
import time
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator, Generator, Tuple, Set

from backend.app.agents.ingest import DocumentIngester
from backend.app.agents.segmenter import ContractSegmenter, ClauseSegment
from backend.app.agents.extractor import get_extractor, LLMProvider
from backend.app.agents.verifiers.extraction_verifier import ExtractionVerifier
from backend.app.agents.translator import ClauseTranslator
from backend.app.agents.explainer import Explainer
from backend.app.agents.verifiers.explanation_verifier import ExplanationVerifier
from backend.app.kb.retriever import RuleRetriever
from backend.app.models.clause_ir import (
    ClauseIR, Finding, FindingKind, Severity, VerificationStatus, ActionOntology
)
from backend.app.logic.ast import Clause
from backend.app.logic.parser import parse_fopl
from backend.app.logic.cnf import CNFConverter
from backend.app.logic.resolution import ResolutionProver, ResolutionOutcome, ProofResult
from backend.app.logic.proof_checker import IndependentProofChecker


class PipelineEvent:
    def __init__(self, stage: str, status: str, duration_ms: int, detail: str, payload: Optional[Dict[str, Any]] = None):
        self.stage = stage
        self.status = status
        self.duration_ms = duration_ms
        self.detail = detail
        self.payload = payload

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "stage": self.stage,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "detail": self.detail
        }
        if self.payload is not None:
            d["payload"] = self.payload
        return d


class AnalysisPipeline:
    """Orchestrates ingestion, segmentation, extraction, verification, reasoning, and reporting."""

    def __init__(self):
        self.rule_retriever = RuleRetriever()
        self.cnf_converter = CNFConverter()
        self.prover = ResolutionProver(max_clauses=400, timeout_seconds=0.5)
        self.proof_checker = IndependentProofChecker()
        self._load_domain_axioms()

    def _load_domain_axioms(self) -> None:
        """Loads and compiles deontic domain axioms from backend/app/kb/axioms.fol."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        axiom_path = os.path.join(base_dir, "kb", "axioms.fol")
        self.axiom_clauses: List[Clause] = []

        if not os.path.exists(axiom_path):
            return

        with open(axiom_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        ax_idx = 1
        for line in lines:
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                continue
            try:
                formula = parse_fopl(line_str)
                clauses, _ = self.cnf_converter.convert_with_steps(
                    formula, source_id=f"AXIOM_{ax_idx}", source_type="axiom"
                )
                self.axiom_clauses.extend(clauses)
                ax_idx += 1
            except Exception:
                continue

    def run_pipeline_sync(
        self,
        raw_text: str,
        redact_pii: bool = False
    ) -> Generator[PipelineEvent, None, None]:
        """Runs the 10-stage pipeline synchronously, yielding progress events."""

        # -------------------------------------------------------------
        # Stage 1: Ingest & Normalization
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        yield PipelineEvent("ingest", "running", 0, "Normalizing document text and applying privacy filters...")

        clean_text, ingest_meta = DocumentIngester.process(raw_text, redact_pii=redact_pii)
        t_ingest = int((time.perf_counter() - t0) * 1000)
        yield PipelineEvent(
            "ingest", "completed", t_ingest,
            f"Normalized {len(clean_text)} characters. Redactions: {ingest_meta['redactions']}"
        )

        # -------------------------------------------------------------
        # Stage 2: Clause Segmenter
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        yield PipelineEvent("segment", "running", 0, "Segmenting text into distinct numbered clauses...")

        raw_segments = ContractSegmenter.segment(clean_text)
        t_segment = int((time.perf_counter() - t0) * 1000)
        yield PipelineEvent(
            "segment", "completed", t_segment,
            f"Segmented {len(raw_segments)} contractual clauses with character offset spans."
        )

        # -------------------------------------------------------------
        # Stage 3: Extractor
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        extractor = get_extractor()
        yield PipelineEvent(
            "extract", "running", 0,
            f"Extracting structured ClauseIR models ({extractor.get_mode_name()} mode)..."
        )

        extracted_clauses: List[ClauseIR] = []
        for seg in raw_segments:
            c_ir = extractor.extract_clause(seg, clean_text)
            extracted_clauses.append(c_ir)

        t_extract = int((time.perf_counter() - t0) * 1000)
        yield PipelineEvent(
            "extract", "completed", t_extract,
            f"Extracted {len(extracted_clauses)} ClauseIR items across closed action ontology."
        )

        # -------------------------------------------------------------
        # Stage 4: Extraction Verifier
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        yield PipelineEvent("verify_extraction", "running", 0, "Running independent dual-pass and pure-code grounding checks...")

        verified_clauses: List[ClauseIR] = []
        verified_count = 0
        for c in extracted_clauses:
            v_c, v_res = ExtractionVerifier.verify_clause(c)
            verified_clauses.append(v_c)
            if v_res.status == VerificationStatus.VERIFIED:
                verified_count += 1

        t_v_extract = int((time.perf_counter() - t0) * 1000)
        yield PipelineEvent(
            "verify_extraction", "completed", t_v_extract,
            f"Verified {verified_count}/{len(verified_clauses)} extractions grounded verbatim in source."
        )

        # -------------------------------------------------------------
        # Stage 5: Deterministic FOPL Translator
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        yield PipelineEvent("translate", "running", 0, "Translating ClauseIR instances to First-Order Logic formulas...")

        fopl_clauses: List[Clause] = []
        clause_fopl_map: Dict[str, str] = {}
        for c in verified_clauses:
            trans_res = ClauseTranslator.translate_to_fopl(c)
            if trans_res:
                formula_str, _ = trans_res
                clause_fopl_map[c.id] = formula_str
                try:
                    f = parse_fopl(formula_str)
                    cls_set, _ = self.cnf_converter.convert_with_steps(f, source_id=c.id, source_type="contract")
                    fopl_clauses.extend(cls_set)
                except Exception:
                    pass

        t_translate = int((time.perf_counter() - t0) * 1000)
        yield PipelineEvent(
            "translate", "completed", t_translate,
            f"Translated {len(fopl_clauses)} FOPL clausal constraints from {len(clause_fopl_map)} clauses."
        )

        # -------------------------------------------------------------
        # Stage 6 & 7: Reasoner (Logic-Based Compliance Engine) & Proof Verifier
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        yield PipelineEvent("reason", "running", 0, "Executing resolution refutation theorem prover over domain axioms...")

        clauses_by_id = {c.id: c for c in verified_clauses}
        conflict_findings: List[Finding] = []
        proved_conflict_pairs: Set[Tuple[str, str]] = set()

        # Targeted conflict discovery: group clauses by action domain
        action_groups: Dict[str, List[str]] = {}
        for c in verified_clauses:
            if c.action != ActionOntology.OTHER and c.id in clause_fopl_map:
                action_groups.setdefault(c.action.value, []).append(c.id)

        pairs_to_test: List[Tuple[str, str]] = []
        for act, cids in action_groups.items():
            if len(cids) >= 2:
                for i in range(len(cids)):
                    for j in range(i + 1, len(cids)):
                        pairs_to_test.append((cids[i], cids[j]))

        deduped_pairs = list(set(tuple(sorted(p)) for p in pairs_to_test))

        for id1, id2 in deduped_pairs:
            # Select relevant subset of clauses
            c1_sub = [c for c in fopl_clauses if c.source_id == id1]
            c2_sub = [c for c in fopl_clauses if c.source_id == id2]

            if not c1_sub or not c2_sub:
                continue

            test_kb = c1_sub + c2_sub + self.axiom_clauses
            res = self.prover.prove(test_kb)

            if res.outcome == ResolutionOutcome.REFUTATION_FOUND:
                conflicts = res.minimal_conflict_clause_ids
                contract_conflicts = sorted([cid for cid in conflicts if cid.startswith("Clause_")])
                if len(contract_conflicts) >= 2:
                    pair_key = (contract_conflicts[0], contract_conflicts[1])
                    if pair_key not in proved_conflict_pairs:
                        proved_conflict_pairs.add(pair_key)
                        
                        # Stage 7: Independent Proof Verifier Check
                        proof_dict = res.to_dict()
                        v_report = self.proof_checker.verify_proof(proof_dict)
                        
                        finding = Explainer.explain_conflict(
                            conflict_id=f"F_CONFLICT_{pair_key[0]}_{pair_key[1]}",
                            clause_ids=contract_conflicts,
                            clauses_by_id=clauses_by_id,
                            proof_result=res
                        )
                        if not v_report.is_valid:
                            finding.verification.status = VerificationStatus.NEEDS_REVIEW
                        conflict_findings.append(finding)

        t_reason = int((time.perf_counter() - t0) * 1000)
        yield PipelineEvent(
            "reason", "completed", t_reason,
            f"Proved {len(conflict_findings)} formal contradiction(s) via resolution refutation."
        )

        # -------------------------------------------------------------
        # Stage 8: Rule Retriever & Risk Assessor
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        yield PipelineEvent("retrieve_rules", "running", 0, "Evaluating Indian Residential Tenancy rules & CWA missing checks...")

        rule_findings = self.rule_retriever.evaluate_rules_on_clauses(verified_clauses)
        t_rules = int((time.perf_counter() - t0) * 1000)
        yield PipelineEvent(
            "retrieve_rules", "completed", t_rules,
            f"Identified {len(rule_findings)} statutory and advisory findings against Indian Tenancy pack."
        )

        # -------------------------------------------------------------
        # Stage 9 & 10: Explanation Verification & Report Assembly
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        yield PipelineEvent("explain", "running", 0, "Verifying explanation quotes and generating tenant negotiation advice...")

        all_findings = conflict_findings + rule_findings
        valid_ids = {c.id for c in verified_clauses}

        final_findings: List[Finding] = []
        for f in all_findings:
            v_finding = ExplanationVerifier.verify_finding(f, valid_ids, clean_text)
            final_findings.append(v_finding)

        # Calculate high/medium/low severity counts
        sev_counts = {
            "high": sum(1 for f in final_findings if f.severity == Severity.HIGH),
            "medium": sum(1 for f in final_findings if f.severity == Severity.MEDIUM),
            "low": sum(1 for f in final_findings if f.severity == Severity.LOW),
            "info": sum(1 for f in final_findings if f.severity == Severity.INFO),
            "conflict": len(conflict_findings)
        }

        # Overall risk index (0 to 100)
        raw_score = (sev_counts["high"] * 25) + (sev_counts["medium"] * 10) + (sev_counts["low"] * 5)
        risk_score = min(100, raw_score)

        t_complete = int((time.perf_counter() - t0) * 1000)
        yield PipelineEvent(
            "complete", "completed", t_complete,
            f"Audit finished. Overall Risk Score: {risk_score}/100.",
            payload={
                "clean_text": clean_text,
                "clauses": [c.model_dump() for c in verified_clauses],
                "findings": [f.model_dump() for f in final_findings],
                "severity_counts": sev_counts,
                "risk_score": risk_score,
                "pii_redacted": redact_pii,
                "llm_mode": extractor.get_mode_name()
            }
        )

    async def run_pipeline(
        self,
        raw_text: str,
        redact_pii: bool = False
    ) -> AsyncGenerator[PipelineEvent, None]:
        """Runs the 10-stage pipeline asynchronously for SSE streaming."""
        for event in self.run_pipeline_sync(raw_text, redact_pii=redact_pii):
            yield event
            await asyncio.sleep(0.005)

    def answer_what_if(
        self,
        question: str,
        clauses: List[ClauseIR],
        clean_text: str
    ) -> Dict[str, Any]:
        """Processes a 'What-If' user query against contract clauses and logic axioms."""
        q_low = question.lower()

        # Constrained Intent List
        intent = "GeneralInquiry"
        if "terminate" in q_low or "vacate" in q_low or "leave early" in q_low or "break lease" in q_low:
            intent = "CanTenantTerminateEarly"
        elif "deposit" in q_low or "refundable" in q_low or "get back" in q_low:
            intent = "IsDepositRefundable"
        elif "enter" in q_low or "inspection" in q_low or "any time" in q_low or "visit" in q_low:
            intent = "CanLandlordEnterAnytime"
        elif "increase" in q_low or "hike" in q_low or "raise rent" in q_low:
            intent = "CanRentIncreaseMidTerm"
        elif "repair" in q_low or "maintenance" in q_low or "leakage" in q_low:
            intent = "WhoPaysRepairs"
        elif "sublet" in q_low or "sub-lease" in q_low or "roommate" in q_low:
            intent = "IsSubletAllowed"
        elif "pet" in q_low or "dog" in q_low or "cat" in q_low:
            intent = "CanKeepPets"

        # Attempt formal proof for known intents
        proof: Optional[ProofResult] = None
        grounded_clauses: List[ClauseIR] = []

        if intent == "CanTenantTerminateEarly":
            term_clauses = [c for c in clauses if c.action.value == "Terminate"]
            grounded_clauses = term_clauses
            if term_clauses:
                # Query: Perm(tenant, Terminate(n))
                # Add ~Perm(tenant, Terminate(30)) and test refutation
                c_trans = [ClauseTranslator.translate_to_fopl(c) for c in term_clauses]
                kb_clauses = []
                for res in c_trans:
                    if res:
                        f = parse_fopl(res[0])
                        cl_set, _ = self.cnf_converter.convert_with_steps(f, source_id="ContractTerm")
                        kb_clauses.extend(cl_set)

                goal_f = parse_fopl("~Perm(tenant, Terminate(30))")
                goal_cl, _ = self.cnf_converter.convert_with_steps(goal_f, source_id="GOAL", source_type="goal")
                proof = self.prover.prove(kb_clauses + goal_cl + self.axiom_clauses)

        elif intent == "CanKeepPets":
            pet_clauses = [c for c in clauses if c.action.value == "KeepPets"]
            grounded_clauses = pet_clauses
            if pet_clauses:
                c_trans = [ClauseTranslator.translate_to_fopl(c) for c in pet_clauses]
                kb_clauses = []
                for res in c_trans:
                    if res:
                        f = parse_fopl(res[0])
                        cl_set, _ = self.cnf_converter.convert_with_steps(f, source_id="ContractPet")
                        kb_clauses.extend(cl_set)
                goal_f = parse_fopl("~Perm(tenant, KeepPets)")
                goal_cl, _ = self.cnf_converter.convert_with_steps(goal_f, source_id="GOAL", source_type="goal")
                proof = self.prover.prove(kb_clauses + goal_cl + self.axiom_clauses)

        elif intent == "CanLandlordEnterAnytime":
            entry_clauses = [c for c in clauses if c.action.value == "EnterPremises"]
            grounded_clauses = entry_clauses
            if entry_clauses:
                c_trans = [ClauseTranslator.translate_to_fopl(c) for c in entry_clauses]
                kb_clauses = []
                for res in c_trans:
                    if res:
                        f = parse_fopl(res[0])
                        cl_set, _ = self.cnf_converter.convert_with_steps(f, source_id="ContractEntry")
                        kb_clauses.extend(cl_set)
                goal_f = parse_fopl("~Perm(landlord, EnterPremises(unrestricted))")
                goal_cl, _ = self.cnf_converter.convert_with_steps(goal_f, source_id="GOAL", source_type="goal")
                proof = self.prover.prove(kb_clauses + goal_cl + self.axiom_clauses)

        # Build response
        return Explainer.explain_query_answer(question, intent, proof, grounded_clauses)
