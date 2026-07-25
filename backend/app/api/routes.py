"""
FastAPI Routes — Phase 10.

Exposes the LangGraph orchestration layer as RESTful HTTP endpoints.
Includes request validation, timing logs, and status checks.
"""

import time
from fastapi import APIRouter, Request

from app.config.settings import settings
from app.core.logging import get_logger
from app.schemas.requests import (
    QueryRequest, 
    QueryResponse, 
    UploadResponse, 
    HealthResponse, 
    StatusResponse
)
from app.agents.workflow import workflow
from app.tools.tool_manager import REGISTRY

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
        dummy_analytics=settings.use_dummy_analytics,
        registered_tools=len(REGISTRY),
    )


@router.post("/query", response_model=QueryResponse, tags=["Agent"])
async def process_query(request: QueryRequest):
    """
    Main entry point for the AMLens agent.
    Takes a natural language query, orchestrates the analytics pipeline,
    and returns a structured compliance narrative and risk assessment.
    """
    start_time = time.time()
    logger.info(f"Received query request: '{request.query}'")
    
    # Construct initial state matching AgentStateDict expectations
    initial_state = {
        "user_query": request.query,
        "filters": request.filters or {},
    }
    
    # Invoke LangGraph Workflow synchronously (it handles async internally if needed, but our tools are threaded)
    final_state = workflow.invoke(initial_state)
    
    elapsed = time.time() - start_time
    logger.info(f"Query processed in {elapsed:.2f}s. Trace: {final_state.get('trace')}")
    
    # Map the AgentStateDict to the QueryResponse Pydantic model
    return QueryResponse(
        user_query=final_state.get("user_query", ""),
        filters=final_state.get("filters", {}),
        parsed_intent=final_state.get("parsed_intent", {}),
        entities=final_state.get("entities", {}),
        execution_plan=final_state.get("execution_plan", []),
        tool_outputs=final_state.get("tool_outputs", {}),
        risk_results=final_state.get("risk_results"),
        explanation=final_state.get("explanation", ""),
        recommendation=final_state.get("recommendation", ""),
        trace=final_state.get("trace", []),
        errors=final_state.get("errors", []),
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
