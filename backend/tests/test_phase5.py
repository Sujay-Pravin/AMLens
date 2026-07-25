"""Phase 5 validation — test Execution Planner with sample intents."""

from app.agents.planner import plan

# Mocked intent outputs derived from Phase 4 results
test_cases = [
    {
        "description": "1. Summarize transactions",
        "intent": {"intent": "summarize", "aml_pattern": None}
    },
    {
        "description": "2. Any structuring in UAE?",
        "intent": {"intent": "detect_pattern", "aml_pattern": "structuring"}
    },
    {
        "description": "3. Score risk for high-velocity",
        "intent": {"intent": "score_risk", "aml_pattern": "high-velocity"}
    },
    {
        "description": "4. Detect smurfing patterns",
        "intent": {"intent": "detect_pattern", "aml_pattern": "smurfing"}
    },
    {
        "description": "5. Investigate dormant reactivation",
        "intent": {"intent": "investigate", "aml_pattern": "dormant account reactivation"}
    },
    {
        "description": "6. Show rapid cash-out activity",
        "intent": {"intent": "investigate", "aml_pattern": "rapid cash-out"}
    },
    {
        "description": "7. What's the anomaly score?",
        "intent": {"intent": "score_risk", "aml_pattern": None}
    },
    {
        "description": "8. Flag layering behavior",
        "intent": {"intent": "detect_pattern", "aml_pattern": "layering"}
    },
    {
        "description": "9. Empty/Unknown intent fallback",
        "intent": {"intent": "unknown", "aml_pattern": None}
    }
]

print("=== Testing Execution Planner Agent ===\n")

for case in test_cases:
    print(f"--- {case['description']} ---")
    print(f"  Input: {case['intent']}")
    
    execution_plan = plan(case['intent'])
    
    print(f"  Plan : {execution_plan}\n")

# Verify order and de-duplication
test_dupes = {"intent": "investigate", "aml_pattern": "layering"} # Hits multiple conditions
dupe_plan = plan(test_dupes)
assert len(dupe_plan) == len(set(dupe_plan)), "Plan contains duplicates!"

expected_order = [
    "run_eda",
    "generate_features",
    "detect_rules",
    "detect_anomalies",
    "calculate_risk",
]
for tool in dupe_plan:
    assert tool in expected_order, f"Unknown tool: {tool}"
    
# Check relative ordering
indices = [expected_order.index(t) for t in dupe_plan]
assert indices == sorted(indices), f"Tools executed out of order: {dupe_plan}"

print("=== ALL TESTS PASSED ===")
