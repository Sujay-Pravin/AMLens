"""
Centralized exception definitions and FastAPI exception handlers.

Design principle: tool failures should degrade gracefully (partial results),
never crash the entire request with a raw 500.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Custom exception classes
# ---------------------------------------------------------------------------

class AMLensError(Exception):
    """Base exception for all AMLens-specific errors."""

    def __init__(self, message: str, detail: dict | None = None):
        super().__init__(message)
        self.message = message
        self.detail = detail or {}


class ToolExecutionError(AMLensError):
    """Raised when an analytics tool fails or times out."""

    def __init__(self, tool_name: str, reason: str):
        super().__init__(
            message=f"Tool '{tool_name}' failed: {reason}",
            detail={"tool": tool_name, "reason": reason},
        )
        self.tool_name = tool_name
        self.reason = reason


class IntentParsingError(AMLensError):
    """Raised when intent extraction fails irrecoverably."""

    def __init__(self, query: str, reason: str):
        super().__init__(
            message=f"Could not parse intent for query: {reason}",
            detail={"query": query, "reason": reason},
        )


class WorkflowError(AMLensError):
    """Raised when the LangGraph workflow encounters a fatal error."""

    def __init__(self, node: str, reason: str):
        super().__init__(
            message=f"Workflow failed at node '{node}': {reason}",
            detail={"node": node, "reason": reason},
        )


# ---------------------------------------------------------------------------
# FastAPI exception handlers
# ---------------------------------------------------------------------------

def register_exception_handlers(app: FastAPI) -> None:
    """Register all custom exception handlers on the FastAPI app."""

    @app.exception_handler(AMLensError)
    async def amlens_error_handler(request: Request, exc: AMLensError):
        """Handle all AMLens-specific errors with a structured JSON response."""
        logger.error(
            f"{exc.__class__.__name__}: {exc.message}",
            extra={"detail": exc.detail},
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": exc.__class__.__name__,
                "message": exc.message,
                "detail": exc.detail,
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError):
        """Catch validation errors and return 400 instead of 500."""
        logger.warning(f"ValueError: {exc}")
        return JSONResponse(
            status_code=400,
            content={
                "error": "ValidationError",
                "message": str(exc),
                "detail": {},
            },
        )

    @app.exception_handler(Exception)
    async def catch_all_handler(request: Request, exc: Exception):
        """Last-resort handler — log the full exception, return a clean 500."""
        logger.exception(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred. Check server logs.",
                "detail": {},
            },
        )
