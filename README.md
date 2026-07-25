# AMLens — AI-Powered Suspicious Activity Detection

> An agentic AI system that turns natural-language AML queries into structured investigation plans, executes analytics tools, and returns explainable, actionable compliance answers.



## ✅ Completed Work

### Phase 0 — Environment & Setup ✅

- **Python 3.13 virtual environment** created and all dependencies installed
  - Used Python 3.13 (not 3.14) because `pydantic-core` PyO3 bindings don't yet support 3.14
- **`requirements.txt`** with pinned versions for all 14 core dependencies:
  - `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`
  - `langgraph`, `langchain-core`, `huggingface_hub`
  - `python-dotenv`, `dateparser`, `python-multipart`
  - `httpx`, `pytest`, `pytest-asyncio`
- **`.env` + `.env.example`** — HuggingFace token, model config, app settings
- **`.gitignore`** — venv, env files, pycache, IDE, OS artifacts
- **`verify_hf.py`** — standalone HF connectivity test with clear error messages and backup model suggestions
- **HuggingFace verified** — Llama-3.1-8B-Instruct confirmed live and responding
- **Full directory skeleton** created with all `__init__.py` files across 6 subpackages

### Phase 1 — Backend Infrastructure ✅

- **`app/config/settings.py`** — Centralized configuration via `pydantic-settings`:
  - HF token & model, tool timeout, environment, log level
  - CORS origins for React dev servers (`localhost:5173`, `localhost:3000`)
  - `use_dummy_analytics` feature flag for Phase 12 swap
- **`app/core/logging.py`** — Dual-mode structured logging:
  - **Dev:** Colored, human-readable console output with timestamps
  - **Prod:** JSON-formatted log lines with structured fields (`query`, `tool`, `duration_ms`, `node`)
  - Silences noisy third-party loggers (httpx, httpcore, uvicorn.access, huggingface_hub)
- **`app/core/exceptions.py`** — Three-tier exception hierarchy + FastAPI handlers:
  - `AMLensError` (base) → `ToolExecutionError`, `IntentParsingError`, `WorkflowError`
  - All errors return structured JSON: `{error, message, detail}`
  - Catch-all handler prevents raw 500 responses — every failure is clean
- **`app/main.py`** — FastAPI application factory:
  - CORS middleware configured for React frontend
  - Lifespan events with structured startup/shutdown logging
  - Exception handlers registered globally
  - Stub endpoints: `GET /health` and `GET /status`

### Phase 2 — Shared State Schema ✅

- **`app/agents/state.py`** — Core shared state for the LangGraph workflow:
  - `AgentState(BaseModel)` with 11 fields: `user_query`, `filters`, `parsed_intent`, `entities`, `execution_plan`, `tool_outputs`, `risk_results`, `explanation`, `recommendation`, `trace`, `errors`
  - `AgentStateDict(TypedDict)` adapter for LangGraph compatibility
  - Round-trip conversion helpers: `state_to_dict()` / `dict_to_state()`
- **`app/schemas/tool_io.py`** — Integration contract with Member 2 (5 output models):
  - `EDAOutput`, `FeatureOutput`, `RuleOutput`, `AnomalyOutput`, `RiskOutput`
  - Range validation on scores (`0.0–1.0`), `Literal` type on `risk_band`
- **`app/schemas/requests.py`** — API request/response models:
  - `QueryRequest` (validated: min 1 char, max 2000 chars)
  - `QueryResponse` (mirrors AgentState, explanation + recommendation prioritized)
  - `UploadRequest/Response` stubs, `HealthResponse`, `StatusResponse`
- **`app/tools/tool_interfaces.py`** — Protocol classes for the 5 analytics functions (structural subtyping — Member 2 doesn't need to inherit anything)

### Phase 3 — Dummy Analytics API ✅

- **`app/tools/dummy_analytics.py`** — realistic stand-in for Member 2's 5 analytics functions:
  - `run_eda()` — EDA summary with varied country pools and transaction volumes
  - `generate_features()` — AML features (velocity, dormancy, cash ratio, cross-border %)
  - `detect_rules()` — rule-based detection across 8 AML patterns with detailed hit info
  - `detect_anomalies()` — ML anomaly scores with top anomalous account lists
  - `calculate_risk()` — composite scoring (40% rules + 60% ML) with contributing factors
- **Design features:**
  - Deterministic seeding from filters → same query always produces same results (reproducible demos)
  - Varied, believable data: different risk bands, country sets, pattern combinations
  - Edge cases covered: empty rules, borderline scores, max risk scenarios
  - All outputs validate against `app/schemas/tool_io.py` Pydantic models

## 🚀 Quick Start

```bash
# 1. Navigate to backend
cd backend

# 2. Create venv with Python 3.13
py -3.13 -m venv venv

# 3. Activate venv
.\venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env
# Edit .env with your HuggingFace token

# 6. Verify HF connectivity
python verify_hf.py

# 7. Start the server
uvicorn app.main:app --reload --port 8000

# 8. Check health
curl http://localhost:8000/health
```

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HF_TOKEN` | ✅ | — | HuggingFace API access token |
| `HF_MODEL` | ❌ | `meta-llama/Llama-3.1-8B-Instruct` | Model for intent parsing + explanation |
| `ENV` | ❌ | `dev` | Environment (`dev` / `staging` / `prod`) |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level |
| `TOOL_TIMEOUT_SECONDS` | ❌ | `15` | Max wait per analytics tool call |

