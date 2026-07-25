"""
Dummy Analytics API — realistic stand-in for Member 2's analytics module.

These five functions match Member 2's exact signatures and return schema-valid
data. The entire agent pipeline (planner, workflow, explainer, recommender) is
built and tested against this module.

Phase 12 swap: change the import in tool_manager.py from this file to Member 2's
real module. Nothing else changes.

Design choices for the dummy data:
- Varied and believable (different risk levels, countries, patterns)
- Controlled randomness seeded by filter content for reproducibility
- Edge cases included (empty results, borderline scores)
- All outputs validate against app/schemas/tool_io.py Pydantic models
"""

from __future__ import annotations

import hashlib
import random
from typing import Any


def _seed_from_filters(filters: dict[str, Any]) -> int:
    """Derive a deterministic seed from filters so same query → same results.

    This makes demos reproducible while still varying output across different queries.
    """
    raw = str(sorted(filters.items())) if filters else "default"
    return int(hashlib.md5(raw.encode()).hexdigest()[:8], 16)


# ---------------------------------------------------------------------------
# 1. Exploratory Data Analysis
# ---------------------------------------------------------------------------

def run_eda(filters: dict[str, Any]) -> dict[str, Any]:
    """Run exploratory data analysis on filtered transaction data.

    Returns:
        {total_transactions, missing_values, top_countries, outlier_count}
    """
    rng = random.Random(_seed_from_filters(filters))

    country_pools = [
        ["AE", "SG", "IN"],
        ["US", "GB", "CH"],
        ["HK", "MY", "PH"],
        ["DE", "NL", "LU"],
        ["NG", "KE", "ZA"],
    ]

    total = rng.randint(500, 50000)
    return {
        "total_transactions": total,
        "missing_values": rng.randint(0, max(1, total // 100)),
        "top_countries": rng.choice(country_pools),
        "outlier_count": rng.randint(5, max(6, total // 50)),
    }


# ---------------------------------------------------------------------------
# 2. Feature Engineering
# ---------------------------------------------------------------------------

def generate_features(filters: dict[str, Any]) -> dict[str, Any]:
    """Generate AML-relevant features from filtered transaction data.

    Returns:
        {velocity_flagged, dormancy_flagged, cash_ratio_avg,
         round_amount_pct, cross_border_pct}
    """
    rng = random.Random(_seed_from_filters(filters))

    return {
        "velocity_flagged": rng.randint(0, 25),
        "dormancy_flagged": rng.randint(0, 10),
        "cash_ratio_avg": round(rng.uniform(0.1, 0.85), 2),
        "round_amount_pct": round(rng.uniform(0.05, 0.60), 2),
        "cross_border_pct": round(rng.uniform(0.10, 0.90), 2),
    }


# ---------------------------------------------------------------------------
# 3. Rule-Based Detection
# ---------------------------------------------------------------------------

_ALL_PATTERNS = [
    "structuring",
    "smurfing",
    "rapid_cash_out",
    "layering",
    "round_tripping",
    "dormant_reactivation",
    "funnel_account",
    "trade_misinvoicing",
]


def detect_rules(filters: dict[str, Any]) -> dict[str, Any]:
    """Detect AML patterns using predefined rules.

    Returns:
        {triggered_rules: list[str], rule_hits: int,
         details: list[dict]}
    """
    rng = random.Random(_seed_from_filters(filters))

    num_triggered = rng.randint(0, 4)
    triggered = rng.sample(_ALL_PATTERNS, k=min(num_triggered, len(_ALL_PATTERNS)))
    rule_hits = sum(rng.randint(1, 5) for _ in triggered) if triggered else 0

    details = [
        {
            "rule": rule,
            "hits": rng.randint(1, 5),
            "severity": rng.choice(["low", "medium", "high"]),
            "sample_accounts": [f"CUST-{rng.randint(1000, 9999)}" for _ in range(2)],
        }
        for rule in triggered
    ]

    return {
        "triggered_rules": triggered,
        "rule_hits": rule_hits,
        "details": details,
    }


# ---------------------------------------------------------------------------
# 4. ML-Based Anomaly Detection
# ---------------------------------------------------------------------------

def detect_anomalies(filters: dict[str, Any]) -> dict[str, Any]:
    """Detect anomalies using ML models.

    Returns:
        {anomaly_score: float, confidence: float,
         top_anomalous_accounts: list[dict]}
    """
    rng = random.Random(_seed_from_filters(filters))

    anomaly_score = round(rng.uniform(0.15, 0.98), 2)
    confidence = round(rng.uniform(0.55, 0.99), 2)

    top_accounts = [
        {
            "account_id": f"CUST-{rng.randint(1000, 9999)}",
            "score": round(rng.uniform(0.6, 0.99), 2),
            "primary_flag": rng.choice([
                "high_velocity", "unusual_pattern", "dormant_reactivation",
                "large_cash_ratio", "cross_border_spike",
            ]),
        }
        for _ in range(rng.randint(2, 5))
    ]

    return {
        "anomaly_score": anomaly_score,
        "confidence": confidence,
        "top_anomalous_accounts": top_accounts,
    }


# ---------------------------------------------------------------------------
# 5. Composite Risk Scoring
# ---------------------------------------------------------------------------

def calculate_risk(rule_out: dict[str, Any], ml_out: dict[str, Any]) -> dict[str, Any]:
    """Calculate composite risk from rule-based + ML outputs.

    Scoring formula:
        risk_score = 0.4 * normalized_rule_hits + 0.6 * anomaly_score

    Returns:
        {risk_score: float, risk_band: str, contributing_factors: list[str]}
    """
    rule_hits = rule_out.get("rule_hits", 0)
    anomaly_score = ml_out.get("anomaly_score", 0.0)

    # Normalize rule hits to 0–1 range (cap at 10 hits)
    normalized_rules = min(rule_hits / 10.0, 1.0)

    # Weighted composite
    risk_score = round(0.4 * normalized_rules + 0.6 * anomaly_score, 2)

    # Band classification
    if risk_score > 0.8:
        risk_band = "Critical"
    elif risk_score > 0.6:
        risk_band = "High"
    elif risk_score > 0.3:
        risk_band = "Medium"
    else:
        risk_band = "Low"

    # Contributing factors for explainability
    factors = []
    if rule_hits > 0:
        triggered = rule_out.get("triggered_rules", [])
        factors.append(f"{rule_hits} rule hits ({', '.join(triggered)})")
    if anomaly_score > 0.7:
        factors.append(f"High anomaly score ({anomaly_score})")
    if anomaly_score <= 0.3:
        factors.append(f"Low anomaly score ({anomaly_score})")

    return {
        "risk_score": risk_score,
        "risk_band": risk_band,
        "contributing_factors": factors,
    }
