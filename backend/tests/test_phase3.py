"""Phase 3 validation — test all dummy analytics functions."""

from app.tools.dummy_analytics import (
    run_eda, generate_features, detect_rules, detect_anomalies, calculate_risk,
)
from app.schemas.tool_io import (
    EDAOutput, FeatureOutput, RuleOutput, AnomalyOutput, RiskOutput,
)

filter_sets = [
    {},
    {"country": "AE"},
    {"customer_id": "CUST-1023", "min_amount": 10000},
    {"country": "SG", "date_from": "2024-01-01"},
    {"country": "NG", "transaction_type": "cash"},
]

print("=== Testing Dummy Analytics API ===\n")

for i, filters in enumerate(filter_sets):
    label = str(filters) if filters else "(empty)"
    print(f"--- Filter set {i+1}: {label} ---")

    eda = run_eda(filters)
    EDAOutput.model_validate(eda)
    print(f"  EDA: {eda['total_transactions']} txns, {eda['outlier_count']} outliers, countries={eda['top_countries']}")

    feat = generate_features(filters)
    FeatureOutput.model_validate(feat)
    print(f"  Features: velocity={feat['velocity_flagged']}, dormancy={feat['dormancy_flagged']}, cash_ratio={feat['cash_ratio_avg']}")

    rules = detect_rules(filters)
    RuleOutput.model_validate(rules)
    print(f"  Rules: {rules['triggered_rules']} ({rules['rule_hits']} hits)")

    anomaly = detect_anomalies(filters)
    AnomalyOutput.model_validate(anomaly)
    print(f"  Anomaly: score={anomaly['anomaly_score']}, confidence={anomaly['confidence']}")

    risk = calculate_risk(rules, anomaly)
    RiskOutput.model_validate(risk)
    print(f"  Risk: score={risk['risk_score']}, band={risk['risk_band']}")
    print(f"  Factors: {risk['contributing_factors']}")
    print()

# Reproducibility
r1 = run_eda({"country": "AE"})
r2 = run_eda({"country": "AE"})
assert r1 == r2, "Reproducibility FAILED!"
print("Reproducibility check: PASSED (same filters -> same output)")

# Edge case: Low risk
low_risk = calculate_risk(
    {"triggered_rules": [], "rule_hits": 0},
    {"anomaly_score": 0.2, "confidence": 0.8},
)
assert low_risk["risk_band"] == "Low"
print(f"Edge case (empty rules + low anomaly): band={low_risk['risk_band']} score={low_risk['risk_score']}")

# Edge case: Critical risk
crit_risk = calculate_risk(
    {"triggered_rules": ["structuring", "smurfing", "layering"], "rule_hits": 10},
    {"anomaly_score": 0.95, "confidence": 0.99},
)
assert crit_risk["risk_band"] == "Critical"
print(f"Edge case (max rules + max anomaly): band={crit_risk['risk_band']} score={crit_risk['risk_score']}")

print("\n=== ALL TESTS PASSED ===")
