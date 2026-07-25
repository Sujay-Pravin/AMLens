"""
Application settings loaded from environment variables via pydantic-settings.

All configuration is centralized here — no module should read os.environ directly.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Global application settings, loaded from .env file and environment variables."""

    # --- Google AI Studio / Gemini ---
    gemini_api_key: str = Field(..., description="Google AI Studio API key")
    gemini_model: str = Field(
        default="gemma-4-31b-it",
        description="Google AI model ID for inference (intent parsing + explanation)",
    )

    # --- Application ---
    env: str = Field(default="dev", description="Environment: dev | staging | prod")
    log_level: str = Field(default="INFO", description="Logging level")
    tool_timeout_seconds: int = Field(
        default=15,
        description="Max seconds to wait for a single analytics tool call",
    )

    # --- API ---
    api_title: str = "AMLens API"
    api_version: str = "0.1.0"
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
        description="Allowed CORS origins (React dev servers)",
    )

    # --- Feature flags ---
    use_dummy_analytics: bool = Field(
        default=True,
        description="Use dummy analytics module instead of Member 2's real module",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# Singleton — import this everywhere
settings = Settings()
