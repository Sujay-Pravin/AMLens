"""Phase 10 validation — test FastAPI Endpoints with TestClient."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=== Testing API Layer (FastAPI) ===\n")

print("--- 1. Testing GET /health ---")
response = client.get("/health")
print(f"Status: {response.status_code}")
print(f"Body: {response.json()}")
assert response.status_code == 200
assert response.json() == {"status": "ok"}

print("\n--- 2. Testing GET /status ---")
response = client.get("/status")
print(f"Status: {response.status_code}")
status_data = response.json()
print(f"Body: {status_data}")
assert response.status_code == 200
assert status_data["agent"] == "ready"
assert status_data.get("tools_registered", status_data.get("registered_tools")) == 5

print("\n--- 3. Testing POST /query (Valid Query) ---")
# Using a simple query to ensure the graph runs quickly
payload = {
    "query": "summarize transactions for CUST-1023",
    "filters": {"country": "AE"}
}
print(f"Sending payload: {payload}")
response = client.post("/query", json=payload)
print(f"Status: {response.status_code}")
assert response.status_code == 200

query_data = response.json()
print(f"Intent: {query_data.get('parsed_intent')}")
print(f"Explanation: {query_data.get('explanation')}")
print(f"Recommendation: {query_data.get('recommendation')}")
print(f"Trace: {query_data.get('trace')}")
assert "intent_parsed" in query_data["trace"]
assert query_data["explanation"] != ""

print("\n--- 4. Testing POST /query (Malformed Input) ---")
bad_payload = {
    "query": "", # Query is empty, should fail validation (min_length=1)
    "filters": "not a dict" # Bad type
}
print(f"Sending bad payload: {bad_payload}")
response = client.post("/query", json=bad_payload)
print(f"Status: {response.status_code}")
# FastAPI returns 422 Unprocessable Entity for validation errors
assert response.status_code == 422
error_data = response.json()
print(f"Error Body: {error_data}")
assert "detail" in error_data

print("\n=== ALL TESTS PASSED ===")
