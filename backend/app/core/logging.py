"""
Structured logging setup for the AMLens backend.

Produces JSON-formatted log lines in production, human-readable in dev.
All modules should use:  from app.core.logging import get_logger
"""

import logging
import json
import sys
from datetime import datetime, timezone

from app.config.settings import settings


class JSONFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        # Attach any extra fields passed via logger.info("msg", extra={...})
        for key in ("query", "tool", "duration_ms", "node", "trace_id"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)
        return json.dumps(log_entry, default=str)


class DevFormatter(logging.Formatter):
    """Human-readable colored formatter for local development."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%H:%M:%S")
        return (
            f"{color}{timestamp} [{record.levelname:>8}]{self.RESET} "
            f"{record.name}: {record.getMessage()}"
        )


def setup_logging() -> None:
    """Configure root logger based on current environment."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicates on reload
    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    if settings.env == "dev":
        handler.setFormatter(DevFormatter())
    else:
        handler.setFormatter(JSONFormatter())

    root.addHandler(handler)

    # Quiet down noisy third-party loggers
    for noisy in ("httpx", "httpcore", "uvicorn.access", "huggingface_hub"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger. Use module __name__ as the name by convention.

    Usage:
        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.info("Processing query", extra={"query": user_query})
    """
    return logging.getLogger(name)
