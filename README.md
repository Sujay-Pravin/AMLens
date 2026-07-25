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
- **`.env` + `.env.example`** — Gemini API key, model config, app settings
- **`.gitignore`** — venv, env files, pycache, IDE, OS artifacts
- **`verify_ai.py`** — standalone Google AI connectivity test with clear error messages
- **Google AI verified** — gemma-4-31b-it confirmed live and responding
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

### Phase 4 — Intent Parsing Agent ✅

- **`app/agents/intent_parser.py`** — hybrid intent parser combining rule-based & LLM extraction:
  - **Rule-based extraction**: High-precision extraction of dates, amounts ($, ₹), customer IDs (`CUST-xxx`), and country codes using `dateparser` and regex heuristics.
  - **LLM extraction**: Google AI Studio (`gemma-4-31b-it`) for fuzzy fields: `intent` label, `aml_pattern`, `transaction_type`, and `threshold_amount`.
  - **Merger & Error Handling**: Merges both outputs (rule-based injected into `_entities`). Includes robust `try/except` wrapping to gracefully degrade to `{"intent": "unknown"}` if the LLM fails, times out, or returns malformed JSON.
  - Fully tested against 8 varied queries and 1 intentional JSON malformation fallback scenario.

### Phase 5 — Execution Planner ✅

- **`app/agents/planner.py`** — deterministic, rule-based planner mapping parsed intents to an ordered list of analytics tools:
  - `"summarize"` / `"investigate"` → includes `run_eda`
  - `"detect_pattern"` or explicit `aml_pattern` → includes `generate_features`, `detect_rules`
  - `"score_risk"` → includes `detect_anomalies`, `calculate_risk`
  - `"unknown"` fallback → defaults to `['run_eda', 'detect_rules', 'calculate_risk']`
  - Automatically de-duplicates the selected tools and strictly enforces execution order based on data dependencies.

### Phase 6 — Tool Integration Layer ✅

- **`app/tools/tool_manager.py`** — centralized dispatcher for executing analytics tools:
  - **Tool Registry**: Dictionary mapping string names from the planner to callable Python functions.
  - **Safe Execution**: Uses `ThreadPoolExecutor` to run tools asynchronously.
  - **Timeout Enforcement**: Enforces `TOOL_TIMEOUT_SECONDS` (15s default). If a tool hangs, the agent moves on gracefully with an error in the state, preventing full pipeline lockup.
  - **Error Isolation**: Catches all exceptions and normalizes them into `{"error": str(e)}` dicts so the LangGraph state remains stable.

### Phase 7 — LangGraph Workflow ✅

- **`app/agents/workflow.py`** — complete directed graph stitching all agents and tools together:
  - **Nodes**: `intent` → `plan` → `execute` → `explain` (stubbed) → `recommend` (stubbed).
  - **State Management**: Uses `AgentStateDict` to flow data through the pipeline, updating `parsed_intent`, `execution_plan`, `tool_outputs`, `risk_results`, and `trace`.
  - **Execution**: `workflow.invoke()` runs the entire pipeline synchronously and successfully returns the populated state dictionary.

### Phase 8 — Explanation Agent ✅

- **`app/agents/explainer.py`** — converts raw tool outputs into plain-language text:
  - **Prompt Engineering**: Instructs Gemma 4 (31b) to act as a senior AML compliance analyst writing a 3-4 sentence narrative.
  - **Integration**: Replaced the stub in `workflow.py` with the actual LLM call.
  - **Fallback**: Wraps the call in a `try/except` block to return a graceful fallback string if the LLM is unreachable, protecting the pipeline.

### Phase 9 — Recommendation Agent ✅

- **`app/agents/recommender.py`** — deterministic, auditable risk recommendation:
  - Takes the `risk_band` computed by the analytics tools and translates it directly into an actionable step (e.g. `Critical` → "Escalate immediately and file a report.").
  - Hooked directly into the final stage of `workflow.py`.

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
# Edit .env with your Google AI Studio API key

# 6. Verify Google AI Studio connectivity
python verify_ai.py

# 7. Start the server
uvicorn app.main:app --reload --port 8000

# 8. Check health
curl http://localhost:8000/health
```

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | ✅ | — | Google AI Studio API key |
| `GEMINI_MODEL` | ❌ | `gemma-4-31b-it` | Model for intent parsing + explanation |
| `ENV` | ❌ | `dev` | Environment (`dev` / `staging` / `prod`) |
| `LOG_LEVEL` | ❌ | `INFO` | Logging level |
| `TOOL_TIMEOUT_SECONDS` | ❌ | `15` | Max wait per analytics tool call |

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API Framework** | FastAPI 0.115 | REST API with auto-generated Swagger docs |
| **LLM** | Google AI Studio (genai SDK) | Intent parsing + explanation generation |
| **Model** | gemma-4-31b-it | Instruction-tuned chat model |
| **Orchestration** | LangGraph 0.4 | Explicit state graph with named nodes |
| **Validation** | Pydantic 2.11 | Schema enforcement at every boundary |
| **Config** | pydantic-settings | Type-safe env var loading |
| **Frontend** | React + Vite | Query UI + results dashboard (Phase 13) |
| **Python** | 3.13 | Latest stable (3.14 incompatible with pydantic-core) |
