"""Phase 9 validation — test Recommendation Agent."""

from types import SimpleNamespace

from app.agents.recommender import recommend

print("=== Testing Recommendation Agent ===\n")

test_states = [
    {
        "desc": "Critical Risk",
        "state": {"risk_assessment": SimpleNamespace(decision="Escalate / File SAR")},
        "expected": "Escalate / File SAR",
    },
    {
        "desc": "Low Risk",
        "state": {"risk_assessment": SimpleNamespace(decision="Clear")},
        "expected": "Clear",
    },
    {
        "desc": "Missing Risk Assessment",
        "state": {},
        "expected": "Unknown risk level — manual review required.",
    },
]

for test in test_states:
    print(f"--- {test['desc']} ---")
    result = recommend(test["state"])
    print(f"  Got: {result}")
    assert result == test["expected"], f"Expected '{test['expected']}', but got '{result}'"

print("\n=== ALL TESTS PASSED ===")
