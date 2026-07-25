"""Phase 8 validation — test Explainer Agent narrative generation."""

from app.agents.explainer import explain

print("=== Testing Explainer Agent ===\n")

# Mock varied risk states
test_states = [
    {
        "desc": "Critical Risk Scenario",
        "state": {
            "user_query": "any structuring for accounts in UAE last month?",
            "parsed_intent": {"intent": "detect_pattern"},
            "tool_outputs": {
                "detect_rules": {"rule_hits": 3, "triggered_rules": ["velocity", "structuring"]},
                "detect_anomalies": {"anomaly_score": 0.89}
            },
            "risk_results": {"risk_score": 0.95, "risk_band": "Critical"}
        }
    },
    {
        "desc": "Low Risk Scenario",
        "state": {
            "user_query": "show me cash-out activity for CUST-4455",
            "parsed_intent": {"intent": "investigate"},
            "tool_outputs": {
                "detect_rules": {"rule_hits": 0, "triggered_rules": []},
                "detect_anomalies": {"anomaly_score": 0.15}
            },
            "risk_results": {"risk_score": 0.10, "risk_band": "Low"}
        }
    },
    {
        "desc": "Empty/Error Fallback",
        "state": {
            "user_query": "error fallback test",
            "parsed_intent": {"intent": "unknown"},
            "tool_outputs": {},
            "risk_results": None
        }
    }
]

for test in test_states:
    print(f"--- {test['desc']} ---")
    result = explain(test["state"])
    print(f"\n{result}\n")
    assert result, "Explanation was empty!"

print("=== ALL TESTS PASSED ===")
