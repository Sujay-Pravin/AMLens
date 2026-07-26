"""
FastAPI Routes — Phase 10.

Exposes the LangGraph orchestration layer as RESTful HTTP endpoints.
Includes request validation, timing logs, and status checks.
"""

import io
import time

import pandas as pd
from fastapi import APIRouter, File, Form, Request, UploadFile

from app.config.settings import settings
from app.core.logging import get_logger
from app.schemas.requests import (
    UploadResponse,
    HealthResponse,
    StatusResponse
)
from app.schemas.evidence import InvestigationResponse
from app.services.investigation_service import run_investigation

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health():
    """Liveness probe."""
    return HealthResponse(status="ok")


@router.get("/status", response_model=StatusResponse, tags=["System"])
async def status():
    """Readiness probe with agent configuration details."""
    return StatusResponse(
        agent="ready",
        environment=settings.env,
        model=settings.gemini_model,
    )


@router.post("/upload", response_model=UploadResponse, tags=["Agent"])
async def upload_file(request: Request):
    """
    Stub endpoint for file uploads (e.g., CSV datasets).
    Just returns a fake path for now.
    """
    logger.info("Upload request received (stubbed).")
    # In a real scenario, use fastapi.UploadFile
    return UploadResponse(
        status="success",
        file_path="/tmp/uploads/stub_data.csv",
        message="File uploaded successfully (stub)."
    )


@router.post("/investigate", response_model=InvestigationResponse, tags=["Investigation"])
async def investigate(file: UploadFile = File(...), query: str = Form(default="")):
    """
    Run the query-driven analytics pipeline on an uploaded transaction CSV.
    The user's natural-language query is parsed into structured intent and
    filters, which the planner uses to decide which analytics tools
    (EDA, rule engine, ML inference + SHAP, risk fusion, graph analytics)
    actually execute, and return the evidence plus an LLM-generated
    investigation narrative.
    """
    start_time = time.time()
    logger.info(f"Received investigation request for file: '{file.filename}', query: '{query}'")

    raw_bytes = await file.read()
    df = pd.read_csv(io.BytesIO(raw_bytes))

    result = run_investigation(df, filename=file.filename or "uploaded.csv", query=query)

    elapsed = time.time() - start_time
    logger.info(
        f"Investigation completed in {elapsed:.2f}s. "
        f"Execution trace: {result.execution_trace}"
    )

    return result
