"""
backend/app/agents/verifiers/explanation_verifier.py
Independent Explanation Verifier.
Verifies that:
1. Every cited clause ID exists in the original contract (no hallucinated IDs).
2. Quoted text in explanations matches the contract text verbatim.
3. Legal risk findings are 'Verified' only if their governing rule has a non-empty
   source_url and source_text; otherwise status is gated to 'Needs review'.
"""

from __future__ import annotations
import re
from typing import List, Set

from backend.app.models.clause_ir import (
    Finding, FindingKind, VerificationResult, VerificationStatus, VerificationCheck
)


class ExplanationVerifier:
    """Decoupled verifier for finding summaries, citations, and plain-English explanations."""

    @classmethod
    def verify_finding(
        cls,
        finding: Finding,
        valid_clause_ids: Set[str],
        contract_raw_text: str
    ) -> Finding:
        checks: List[VerificationCheck] = []
        is_verified = True

        # Check 1: Valid Clause IDs cited
        cited_ids = set(re.findall(r"\bClause_[0-9]+(?:_[0-9]+)?\b", finding.plain_explanation))
        cited_ids.update(finding.affected_clause_ids)
        invalid_ids = cited_ids - valid_clause_ids

        clause_check_passed = (len(invalid_ids) == 0)
        checks.append(VerificationCheck(
            name="Clause Reference Integrity",
            passed=clause_check_passed,
            detail="All referenced clause IDs exist in contract" if clause_check_passed else f"Hallucinated clause IDs: {list(invalid_ids)}"
        ))
        if not clause_check_passed:
            is_verified = False

        # Check 2: Verbatim Quoting Check
        # Check quoted strings in explanation
        quotes_in_expl = re.findall(r"[\"']([^\"']{8,})[\"']", finding.plain_explanation)
        unmatched_quotes = []
        for q in quotes_in_expl:
            if q not in contract_raw_text and q not in finding.evidence_quote:
                unmatched_quotes.append(q)

        quote_check_passed = (len(unmatched_quotes) == 0)
        checks.append(VerificationCheck(
            name="Verbatim Quote Verification",
            passed=quote_check_passed,
            detail="All quoted statements match the agreement verbatim" if quote_check_passed else f"Non-verbatim quotes detected: {unmatched_quotes[:2]}"
        ))
        if not quote_check_passed:
            is_verified = False

        # Check 3: Legal Risk Statutory Source Verification
        if finding.kind == FindingKind.LEGAL_RISK:
            has_source_url = bool(finding.source and finding.source.source_url)
            has_source_text = bool(finding.source and finding.source.source_text.strip())
            is_reviewed = bool(finding.source and finding.source.reviewed)

            source_complete = has_source_url and has_source_text and is_reviewed
            checks.append(VerificationCheck(
                name="Statutory Certification",
                passed=source_complete,
                detail="Official statute citation certified by legal practitioner" if source_complete else "Unreviewed rule (source text pending advocate review)"
            ))
            if not source_complete:
                is_verified = False

        # Combine with existing checks if any
        if finding.verification and finding.verification.checks:
            combined_checks = finding.verification.checks + checks
        else:
            combined_checks = checks

        status = VerificationStatus.VERIFIED if is_verified and all(c.passed for c in combined_checks) else VerificationStatus.NEEDS_REVIEW
        finding.verification = VerificationResult(status=status, checks=combined_checks)
        return finding

