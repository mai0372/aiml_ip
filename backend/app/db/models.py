"""
backend/app/db/models.py
SQLModel data models for storing analysis history in SQLite.
"""

from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class AnalysisRecord(SQLModel, table=True):
    __tablename__ = "analyses"

    id: str = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    filename: Optional[str] = Field(default="agreement.txt")
    raw_text: str
    clean_text: str
    risk_score: int = Field(default=0)
    clauses_json: str
    findings_json: str
    severity_counts_json: str
    llm_mode: str = Field(default="offline")
    redacted: bool = Field(default=False)

