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

