"""
Abstract interfaces (Protocol classes) for the analytics tool functions.

These define what Member 2's module must implement. The dummy_analytics module
(Phase 3) and the real module (Phase 12) both conform to these protocols.

Using Protocol (structural subtyping) instead of ABC so Member 2 doesn't
need to inherit from our base classes — duck typing is sufficient.
"""

from __future__ import annotations

from typing import Any, Protocol


class EDAAnalyzer(Protocol):
    """Protocol for exploratory data analysis."""

    def __call__(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Run EDA on filtered transaction data.

        Returns:
            {total_transactions, missing_values, top_countries, outlier_count}
        """
        ...


class FeatureGenerator(Protocol):
    """Protocol for feature engineering."""

    def __call__(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Generate AML-relevant features from filtered data.

        Returns:
            {velocity_flagged, dormancy_flagged, cash_ratio_avg, ...}
        """
        ...


class RuleDetector(Protocol):
    """Protocol for rule-based AML pattern detection."""

    def __call__(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Detect AML patterns using predefined rules.

        Returns:
            {triggered_rules: list[str], rule_hits: int}
        """
        ...


class AnomalyDetector(Protocol):
    """Protocol for ML-based anomaly detection."""

    def __call__(self, filters: dict[str, Any]) -> dict[str, Any]:
        """Detect anomalies using ML models.

        Returns:
            {anomaly_score: float, confidence: float}
        """
        ...


class RiskCalculator(Protocol):
    """Protocol for composite risk scoring."""

    def __call__(self, rule_out: dict[str, Any], ml_out: dict[str, Any]) -> dict[str, Any]:
        """Calculate composite risk from rule + ML outputs.

        Returns:
            {risk_score: float, risk_band: 'Low'|'Medium'|'High'|'Critical'}
        """
        ...
