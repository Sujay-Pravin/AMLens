"""
Pydantic models for the Integration Contract with Member 2.

These define the exact output shape for each of the 5 analytics functions.
Both the dummy analytics (Phase 3) and Member 2's real modules must return
data that validates against these models. This is what makes the swap seamless.

Field names below are NON-NEGOTIABLE without updating both sides.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class EDAOutput(BaseModel):
    """Output schema for run_eda() — exploratory data analysis summary."""

    total_transactions: int = Field(
        ..., description="Total number of transactions in the filtered dataset"
    )
    missing_values: int = Field(
        ..., description="Count of missing/null values across key fields"
    )
    top_countries: list[str] = Field(
        ..., description="Top countries by transaction volume (ISO 3166-1 alpha-2)"
    )
    outlier_count: int = Field(
        ..., description="Number of statistical outliers detected"
    )


class FeatureOutput(BaseModel):
    """Output schema for generate_features() — engineered features for AML detection."""

    velocity_flagged: int = Field(
        ..., description="Number of accounts flagged for high transaction velocity"
    )
    dormancy_flagged: int = Field(
        ..., description="Number of accounts flagged for dormancy reactivation"
    )
    cash_ratio_avg: float = Field(
        ..., description="Average cash-to-total transaction ratio across accounts"
    )


class RuleOutput(BaseModel):
    """Output schema for detect_rules() — rule-based AML pattern detection."""

    triggered_rules: list[str] = Field(
        ...,
        description=(
            "List of AML pattern names triggered. "
            "e.g. ['structuring', 'smurfing', 'rapid_cash_out', 'layering']"
        ),
    )
    rule_hits: int = Field(
        ..., description="Total number of rule hits across all patterns"
    )


class AnomalyOutput(BaseModel):
    """Output schema for detect_anomalies() — ML-based anomaly detection."""

    anomaly_score: float = Field(
        ..., ge=0.0, le=1.0, description="Anomaly score (0 = normal, 1 = highly anomalous)"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Model confidence in the anomaly score"
    )


class RiskOutput(BaseModel):
    """Output schema for calculate_risk() — composite risk assessment."""

    risk_score: float = Field(
        ..., ge=0.0, le=1.0, description="Composite risk score combining rules + ML"
    )
    risk_band: Literal["Low", "Medium", "High", "Critical"] = Field(
        ..., description="Risk classification band"
    )
