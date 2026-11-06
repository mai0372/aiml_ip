"""
backend/app/models/clause_ir.py
Pydantic v2 data models for Clause Intermediate Representation (ClauseIR),
Action Ontology, and Verification Auditing.
"""

from __future__ import annotations
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class ClauseType(str, Enum):
    RENT = "rent"
    DEPOSIT = "deposit"
    TERM = "term"
    TERMINATION = "termination"
    RENEWAL = "renewal"
    ENTRY = "entry"
    REPAIRS = "repairs"
    UTILITIES = "utilities"
    SUBLETTING = "subletting"
    RENT_INCREASE = "rent_increase"
    LOCK_IN = "lock_in"
    PENALTY = "penalty"
    REGISTRATION = "registration"
    PETS = "pets"
    MISC = "misc"


class Party(str, Enum):
    LANDLORD = "landlord"
    TENANT = "tenant"
    BOTH = "both"


class Modality(str, Enum):
    OBLIGATION = "obligation"
    PERMISSION = "permission"
    PROHIBITION = "prohibition"
    RIGHT = "right"
    DEFINITION = "definition"


class ActionOntology(str, Enum):
    PAY_RENT = "PayRent"
    PAY_DEPOSIT = "PayDeposit"
    REFUND_DEPOSIT = "RefundDeposit"
    ENTER_PREMISES = "EnterPremises"
    TERMINATE = "Terminate"
    INCREASE_RENT = "IncreaseRent"
    SUBLET = "Sublet"
    REPAIR = "Repair"
    CUT_UTILITIES = "CutUtilities"
    FORFEIT_DEPOSIT = "ForfeitDeposit"
    CHARGE_LATE_FEE = "ChargeLateFee"
    RENEW = "Renew"
    EVICT = "Evict"
    KEEP_PETS = "KeepPets"
    OTHER = "Other"


class ClauseSpan(BaseModel):
    start: int = Field(..., description="Character offset start in raw contract text")
    end: int = Field(..., description="Character offset end in raw contract text")


class ClauseParams(BaseModel):
    amount_inr: Optional[float] = None
    months: Optional[float] = None
    days: Optional[int] = None
    notice_days: Optional[int] = None
    notice_months: Optional[float] = None
    percent: Optional[float] = None
    ratio: Optional[float] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class ClauseIR(BaseModel):
    """Structured intermediate representation of a single contractual clause."""
    id: str = Field(..., description="Unique clause identifier, e.g. Clause_1, Clause_3.2")
    raw_number: Optional[str] = Field(None, description="Original numbering label in text, e.g. '1.', 'Clause 4'")
    text: str = Field(..., description="Cleaned text of the clause")
    span: ClauseSpan
    clause_type: ClauseType = Field(default=ClauseType.MISC)
    party: Party = Field(default=Party.BOTH)
    modality: Modality = Field(default=Modality.DEFINITION)
    action: ActionOntology = Field(default=ActionOntology.OTHER)
    params: ClauseParams = Field(default_factory=ClauseParams)
    conditions: List[str] = Field(default_factory=list)
    exceptions: List[str] = Field(default_factory=list)
    evidence_quote: str = Field(..., description="Exact substring from clause text providing grounds for extraction")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    internal_reasoning: Optional[str] = Field(None, description="Internal reasoning chain (kept hidden from user)")


class VerificationCheck(BaseModel):
    name: str
    passed: bool
    detail: str


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    NEEDS_REVIEW = "needs_review"
    DISPUTED = "disputed"


class VerificationResult(BaseModel):
    status: VerificationStatus
    checks: List[VerificationCheck] = Field(default_factory=list)


class FindingKind(str, Enum):
    CONFLICT = "conflict"
    LEGAL_RISK = "legal_risk"
    ADVISORY = "advisory"
    MISSING = "missing"


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class StatutorySource(BaseModel):
    statute_name: str
    section: str
    source_text: str = ""  # Left empty for unverified rules
    source_url: str
    retrieved_on: str = ""
    reviewed: bool = False
    reviewed_by: Optional[str] = None
    reviewed_on: Optional[str] = None
    applicability: str  # "central act" | "model law, state adoption varies" | "state act, varies"
    jurisdiction_note: str


class Finding(BaseModel):
    id: str
    kind: FindingKind
    severity: Severity
    title: str
    plain_explanation: str
    why_it_matters: str
    evidence_quote: str
    suggestion: str
    affected_clause_ids: List[str] = Field(default_factory=list)
    rule_id: Optional[str] = None
    source: Optional[StatutorySource] = None
    verification: VerificationResult
    proof: Optional[Dict[str, Any]] = None  # Populated for FOPL conflicts / query answers

