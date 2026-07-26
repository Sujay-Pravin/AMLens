"""
AMLens FastAPI Application Entry Point.

Run with:
    uvicorn app.main:app --reload --port 8000
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

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
    logger.info(f"  Gemini Model: {settings.gemini_model}")
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
    from app.api.routes import router
    app.include_router(router)

    # --- Minimal hackathon frontend (temporary; same-origin, no CORS needed) ---
    static_dir = Path(__file__).resolve().parent.parent / "static"
    if static_dir.exists():
        app.mount("/ui", StaticFiles(directory=str(static_dir), html=True), name="ui")

    return app


app = create_app()
