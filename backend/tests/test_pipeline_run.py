"""
backend/tests/test_pipeline_run.py
End-to-end integration test verifying the 10-stage pipeline on Sample B:
- 16 clauses segmented
- 2 provable contradictions detected by FOPL engine
- Statutory rule hits (R01, R02, R03, R04, R05)
- Independent proof verifier passes
"""

import pytest
import asyncio
import os

from backend.app.agents.pipeline import AnalysisPipeline
from backend.app.models.clause_ir import FindingKind, Severity, VerificationStatus


def test_pipeline_on_sample_b():
    sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "samples", "sample_b_problematic.txt")
    with open(sample_path, "r", encoding="utf-8") as f:
        text = f.read()

    pipeline = AnalysisPipeline()
    events = []
    final_payload = None

    for event in pipeline.run_pipeline_sync(text):
        events.append(event)
        if event.stage == "complete":
            final_payload = event.payload

    assert final_payload is not None
    assert len(final_payload["clauses"]) == 16

    findings = final_payload["findings"]
    conflicts = [f for f in findings if f["kind"] == FindingKind.CONFLICT]

    # Must prove AT LEAST 2 internal contradictions
    assert len(conflicts) >= 2, f"Expected at least 2 proved conflicts, got {len(conflicts)}"

    # Check the 2 conflicts
    affected_pairs = [tuple(sorted(f["affected_clause_ids"])) for f in conflicts]
    assert ("Clause_12", "Clause_3") in affected_pairs
    assert ("Clause_16", "Clause_7") in affected_pairs

    # Check statutory rule hits
    rule_ids = {f["rule_id"] for f in findings if f["rule_id"]}
    assert "R01" in rule_ids  # Deposit > 2 months
    assert "R02" in rule_ids  # Unrestricted entry
    assert "R03" in rule_ids  # Rent increase without 3 months notice
    assert "R04" in rule_ids  # Utilities cut off remedy
    assert "R05" in rule_ids  # Forfeiture penalty

    # Check verifier status
    # Legal risk findings must have status "needs_review" because source_text is unreviewed
    legal_risks = [f for f in findings if f["kind"] == FindingKind.LEGAL_RISK]
    for lr in legal_risks:
        assert lr["verification"]["status"] == VerificationStatus.NEEDS_REVIEW
        assert any("Unreviewed rule" in c["detail"] for c in lr["verification"]["checks"])

    # Proved conflicts must be VERIFIED by the decoupled proof verifier
    for cf in conflicts:
        assert cf["verification"]["status"] == VerificationStatus.VERIFIED


def test_what_if_query_answering():
    sample_path = os.path.join(os.path.dirname(__file__), "..", "..", "samples", "sample_b_problematic.txt")
    with open(sample_path, "r", encoding="utf-8") as f:
        text = f.read()

    pipeline = AnalysisPipeline()
    final_payload = None
    for event in pipeline.run_pipeline_sync(text):
        if event.stage == "complete":
            final_payload = event.payload

    from backend.app.models.clause_ir import ClauseIR
    clauses = [ClauseIR(**c) for c in final_payload["clauses"]]

    # Query 1: Can tenant terminate early?
    ans1 = pipeline.answer_what_if("Can the tenant terminate early?", clauses, final_payload["clean_text"])
    assert ans1["answered"] is True

    # Query 2: Can tenant keep pets?
    ans2 = pipeline.answer_what_if("Are pets allowed in the apartment?", clauses, final_payload["clean_text"])
    assert ans2["answered"] is True
