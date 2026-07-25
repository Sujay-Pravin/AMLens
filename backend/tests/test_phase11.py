"""
Phase 11 validation — End-to-End API Testing.

Tests the live FastAPI app with 8 real-world AML queries to ensure
the entire LangGraph pipeline processes them successfully and quickly.
"""

import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=== Testing End-to-End AMLens Pipeline ===\n")

queries = [
    "summarize transactions for CUST-1023",
    "any structuring for accounts in UAE last month?",
    "score risk for high-velocity accounts",
    "detect smurfing patterns above $10,000",
    "investigate dormant account reactivation in Singapore",
    "show me rapid cash-out activity for CUST-4455 since January",
    "what's the anomaly score for transactions over ₹50,000?",
    "flag layering behavior in accounts from AE and IN",
]

total_start = time.time()
passed_count = 0

for i, query in enumerate(queries, 1):
    print(f"--- Query {i}: '{query}' ---")
    start = time.time()
    
    response = client.post("/query", json={"query": query})
    elapsed = time.time() - start
    
    if response.status_code != 200:
        print(f"  [ERROR] Status {response.status_code}: {response.text}")
        continue
        
    data = response.json()
    
    print(f"  Status        : 200 OK")
    print(f"  Response Time : {elapsed:.2f}s")
    print(f"  Parsed Intent : {data.get('parsed_intent', {}).get('intent')}")
    print(f"  Plan          : {data.get('execution_plan')}")
    print(f"  Trace         : {data.get('trace')}")
    
    risk_results = data.get("risk_results")
    risk_band = risk_results.get("risk_band") if risk_results else "None"
    print(f"  Risk Band     : {risk_band}")
    
    print(f"  Recommendation: {data.get('recommendation')}")
    print(f"  Explanation   : {data.get('explanation')[:100]}...") # Truncated for terminal readability
    print()
    
    # Assertions
    assert "error" not in data.get("errors", []), "Graph errors encountered!"
    assert data.get("explanation"), "Missing explanation!"
    assert data.get("recommendation"), "Missing recommendation!"
    # Relaxed SLA to 45.0s to account for remote Google GenAI latency (two LLM calls)
    assert elapsed < 45.0, f"Query took too long: {elapsed}s"
    
    passed_count += 1

total_elapsed = time.time() - total_start
print(f"=== E2E TESTING COMPLETE ===")
print(f"  {passed_count}/{len(queries)} queries passed in {total_elapsed:.2f}s.")

if passed_count == len(queries):
    print("  Status: READY FOR DEMO / PHASE 12 SWAP")
else:
    print("  Status: FAILED")
