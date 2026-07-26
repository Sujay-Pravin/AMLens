"""Phase 7 validation — test LangGraph Workflow orchestration over real analytics evidence."""

from types import SimpleNamespace

from app.agents.workflow import workflow

print("=== Testing LangGraph Workflow Orchestration ===\n")

# Stand-in evidence shaped like the real analytics dataclasses
# (ValidationReport, RuleResult, MLResult, RiskAssessment, GraphMetrics).
validation = SimpleNamespace(
    total_rows=1000, total_columns=12, duplicate_rows=3, missing_columns=[]
)
rule_result = SimpleNamespace(
    triggered_rules=["structuring", "layering"], risk_score=7, explanations=["High velocity"]
)
ml_result = SimpleNamespace(
    prediction=1,
    probability=0.87,
    top_positive_features=[SimpleNamespace(feature="amount_paid")],
    top_negative_features=[SimpleNamespace(feature="account_age")],
)
risk_assessment = SimpleNamespace(
    final_score=0.79, risk_level="High", decision="Investigate", reasons=["High velocity"]
)
graph_metrics = SimpleNamespace(
    node_count=42, edge_count=88, num_components=3, hub_accounts=["ACC-1"],
    mule_accounts=[], cycles=[],
)

initial_state = {
    "user_query": "Investigate the highest-risk transaction in 'sample.csv'.",
    "filters": {},
    "validation": validation,
    "rule_result": rule_result,
    "ml_result": ml_result,
    "risk_assessment": risk_assessment,
    "graph_metrics": graph_metrics,
}

print("--- Triggering Workflow ---")
try:
    final_state = workflow.invoke(initial_state)
except Exception as e:
    print(f"WORKFLOW CRASHED: {type(e).__name__}: {e}")
    raise

print("--- Execution Trace ---")
for step in final_state.get("trace", []):
    print(f"  -> {step}")

print("\n--- Explanation & Recommendation ---")
print(f"  Explain: {final_state.get('explanation')}")
print(f"  Recommend: {final_state.get('recommendation')}")
print()

# Assertions
trace = final_state.get("trace", [])
assert trace == [
    "intent_parsed", "plan_created", "tools_executed",
    "explanation_generated", "recommendation_generated"
], "Trace order is incorrect!"

assert not final_state.get("errors"), f"Graph execution encountered errors: {final_state.get('errors')}"
assert final_state.get("explanation"), "Missing explanation!"
assert final_state.get("recommendation") == "Investigate", "Recommendation should surface RiskAssessment.decision!"

print("=== ALL TESTS PASSED ===")
