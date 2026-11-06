"""
backend/app/models/api_models.py
Pydantic v2 schemas for REST API request and response payloads.
"""

from __future__ import annotations
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AnalysisCreateRequest(BaseModel):
    text: Optional[str] = Field(None, description="Plain text of the rental agreement")
    filename: Optional[str] = Field("agreement.txt", description="File name if uploaded")
    redact_pii: bool = Field(False, description="Whether to mask Indian phones, emails, Aadhaar, and PAN")


class AnalysisCreateResponse(BaseModel):
    id: str
    status: str = "processing"
    message: str = "Analysis initialized. Connect to /events for real-time SSE progress."


class WhatIfRequest(BaseModel):
    question: str = Field(..., description="The query to ask against the contract, e.g. 'Can I terminate early?'")


class LogicConvertRequest(BaseModel):
    formula: str = Field(..., description="FOPL WFF string to convert to CNF, e.g. 'forall x: (Man(x) -> Mortal(x))'")


class LogicProveRequest(BaseModel):
    premises: List[str] = Field(..., description="List of premise WFF formulas")
    goal: Optional[str] = Field(None, description="Optional conclusion formula to prove by refutation")


class HealthResponse(BaseModel):
    status: str = "ok"
    mode: str = "offline"  # "offline" or "llm"
    version: str = "1.0.0"
    engine: str = "Logic-Based Contract Compliance Engine"

