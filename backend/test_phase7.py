"""Phase 7 validation — test LangGraph Workflow orchestration."""

import json
from app.agents.workflow import workflow

print("=== Testing LangGraph Workflow Orchestration ===\n")

# 1. Initialize the state
initial_state = {
    "user_query": "any structuring for accounts in UAE last month?",
    "filters": {"country": "AE"}
}

print(f"--- Triggering Workflow ---")
print(f"  Query: '{initial_state['user_query']}'")
print(f"  Filters: {initial_state['filters']}")
print()

# 2. Invoke the graph
# The graph runs synchronously. Since the LLM intent parsing is involved, it might take a few seconds.
try:
    final_state = workflow.invoke(initial_state)
except Exception as e:
    print(f"WORKFLOW CRASHED: {type(e).__name__}: {e}")
    raise

# 3. Verify results
print("--- Execution Trace ---")
for step in final_state.get("trace", []):
    print(f"  -> {step}")
    
print("\n--- Parsed Intent ---")
print(f"  {final_state.get('parsed_intent')}")
print(f"  Entities: {final_state.get('entities')}")

print("\n--- Execution Plan ---")
print(f"  {final_state.get('execution_plan')}")

print("\n--- Tool Outputs ---")
for tool, out in final_state.get('tool_outputs', {}).items():
    print(f"  {tool}: {len(out)} keys")

print("\n--- Risk Results ---")
print(f"  {final_state.get('risk_results')}")

print("\n--- Explanation & Recommendation (Stubbed) ---")
print(f"  Explain: {final_state.get('explanation')}")
print(f"  Recommend: {final_state.get('recommendation')}")
print()

# Assertions
trace = final_state.get("trace", [])
assert trace == [
    "intent_parsed", "plan_created", "tools_executed", 
    "explanation_generated", "recommendation_generated"
], "Trace order is incorrect!"

assert len(final_state.get("execution_plan", [])) > 0, "Execution plan is empty!"
assert "error" not in final_state.get("errors", []), "Graph execution encountered errors!"

print("=== ALL TESTS PASSED ===")
