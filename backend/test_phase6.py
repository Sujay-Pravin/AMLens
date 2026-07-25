"""Phase 6 validation — test Tool Manager execution and error handling."""

import time
from app.tools.tool_manager import call_tool, REGISTRY
from app.config.settings import settings

print("=== Testing Tool Integration Layer ===\n")

# 1. Test all 5 registered tools
print("--- 1. Testing Valid Tools ---")
filters = {"country": "AE"}

eda_res = call_tool("run_eda", filters=filters)
print(f"  run_eda: success, total_transactions = {eda_res.get('total_transactions')}")
assert "error" not in eda_res

feat_res = call_tool("generate_features", filters=filters)
print(f"  generate_features: success, cash_ratio = {feat_res.get('cash_ratio_avg')}")
assert "error" not in feat_res

rule_res = call_tool("detect_rules", filters=filters)
print(f"  detect_rules: success, hits = {rule_res.get('rule_hits')}")
assert "error" not in rule_res

anomaly_res = call_tool("detect_anomalies", filters=filters)
print(f"  detect_anomalies: success, score = {anomaly_res.get('anomaly_score')}")
assert "error" not in anomaly_res

risk_res = call_tool("calculate_risk", rule_out=rule_res, ml_out=anomaly_res)
print(f"  calculate_risk: success, band = {risk_res.get('risk_band')}")
assert "error" not in risk_res

# 2. Test unknown tool
print("\n--- 2. Testing Unknown Tool ---")
bad_res = call_tool("nonexistent_tool", filters=filters)
print(f"  Result: {bad_res}")
assert "error" in bad_res
assert "Unknown tool" in bad_res["error"]

# 3. Test timeout handling
print("\n--- 3. Testing Timeout Handling ---")
# Create a temporarily hanging function
def hanging_function(**kwargs):
    time.sleep(3)
    return {"status": "finished"}

# Inject it into registry temporarily
REGISTRY["hanging_tool"] = hanging_function

# Temporarily override settings to timeout quickly
original_timeout = settings.tool_timeout_seconds
settings.tool_timeout_seconds = 1.0

print(f"  Setting timeout to {settings.tool_timeout_seconds}s and calling a 3s tool...")
timeout_res = call_tool("hanging_tool")
print(f"  Result: {timeout_res}")

assert "error" in timeout_res
assert "timed out" in timeout_res["error"]

# Restore settings and registry
settings.tool_timeout_seconds = original_timeout
del REGISTRY["hanging_tool"]

print("\n=== ALL TESTS PASSED ===")
