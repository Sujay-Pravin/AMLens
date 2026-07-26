"""
Global configuration for the Analytics SDK.

This module centralizes configurable values used across the analytics
pipeline. Business logic should not be implemented here.
"""

from pathlib import Path

# -----------------------------------------------------------------------------
# Project Paths
# -----------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "datasets"

MODEL_DIR = PROJECT_ROOT / "models"

OUTPUT_DIR = PROJECT_ROOT / "outputs"

PLOT_DIR = OUTPUT_DIR / "plots"

# -----------------------------------------------------------------------------
# Dataset Configuration
# -----------------------------------------------------------------------------

DEFAULT_TIMESTAMP_COLUMN = "Timestamp"

DEFAULT_TARGET_COLUMN = "Is_Laundering"

SUPPORTED_FILE_TYPES = {
    ".csv",
    ".parquet"
}

# -----------------------------------------------------------------------------
# Randomness
# -----------------------------------------------------------------------------

RANDOM_STATE = 42

# -----------------------------------------------------------------------------
# Time
# -----------------------------------------------------------------------------

DEFAULT_TIMEZONE = "UTC"

# -----------------------------------------------------------------------------
# Logging
# -----------------------------------------------------------------------------

LOG_LEVEL = "INFO"