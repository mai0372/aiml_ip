"""
backend/app/agents/extractor.py
Pluggable ClauseIR Extractor.
Supports two modes:
  1. Fully Offline Mode (Default): Deterministic regex and lexical pattern extractor
     over the fixed ontology. Requires zero network, zero API key, runs instantaneously.
  2. Gemini LLM Mode (Optional): Uses google-genai SDK with structured Pydantic output,
     prioritizing evidence quotes before structured extraction.
"""

from __future__ import annotations
import os
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from backend.app.models.clause_ir import (
    ClauseIR, ClauseSpan, ClauseType, Party, Modality,
    ActionOntology, ClauseParams
)
from backend.app.agents.segmenter import ClauseSegment


class LLMProvider(ABC):
    """Abstract interface for clause extraction and query answering."""

    @abstractmethod
    def extract_clause(self, segment: ClauseSegment, full_text: str = "") -> ClauseIR:
        pass

    @abstractmethod
    def get_mode_name(self) -> str:
        pass


class OfflineExtractor(LLMProvider):
    """
    Deterministic rule-based extractor.
    Extracts structured ClauseIR using keyword patterns and regular expressions
    over the closed action ontology. Guarantees 100% reproducible results offline.
    """

    def get_mode_name(self) -> str:
        return "offline"

    def extract_clause(self, segment: ClauseSegment, full_text: str = "") -> ClauseIR:
        text = segment.text
        text_lower = text.lower()

        # 1. Detect ClauseType
        clause_type = self._detect_clause_type(text_lower)

        # 2. Detect Party
        party = self._detect_party(text_lower)

        # 3. Detect Modality
        modality = self._detect_modality(text_lower)

        # 4. Detect Action
        action = self._detect_action(clause_type, modality, text_lower)

        # 5. Extract Numeric Parameters
        params = self._extract_params(text)

        # 6. Extract verbatim evidence quote
        evidence_quote = self._extract_evidence_quote(text, clause_type, action)

        return ClauseIR(
            id=segment.clause_id,
            raw_number=segment.raw_number,
            text=text,
            span=segment.span,
            clause_type=clause_type,
            party=party,
            modality=modality,
            action=action,
            params=params,
            conditions=[],
            exceptions=[],
            evidence_quote=evidence_quote,
            confidence=0.95,
            internal_reasoning=f"Offline deterministic regex matched type '{clause_type.value}' and action '{action.value}'"
        )

    def _detect_clause_type(self, t: str) -> ClauseType:
        if "lock-in" in t or "lock in" in t:
            return ClauseType.LOCK_IN
        if "pet" in t or "animal" in t or "dog" in t or "cat" in t:
            return ClauseType.PETS
        if "forfeit" in t or "liquidated damage" in t or "penalty" in t or "late fee" in t:
            return ClauseType.PENALTY
        if "disconnect" in t or "cut" in t or "electricity" in t or "water charges" in t or "utility" in t:
            return ClauseType.UTILITIES
        if "inspect" in t or "right of entry" in t or "enter and inspect" in t or "enter the premises" in t:
            return ClauseType.ENTRY
        if "terminate" in t or "termination" in t or "vacate" in t or "notice to vacate" in t:
            return ClauseType.TERMINATION
        if "security deposit" in t or "advance amount" in t or "security advance" in t or "refundable deposit" in t:
            return ClauseType.DEPOSIT
        if "rent" in t and ("increase" in t or "revision" in t or "escalation" in t or "revise" in t):
            return ClauseType.RENT_INCREASE
        if "monthly rent" in t or "rent of rs" in t or "pay as rent" in t or "rent payment" in t:
            return ClauseType.RENT
        if "repair" in t or "maintenance" in t or "upkeep" in t:
            return ClauseType.REPAIRS
        if "sublet" in t or "sub-let" in t or "assign or otherwise" in t:
            return ClauseType.SUBLETTING
        if "tenancy shall be for" in t or "period of tenancy" in t or "duration" in t or "eleven months" in t:
            return ClauseType.TERM
        if "renew" in t or "extension" in t:
            return ClauseType.RENEWAL
        if "register" in t or "registration" in t:
            return ClauseType.REGISTRATION
        return ClauseType.MISC

    def _detect_party(self, t: str) -> Party:
        # Determine focal party of obligation or prohibition
        has_tenant = "tenant" in t or "lessee" in t or "2nd party" in t
        has_landlord = "landlord" in t or "lessor" in t or "house owner" in t or "1st party" in t

        if has_tenant and not has_landlord:
            return Party.TENANT
        if has_landlord and not has_tenant:
            return Party.LANDLORD

        # Contextual subject analysis
        if "tenant shall" in t or "tenant is permitted" in t or "tenant is strictly" in t or "termination by the tenant" in t:
            return Party.TENANT
        if "landlord shall" in t or "landlord reserves" in t or "landlord may" in t or "lessor may" in t:
            return Party.LANDLORD
        if "either party" in t or "both parties" in t:
            return Party.BOTH

        return Party.TENANT if has_tenant else (Party.LANDLORD if has_landlord else Party.BOTH)

    def _detect_modality(self, t: str) -> Modality:
        if "strictly prohibited" in t or "forbidden" in t or "shall not" in t or "cannot" in t or "under no circumstances" in t:
            return Modality.PROHIBITION
        if "permitted" in t or "may" in t or "right to" in t or "liberty to" in t or "allowed" in t:
            return Modality.PERMISSION
        if "shall" in t or "agrees to" in t or "must" in t or "required to" in t or "obliged" in t:
            return Modality.OBLIGATION
        return Modality.DEFINITION

    def _detect_action(self, ctype: ClauseType, mod: Modality, t: str) -> ActionOntology:
        if ctype == ClauseType.TERMINATION:
            return ActionOntology.TERMINATE
        if ctype == ClauseType.DEPOSIT:
            if "refund" in t or "returned" in t:
                return ActionOntology.REFUND_DEPOSIT
            return ActionOntology.PAY_DEPOSIT
        if ctype == ClauseType.RENT:
            return ActionOntology.PAY_RENT
        if ctype == ClauseType.ENTRY:
            return ActionOntology.ENTER_PREMISES
        if ctype == ClauseType.UTILITIES:
            if "disconnect" in t or "cut" in t:
                return ActionOntology.CUT_UTILITIES
            return ActionOntology.OTHER
        if ctype == ClauseType.PENALTY:
            if "forfeit" in t:
                return ActionOntology.FORFEIT_DEPOSIT
            if "late fee" in t or "interest" in t:
                return ActionOntology.CHARGE_LATE_FEE
        if ctype == ClauseType.RENT_INCREASE:
            return ActionOntology.INCREASE_RENT
        if ctype == ClauseType.SUBLETTING:
            return ActionOntology.SUBLET
        if ctype == ClauseType.REPAIRS:
            return ActionOntology.REPAIR
        if ctype == ClauseType.RENEWAL:
            return ActionOntology.RENEW
        if ctype == ClauseType.PETS:
            return ActionOntology.KEEP_PETS

        return ActionOntology.OTHER

    def _extract_params(self, text: str) -> ClauseParams:
        params = ClauseParams()
        extra: Dict[str, Any] = {}

        # 1. INR Amount
        amt_match = re.search(r"(?:Rs\.?|INR|₹)\s*([0-9,]+)", text, re.IGNORECASE)
        if amt_match:
            try:
                amt_str = amt_match.group(1).replace(",", "")
                params.amount_inr = float(amt_str)
            except ValueError:
                pass

        # 2. Notice Days
        notice_match = re.search(r"([0-9]{1,3})\s*(?:calendar\s*)?days?\s*(?:advance|prior)?\s*(?:written)?\s*notice", text, re.IGNORECASE)
        if not notice_match:
            notice_match = re.search(r"notice\s*of\s*([0-9]{1,3})\s*days", text, re.IGNORECASE)
        if notice_match:
            try:
                params.notice_days = int(notice_match.group(1))
            except ValueError:
                pass

        # Word numbers for notice: thirty days, ninety days, 30 days
        if not params.notice_days:
            if "thirty (30)" in text or "30 days" in text or "thirty days" in text:
                params.notice_days = 30
            elif "ninety (90)" in text or "90 days" in text or "ninety days" in text:
                params.notice_days = 90
            elif "fifteen (15)" in text or "15 days" in text or "fifteen days" in text:
                params.notice_days = 15
            elif "one (1) month notice" in text or "one month notice" in text or "1 month notice" in text:
                params.notice_days = 30
                params.notice_months = 1.0
            elif "two (2) months notice" in text or "two months notice" in text or "2 months notice" in text:
                params.notice_days = 60
                params.notice_months = 2.0
            elif "three (3) months notice" in text or "three months notice" in text or "3 months notice" in text:
                params.notice_days = 90
                params.notice_months = 3.0

        # 3. Months (e.g. deposit months, term months)
        months_match = re.search(r"([0-9]{1,2})\s*months?", text, re.IGNORECASE)
        if months_match:
            try:
                params.months = float(months_match.group(1))
            except ValueError:
                pass
        else:
            if "eleven (11) months" in text.lower() or "eleven months" in text.lower():
                params.months = 11.0
            elif "six (6) months" in text.lower() or "six months" in text.lower():
                params.months = 6.0
            elif "two (2) months" in text.lower() or "two months" in text.lower():
                params.months = 2.0

        # Unrestricted entry check
        t_low = text.lower()
        if "at any time" in t_low or "without notice" in t_low:
            extra["unrestricted"] = True

        params.extra = extra
        return params

    def _extract_evidence_quote(self, text: str, ctype: ClauseType, action: ActionOntology) -> str:
        """Pulls a concise verbatim sentence or substring from the clause."""
        sentences = [s.strip() for s in re.split(r"[\.\n]", text) if s.strip()]
        if not sentences:
            return text[:120].strip()

        # Find sentence containing keywords for the clause type
        keywords = {
            ClauseType.TERMINATION: ["terminate", "notice", "vacate"],
            ClauseType.DEPOSIT: ["deposit", "advance", "refund"],
            ClauseType.RENT: ["rent", "pay", "monthly"],
            ClauseType.ENTRY: ["enter", "inspect", "notice"],
            ClauseType.UTILITIES: ["disconnect", "electricity", "water"],
            ClauseType.PENALTY: ["forfeit", "penalty", "liquidated"],
            ClauseType.PETS: ["pet", "animal", "dog", "cat"]
        }.get(ctype, [])

        for s in sentences:
            s_low = s.lower()
            if any(k in s_low for k in keywords):
                return s

        return sentences[0]


class GeminiLLMProvider(LLMProvider):
    """
    Online LLM provider leveraging google-genai SDK.
    Follows required field order: evidence_quote -> internal reasoning -> structured fields.
    """

    def __init__(self, api_key: str, model_name: str):
        self.api_key = api_key
        self.model_name = model_name
        from google import genai
        self.client = genai.Client(api_key=api_key)

    def get_mode_name(self) -> str:
        return f"Gemini ({self.model_name})"

    def extract_clause(self, segment: ClauseSegment, full_text: str = "") -> ClauseIR:
        # Prompt structured output with Gemini
        prompt = f"""
You are an expert Indian tenancy contract compliance analyst.
Analyze the following contractual clause:

CLAUSE TEXT:
\"\"\"{segment.text}\"\"\"

Extract structured fields in this exact JSON schema:
{{
  "evidence_quote": "<verbatim substring from text>",
  "internal_reasoning": "<1-2 sentences of deduction>",
  "clause_type": "rent"|"deposit"|"term"|"termination"|"renewal"|"entry"|"repairs"|"utilities"|"subletting"|"rent_increase"|"lock_in"|"penalty"|"registration"|"pets"|"misc",
  "party": "landlord"|"tenant"|"both",
  "modality": "obligation"|"permission"|"prohibition"|"right"|"definition",
  "action": "PayRent"|"PayDeposit"|"RefundDeposit"|"EnterPremises"|"Terminate"|"IncreaseRent"|"Sublet"|"Repair"|"CutUtilities"|"ForfeitDeposit"|"ChargeLateFee"|"Renew"|"Evict"|"KeepPets"|"Other",
  "amount_inr": <number or null>,
  "notice_days": <number or null>,
  "months": <number or null>,
  "confidence": <0.0 to 1.0>
}}
"""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={"response_mime_type": "application/json"}
            )
            import json
            data = json.loads(response.text)
            params = ClauseParams(
                amount_inr=data.get("amount_inr"),
                notice_days=data.get("notice_days"),
                months=data.get("months")
            )
            return ClauseIR(
                id=segment.clause_id,
                raw_number=segment.raw_number,
                text=segment.text,
                span=segment.span,
                clause_type=ClauseType(data.get("clause_type", "misc")),
                party=Party(data.get("party", "both")),
                modality=Modality(data.get("modality", "definition")),
                action=ActionOntology(data.get("action", "Other")),
                params=params,
                evidence_quote=data.get("evidence_quote", segment.text[:100]),
                confidence=float(data.get("confidence", 0.9)),
                internal_reasoning=data.get("internal_reasoning")
            )
        except Exception as e:
            # Fallback to offline extractor on API glitch
            fallback = OfflineExtractor()
            res = fallback.extract_clause(segment, full_text)
            res.confidence = 0.75
            res.internal_reasoning = f"LLM error fallback: {str(e)}"
            return res


def get_extractor() -> LLMProvider:
    """Factory to retrieve current extractor based on environment variables."""
    provider_name = os.getenv("LLM_PROVIDER", "offline").lower()
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    model_name = os.getenv("LLM_MODEL", "gemini-2.5-flash").strip()

    if provider_name == "gemini" and api_key:
        try:
            return GeminiLLMProvider(api_key=api_key, model_name=model_name)
        except Exception:
            return OfflineExtractor()

    return OfflineExtractor()
