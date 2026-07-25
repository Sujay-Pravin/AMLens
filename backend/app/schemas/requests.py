"""
API request and response models for the AMLens REST endpoints.

All endpoints use these Pydantic models for validation and serialization.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    """POST /query — submit a natural-language AML investigation query."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural-language AML query",
        examples=[
            "Summarize transactions for CUST-1023",
            "Detect structuring patterns above $10,000 in UAE",
            "Score risk for high-velocity accounts since January",
        ],
    )
    filters: Optional[dict[str, Any]] = Field(
        default=None,
        description=(
            "Optional filters to narrow the analysis. "
            "Keys may include: date_from, date_to, country, customer_id, min_amount"
        ),
    )


class UploadRequest(BaseModel):
    """POST /upload — metadata for a file upload (stub for sprint)."""

    filename: str = Field(..., description="Name of the uploaded file")
    description: Optional[str] = Field(
        default=None, description="Optional description of the dataset"
    )


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class QueryResponse(BaseModel):
    """Response from POST /query — full pipeline results."""

    # Core results
    user_query: str
    explanation: Optional[str] = None
    recommendation: Optional[str] = None
    risk_results: Optional[dict[str, Any]] = None

    # Supporting data
    parsed_intent: Optional[dict[str, Any]] = None
    execution_plan: list[str] = Field(default_factory=list)
    tool_outputs: dict[str, Any] = Field(default_factory=dict)
    entities: dict[str, Any] = Field(default_factory=dict)

    # Observability
    trace: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class UploadResponse(BaseModel):
    """Response from POST /upload."""

    status: str = "received"
    filename: str
    message: str = "File uploaded successfully. Ready for analysis."


class HealthResponse(BaseModel):
    """Response from GET /health."""

    status: str = "ok"


class StatusResponse(BaseModel):
    """Response from GET /status."""

    agent: str = "ready"
    environment: str
    model: str
    dummy_analytics: bool
    tools_registered: int = Field(
        default=5, description="Number of analytics tools in the registry"
    )
