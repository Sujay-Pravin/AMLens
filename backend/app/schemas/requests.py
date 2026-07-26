"""
API request and response models for the AMLens REST endpoints.

All endpoints use these Pydantic models for validation and serialization.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class UploadRequest(BaseModel):
    """POST /upload — metadata for a file upload (stub for sprint)."""

    filename: str = Field(..., description="Name of the uploaded file")
    description: Optional[str] = Field(
        default=None, description="Optional description of the dataset"
    )


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

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
