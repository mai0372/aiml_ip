"""
backend/app/api/router.py
FastAPI router endpoints for analyses, SSE streaming, What-If queries,
Logic Lab conversions & proofs, and Indian statutory rules.
"""

from __future__ import annotations
import uuid
import json
import asyncio
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, Request
from fastapi.responses import StreamingResponse

from backend.app.models.api_models import (
    AnalysisCreateRequest, AnalysisCreateResponse, WhatIfRequest,
    LogicConvertRequest, LogicProveRequest, HealthResponse
)
from backend.app.agents.pipeline import AnalysisPipeline, PipelineEvent
from backend.app.agents.ingest import DocumentIngester
from backend.app.agents.extractor import get_extractor
from backend.app.db.session import save_analysis, get_analysis_by_id, list_all_analyses
from backend.app.kb.retriever import RuleRetriever
from backend.app.logic.parser import parse_fopl
from backend.app.logic.cnf import CNFConverter
from backend.app.logic.resolution import ResolutionProver

router = APIRouter(prefix="/api")

# In-memory store for pending analyses before SSE completion
pending_jobs: Dict[str, Dict[str, Any]] = {}
pipeline_engine = AnalysisPipeline()
rule_retriever = RuleRetriever()


@router.get("/health", response_model=HealthResponse)
def get_health():
    extractor = get_extractor()
    return HealthResponse(
        status="ok",
        mode=extractor.get_mode_name(),
        version="1.0.0",
        engine="Logic-Based Contract Compliance Engine"
    )


@router.post("/analyses", response_model=AnalysisCreateResponse)
async def create_analysis(
    request: Request,
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    filename: Optional[str] = Form(None),
    redact_pii: bool = Form(False)
):
    analysis_id = str(uuid.uuid4())[:8]
    raw_content = ""
    target_filename = filename or "agreement.txt"

    # Handle file upload or JSON payload
    if file:
        file_bytes = await file.read()
        target_filename = file.filename or "uploaded_contract"
        raw_content = DocumentIngester.extract_from_bytes(file_bytes, target_filename)
    elif text:
        raw_content = text
    else:
        # Check if raw JSON body was sent
        try:
            body = await request.json()
            raw_content = body.get("text", "")
            target_filename = body.get("filename", "agreement.txt")
            redact_pii = body.get("redact_pii", False)
        except Exception:
            pass

    if not raw_content.strip():
        raise HTTPException(status_code=400, detail="No contract text or file provided.")

    pending_jobs[analysis_id] = {
        "id": analysis_id,
        "text": raw_content,
        "filename": target_filename,
        "redact_pii": redact_pii
    }

    return AnalysisCreateResponse(
        id=analysis_id,
        status="processing",
        message="Analysis initialized. Stream live progress via /api/analyses/{id}/events."
    )


@router.get("/analyses/{analysis_id}/events")
def stream_analysis_events(analysis_id: str):
    """Server-Sent Events (SSE) live pipeline stream."""
    if analysis_id not in pending_jobs:
        # Check if already processed in database
        existing = get_analysis_by_id(analysis_id)
        if existing:
            def single_event():
                yield f"data: {json.dumps({'stage': 'complete', 'status': 'completed', 'duration_ms': 0, 'detail': 'Loaded from history.'})}\n\n"
            return StreamingResponse(single_event(), media_type="text/event-stream")
        raise HTTPException(status_code=404, detail="Analysis ID not found.")

    job = pending_jobs.pop(analysis_id)
    text = job["text"]
    filename = job["filename"]
    redact_pii = job["redact_pii"]

    def event_generator():
        final_payload = None
        for event in pipeline_engine.run_pipeline_sync(text, redact_pii=redact_pii):
            payload_dict = event.to_dict()
            yield f"data: {json.dumps(payload_dict)}\n\n"
            if event.stage == "complete":
                final_payload = event.payload

        # Persist finalized analysis to SQLite database
        if final_payload:
            save_analysis(analysis_id, text, final_payload, filename)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/analyses/{analysis_id}")
def get_analysis(analysis_id: str):
    record = get_analysis_by_id(analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")
    return record


@router.get("/analyses")
def list_analyses():
    return list_all_analyses()


@router.post("/analyses/{analysis_id}/ask")
def ask_what_if(analysis_id: str, payload: WhatIfRequest):
    record = get_analysis_by_id(analysis_id)
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    from backend.app.models.clause_ir import ClauseIR
    clauses = [ClauseIR(**c) for c in record.get("clauses", [])]
    clean_text = record.get("clean_text", "")

    result = pipeline_engine.answer_what_if(payload.question, clauses, clean_text)
    return result


@router.post("/logic/convert")
def convert_logic_wff(payload: LogicConvertRequest):
    """Syllabus Showcase: Converts any WFF to CNF, returning all 9 steps."""
    try:
        formula = parse_fopl(payload.formula)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Formula syntax error: {str(e)}")

    converter = CNFConverter()
    clauses, steps = converter.convert_with_steps(formula, source_id="USER")

    return {
        "formula": payload.formula,
        "ast": formula.to_dict(),
        "steps": [s.to_dict() for s in steps],
        "clauses": [c.to_dict() for c in clauses]
    }


@router.post("/logic/prove")
def prove_logic_formulas(payload: LogicProveRequest):
    """Syllabus Showcase: Executes Robinson unification & resolution refutation."""
    converter = CNFConverter()
    all_clauses = []

    # Convert premises
    for i, p_str in enumerate(payload.premises):
        try:
            f = parse_fopl(p_str)
            cls, _ = converter.convert_with_steps(f, source_id=f"P{i+1}", source_type="contract")
            all_clauses.extend(cls)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Premise {i+1} parse error: {str(e)}")

    # Convert negated goal if provided
    if payload.goal and payload.goal.strip():
        try:
            goal_wff = parse_fopl(payload.goal)
            from backend.app.logic.ast import Not
            neg_goal_wff = Not(goal_wff)
            goal_cls, _ = converter.convert_with_steps(neg_goal_wff, source_id="GOAL", source_type="goal")
            all_clauses.extend(goal_cls)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Goal parse error: {str(e)}")

    prover = ResolutionProver(max_clauses=800, timeout_seconds=2.0)
    result = prover.prove(all_clauses)

    return result.to_dict()


@router.get("/rules")
def get_all_rules():
    """Returns browsable Indian statutory rule pack with source status."""
    return rule_retriever.get_all_rules()

