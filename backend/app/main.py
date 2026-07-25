"""
AMLens FastAPI Application Entry Point.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import register_exception_handlers

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    setup_logging()
    logger.info("=" * 60)
    logger.info("AMLens API starting up")
    logger.info(f"  Environment : {settings.env}")
    logger.info(f"  HF Model    : {settings.hf_model}")
    logger.info(f"  Dummy tools : {settings.use_dummy_analytics}")
    logger.info("=" * 60)
    yield
    logger.info("AMLens API shutting down")


def create_app() -> FastAPI:
    """Application factory — creates and configures the FastAPI instance."""
    app = FastAPI(
        title=settings.api_title,
        version=settings.api_version,
        description=(
            "AI-Powered Suspicious Activity Detection — "
            "Agent orchestration layer for AML compliance analysis."
        ),
        lifespan=lifespan,
    )

    # --- CORS ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Exception handlers ---
    register_exception_handlers(app)

    # --- Routes ---
    # Stub health endpoint available immediately; full routes wired in Phase 10
    @app.get("/health", tags=["System"])
    async def health():
        return {"status": "ok"}

    @app.get("/status", tags=["System"])
    async def status():
        return {
            "agent": "ready",
            "environment": settings.env,
            "model": settings.hf_model,
            "dummy_analytics": settings.use_dummy_analytics,
        }

    return app


app = create_app()
