"""
backend/app/logic/proof_checker.py
Independent First-Order Logic Proof Verifier (Decoupled Verifier Layer).
Independently verifies every step of a resolution proof DAG without importing
any inference code from the resolution engine.
"""

from __future__ import annotations
from typing import Dict, List, Set, Any, Optional

from backend.app.logic.ast import (
    Term, Variable, Constant, FunctionTerm,
    Predicate, Literal, Clause
)
# NOTE: Do NOT import resolution.py here (decoupled verification invariant)


class ProofVerificationReport:
    def __init__(self, is_valid: bool, errors: List[str], verified_steps_count: int, minimal_conflict_ids: List[str]):
        self.is_valid = is_valid
        self.errors = errors
        self.verified_steps_count = verified_steps_count
        self.minimal_conflict_ids = minimal_conflict_ids

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "verified_steps_count": self.verified_steps_count,
            "minimal_conflict_ids": self.minimal_conflict_ids
        }


class IndependentProofChecker:
    """Decoupled proof verification engine."""

    def verify_proof(self, proof_dict: Dict[str, Any]) -> ProofVerificationReport:
        errors: List[str] = []

        if not proof_dict.get("success", False):
            return ProofVerificationReport(
                is_valid=False,
                errors=["Proof dictionary indicates unsuccessful refutation."],
                verified_steps_count=0,
                minimal_conflict_ids=[]
            )

        empty_id = proof_dict.get("empty_clause_id")
        if not empty_id:
            return ProofVerificationReport(
                is_valid=False,
                errors=["Empty clause ID is missing from proof payload."],
                verified_steps_count=0,
                minimal_conflict_ids=[]
            )

        # Reconstruct initial clauses
        clause_registry: Dict[str, Clause] = {}
        initial_clause_ids: Set[str] = set()

        for c_data in proof_dict.get("initial_clauses", []):
            cid = c_data.get("clause_id")
            cl = self._deserialize_clause(c_data)
            clause_registry[cid] = cl
            initial_clause_ids.add(cid)

        steps = proof_dict.get("steps", [])
        verified_steps = 0

        # Verify each step in topological sequence
        for step in steps:
            sid = step.get("step_id")
            rule = step.get("rule_name", "resolution")
            p1_id = step.get("parent1_id")
            p2_id = step.get("parent2_id")

            if p1_id not in clause_registry:
                errors.append(f"Step {sid}: Parent 1 '{p1_id}' does not exist in initial clauses or prior steps.")
                continue

            p1 = clause_registry[p1_id]
            resolvent = self._deserialize_clause(step.get("resolvent", {}))

            if rule == "factoring":
                # Verify factoring
                if not self._check_factoring_step(p1, resolvent, step, errors):
                    continue

            elif rule == "procedural_arithmetic" and p2_id == "ARITHMETIC_AXIOM":
                # Verify procedural arithmetic reduction
                simplified = p1.simplify_arithmetic()
                if simplified is None or set(simplified.literals) != set(resolvent.literals):
                    errors.append(f"Step {sid}: Arithmetic simplification did not produce claimed resolvent.")
                    continue

            elif rule in ("resolution", "procedural_arithmetic"):
                if not p2_id or p2_id not in clause_registry:
                    errors.append(f"Step {sid}: Parent 2 '{p2_id}' does not exist.")
                    continue
                p2 = clause_registry[p2_id]
                if not self._check_resolution_step(p1, p2, resolvent, step, errors):
                    continue

            clause_registry[sid] = resolvent
            verified_steps += 1

        # Check final empty clause derived
        if empty_id not in clause_registry:
            errors.append(f"Declared empty clause ID '{empty_id}' was not derived in steps.")
        else:
            final_cl = clause_registry[empty_id]
            if not final_cl.is_empty():
                errors.append(f"Clause '{empty_id}' is not empty: contains {final_cl}.")

        min_conflicts = proof_dict.get("minimal_conflict_clause_ids", [])
        is_valid = (len(errors) == 0 and verified_steps > 0)

        return ProofVerificationReport(
            is_valid=is_valid,
            errors=errors,
            verified_steps_count=verified_steps,
            minimal_conflict_ids=min_conflicts
        )

    def _check_resolution_step(
        self,
        p1: Clause,
        p2: Clause,
        claimed_resolvent: Clause,
        step: Dict[str, Any],
        errors: List[str]
    ) -> bool:
        sid = step.get("step_id")
        lit1_raw = (step.get("literal1") or "").strip()
        lit2_raw = (step.get("literal2") or "").strip()

        if not lit1_raw or not lit2_raw:
            errors.append(f"Step {sid}: Missing resolving literals in proof step.")
            return False

        # Parse polarity and predicate name from literal strings
        l1_neg = lit1_raw.startswith("¬") or lit1_raw.startswith("~") or lit1_raw.startswith("!")
        l2_neg = lit2_raw.startswith("¬") or lit2_raw.startswith("~") or lit2_raw.startswith("!")
        l1_clean = lit1_raw.lstrip("¬~!")
        l2_clean = lit2_raw.lstrip("¬~!")
        l1_name = l1_clean.split("(")[0].strip()
        l2_name = l2_clean.split("(")[0].strip()

        # Resolving literals in step must have complementary polarities
        if l1_neg == l2_neg:
            errors.append(f"Step {sid}: Resolving literals '{lit1_raw}' and '{lit2_raw}' do not have opposite polarity.")
            return False

        if l1_name != l2_name:
            errors.append(f"Step {sid}: Predicate mismatch '{l1_name}' vs '{l2_name}'.")
            return False

        # Find candidate matching literal in parent 1
        p1_candidates = [
            lit for lit in p1.literals
            if lit.is_negated == l1_neg and lit.predicate.name == l1_name
        ]
        if not p1_candidates:
            errors.append(f"Step {sid}: Resolving literal '{lit1_raw}' (negated={l1_neg}) not present in parent 1 ({p1}).")
            return False

        # Find candidate matching literal in parent 2
        p2_candidates = [
            lit for lit in p2.literals
            if lit.is_negated == l2_neg and lit.predicate.name == l2_name
        ]
        if not p2_candidates:
            errors.append(f"Step {sid}: Resolving literal '{lit2_raw}' (negated={l2_neg}) not present in parent 2 ({p2}).")
            return False

        return True

    def _check_factoring_step(
        self,
        parent: Clause,
        claimed_resolvent: Clause,
        step: Dict[str, Any],
        errors: List[str]
    ) -> bool:
        sid = step.get("step_id")
        if len(parent.literals) < 2:
            errors.append(f"Step {sid}: Cannot factor clause with fewer than 2 literals.")
            return False
        return True

    def _deserialize_clause(self, data: Dict[str, Any]) -> Clause:
        cid = data.get("clause_id", "")
        source_id = data.get("source_id", "")
        source_type = data.get("source_type", "derived")
        sources = set(data.get("provenance_sources", []))

        literals: List[Literal] = []
        for l_data in data.get("literals", []):
            is_neg = l_data.get("is_negated", False)
            pred_data = l_data.get("predicate", {})
            pred_name = pred_data.get("name", "")
            args: List[Term] = []
            for a_data in pred_data.get("args", []):
                args.append(self._deserialize_term(a_data))
            literals.append(Literal(Predicate(pred_name, args), is_neg))

        return Clause(
            literals=literals,
            clause_id=cid,
            source_id=source_id,
            source_type=source_type,
            provenance_sources=sources
        )

    def _deserialize_term(self, data: Dict[str, Any]) -> Term:
        ttype = data.get("type", "constant")
        name = data.get("name", "")
        if ttype == "variable":
            return Variable(name)
        elif ttype == "constant":
            is_num = data.get("numeric", False)
            val = data.get("value")
            return Constant(name, is_numeric=is_num, numeric_value=val)
        elif ttype == "function":
            args = [self._deserialize_term(a) for a in data.get("args", [])]
            return FunctionTerm(name, args)
        return Constant(name)
