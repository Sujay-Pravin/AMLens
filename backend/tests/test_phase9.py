"""Phase 9 validation — test Recommendation Agent."""

from app.agents.recommender import recommend

print("=== Testing Recommendation Agent ===\n")

test_states = [
    {
        "desc": "Critical Risk",
        "state": {"risk_results": {"risk_band": "Critical"}},
        "expected": "Escalate immediately and file a report."
    },
    {
        "desc": "High Risk",
        "state": {"risk_results": {"risk_band": "High"}},
        "expected": "Escalate for manual review."
    },
    {
        "desc": "Medium Risk",
        "state": {"risk_results": {"risk_band": "Medium"}},
        "expected": "Flag for review within SLA."
    },
    {
        "desc": "Low Risk",
        "state": {"risk_results": {"risk_band": "Low"}},
        "expected": "Continue monitoring, no action required."
    },
    {
        "desc": "Unknown Risk Band",
        "state": {"risk_results": {"risk_band": "WeirdBand"}},
        "expected": "Unknown risk level — manual review required."
    },
    {
        "desc": "Missing Risk Results",
        "state": {},
        "expected": "Unknown risk level — manual review required."
    }
]

for test in test_states:
    print(f"--- {test['desc']} ---")
    result = recommend(test["state"])
    print(f"  Got: {result}")
    assert result == test["expected"], f"Expected '{test['expected']}', but got '{result}'"

print("\n=== ALL TESTS PASSED ===")
