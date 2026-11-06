"""
backend/app/db/session.py
Database initialization and repository operations for SQLite via SQLModel.
"""

from __future__ import annotations
import os
import json
from typing import List, Optional, Dict, Any
from sqlmodel import SQLModel, Session, create_engine, select

from backend.app.db.models import AnalysisRecord

DB_FILE = os.getenv("DATABASE_URL", "sqlite:///clauselens.db")
engine = create_engine(DB_FILE, connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def save_analysis(
    analysis_id: str,
    raw_text: str,
    payload: Dict[str, Any],
    filename: Optional[str] = None
) -> AnalysisRecord:
    with Session(engine) as session:
        record = AnalysisRecord(
            id=analysis_id,
            filename=filename or "agreement.txt",
            raw_text=raw_text,
            clean_text=payload.get("clean_text", raw_text),
            risk_score=payload.get("risk_score", 0),
            clauses_json=json.dumps(payload.get("clauses", [])),
            findings_json=json.dumps(payload.get("findings", [])),
            severity_counts_json=json.dumps(payload.get("severity_counts", {})),
            llm_mode=payload.get("llm_mode", "offline"),
            redacted=payload.get("pii_redacted", False)
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record


def get_analysis_by_id(analysis_id: str) -> Optional[Dict[str, Any]]:
    with Session(engine) as session:
        statement = select(AnalysisRecord).where(AnalysisRecord.id == analysis_id)
        record = session.exec(statement).first()
        if not record:
            return None
        return {
            "id": record.id,
            "created_at": record.created_at.isoformat(),
            "filename": record.filename,
            "clean_text": record.clean_text,
            "risk_score": record.risk_score,
            "clauses": json.loads(record.clauses_json),
            "findings": json.loads(record.findings_json),
            "severity_counts": json.loads(record.severity_counts_json),
            "llm_mode": record.llm_mode,
            "redacted": record.redacted
        }


def list_all_analyses() -> List[Dict[str, Any]]:
    with Session(engine) as session:
        statement = select(AnalysisRecord).order_by(AnalysisRecord.created_at.desc())
        records = session.exec(statement).all()
        return [
            {
                "id": r.id,
                "created_at": r.created_at.isoformat(),
                "filename": r.filename,
                "risk_score": r.risk_score,
                "clauses_count": len(json.loads(r.clauses_json)),
                "findings_count": len(json.loads(r.findings_json)),
                "severity_counts": json.loads(r.severity_counts_json),
                "llm_mode": r.llm_mode
            }
            for r in records
        ]

