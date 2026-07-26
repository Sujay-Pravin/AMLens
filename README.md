# AMLens — AI-Powered AML Investigation System

An end-to-end Anti-Money Laundering (AML) transaction network investigation system combining a Python analytics pipeline (validation → preprocessing → features → rules → ML inference + SHAP → fusion → graph analytics) and a LangGraph-based AI agent that generates natural-language compliance narrative reports.

---

## 1. Project Overview

Money laundering investigations start with raw transaction data and end with a compliance decision. This system automates the intermediate analytics and narrative generation steps:

1. **Ingest & validate** a raw transaction CSV.
2. **Engineer 17 behavioral features** (velocity, spikes, currency/bank indicators, network metrics) per transaction.
3. **Score** transactions via two lenses: deterministic **rules** and a trained **XGBoost classifier**, explained per-feature using **SHAP**.
4. **Fuse** both risk signals into a combined score and compliance action decision (Clear, Monitor, Investigate, Escalate).
5. **Analyze the transaction network** as a graph to surface hub accounts, suspected mule accounts, and cycles.
6. **Hand the evidence to the LangGraph Agent** which orchestrates the intent parsing, planning, execution check, and calls the Gemini LLM to write a plain-English compliance narrative.
7. **Display results** on a responsive HTML5 dashboard.

---

## 2. System Architecture

```
                                  AMLens/
  ┌────────────────────────────────────────────────────────────────────────┐
  │  CSV Ingestion ──▶ [DataLoader] ──▶ [Validator] ──▶ [Preprocessor]      │
  │                                                            │           │
  │                                                            ▼           │
  │                                                    [FeatureEngineer]   │
  │                                                      /          \      │
  │                                                     ▼            ▼     │
  │                                              [RuleEngine]   [AMLInference]
  │                                                     \            /     │
  │                                                      ▼          ▼      │
  │                                                      [RiskFusion]      │
  │                                                            │           │
  │                                                            ▼           │
  │                                                     [GraphAnalyzer]    │
  └────────────────────────────────────────────────────────────┬───────────┘
                                                               ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │                          LangGraph Agent Layer                         │
  │                                                                        │
  │   [workflow.invoke] ──▶ [Intent] ──▶ [Plan] ──▶ [Execute]              │
  │                                                     │                  │
  │                                                     ▼                  │
  │   [Narrative Report] ◀── [Recommender] ◀── [EvidenceExplainer (Gemini)]│
  └────────────────────────────────────────────────────────────┬───────────┘
                                                               ▼
                                             Frontend Dashboard (/ui)
```

The system is fully consolidated inside the `AMLens/` workspace:
* **`analytics/`** — Python SDK handles the core ingestion, processing, feature engineering, rules, ML inference, and network analytics.
* **`backend/`** — FastAPI application hosting the backend service, routes, database/API models, and the LangGraph agent orchestrating narration.
* **`models/`** — Trained XGBoost ML pipeline and estimators.
* **`backend/static/`** — Minimal same-origin HTML5/JS dashboard (served at `/ui`), useful for a zero-build smoke test of the API.
* **`frontend/`** — Standalone React + Vite neobrutalism dashboard that talks to the backend over HTTP/CORS. This is the primary UI.

---

## 3. Folder Structure

```
AMLens/
├── analytics/                  # Core analytics SDK subpackage
│   ├── config.py                #   Paths and config settings
│   ├── interfaces.py            #   Shared dataclasses (RuleResult, RiskAssessment, ...)
│   ├── data/                    #   Loader, Validator, Preprocessor
│   ├── features/                #   FeatureEngineer (17 engineered features)
│   ├── rules/                   #   RuleEngine + 11 point-based rules
│   ├── ml/                      #   AMLInference (XGBoost + SHAP local explanations)
│   ├── fusion/                  #   RiskFusion (combines rules & ML signals)
│   └── graph/                   #   GraphAnalyzer (NetworkX component, cycle, hub, mule metrics)
├── backend/                    # FastAPI web server & Agent layer
│   ├── app/
│   │   ├── main.py              #   FastAPI application setup & Static UI mount
│   │   ├── api/routes.py        #   API Router (/health, /status, /investigate, /upload)
│   │   ├── services/            #   investigation_service.py (runs analytics & invokes LangGraph)
│   │   ├── schemas/             #   Pydantic validation schemas (evidence.py, requests.py)
│   │   └── agents/              #   LangGraph agent workflow definitions
│   │       ├── workflow.py      #     Pregel orchestration graph (intent -> plan -> execute -> explain -> recommend)
│   │       ├── state.py         #     State TypedDict and conversion helpers
│   │       ├── intent_parser.py #     Intent parser (Regex + Gemini query intent classifier)
│   │       ├── planner.py       #     Static planner mapping intents to execution steps
│   │       ├── recommender.py   #     Deterministic compliance action mapper
│   │       └── evidence_explainer.py # LLM explainer translating metrics into plain text
│   ├── static/                  # Minimal same-origin UI dashboard (served at /ui)
│   │   └── index.html           #   Upload interface & results viewer
│   └── requirements.txt         # Pinned backend and analytics dependencies
├── frontend/                    # React + Vite neobrutalism dashboard (primary UI)
│   ├── src/
│   │   ├── api.js                #   Fetch client — reads backend URL from VITE_API_BASE_URL
│   │   ├── App.jsx                #   App shell: upload state, health check, results
│   │   └── components/            #   Header, UploadPanel, ResultsDashboard, Badge
│   ├── .env.example              # Template for VITE_API_BASE_URL
│   └── package.json
├── models/                      # XGBoost trained pipeline joblib files
├── test.py                      # Standalone pipeline validation script (no web server needed)
└── README.md                    # This documentation file
```

---

## 4. Running the Project

All setup and execution are handled inside the `AMLens` python environment.

### 4.1 Prerequisites
* Python 3.12 (standard stable release)
* Node.js 18+ and npm (for the React frontend)
* A Google AI Studio API Key (for Gemini intent parsing + narrative generation)

### 4.2 Backend Setup
1. Open your terminal in the `AMLens` folder (or navigate into it):
   ```bash
   cd AMLens
   ```
2. Create and activate a Python virtual environment:
   ```bash
   # Windows PowerShell
   python -m venv .venv
   .venv\Scripts\activate
   
   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install all dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
4. Configure your environment keys:
   * Copy the example environment template:
     ```bash
     cp backend/.env.example backend/.env
     ```
   * Open `backend/.env` and update the `GEMINI_API_KEY` with your Google AI Studio API key:
     ```env
     GEMINI_API_KEY=your_gemini_api_key_here
     ```
   * `CORS_ORIGINS` in `backend/app/config/settings.py` already allows the Vite dev server
     (`http://localhost:5173`, `http://127.0.0.1:5173`) and CRA-style `http://localhost:3000`
     out of the box. If you serve the frontend from a different origin (e.g. a deployed URL),
     add it to `CORS_ORIGINS` in `backend/.env`:
     ```env
     CORS_ORIGINS=["http://localhost:5173","https://your-frontend-domain.com"]
     ```

### 4.3 Frontend Setup
The React dashboard lives in `frontend/` and talks to the backend purely over HTTP — it does not
need to be built or served by FastAPI.

1. From the `AMLens` folder, install dependencies:
   ```bash
   cd frontend
   npm install
   ```
2. Configure the backend URL the frontend should call:
   ```bash
   cp .env.example .env
   ```
   Open `frontend/.env` and confirm `VITE_API_BASE_URL` points at your running backend (defaults
   to `http://127.0.0.1:8000`, matching step 4.5 below):
   ```env
   VITE_API_BASE_URL=http://127.0.0.1:8000
   ```
   Any time you change `.env`, restart `npm run dev` — Vite only reads env files on startup.

### 4.4 Running the Analytics Verification
To run a standalone check of the analytics pipeline (Loader → Validator → Preprocessor → FeatureEngineer → RuleEngine → ML → Fusion → Graph) without booting the web server:
```bash
python test.py
```
This processes `../dataset/sample.csv` and prints the structured evidence output of each step.

### 4.5 Running the Full Application (backend + frontend)
1. Start the FastAPI backend server (in one terminal, from `backend/`, with the venv active):
   ```bash
   cd backend
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
   Verify it's up: `http://127.0.0.1:8000/health` should return `{"status":"ok"}`.
2. Start the React frontend dev server (in a second terminal, from `frontend/`):
   ```bash
   cd frontend
   npm run dev
   ```
3. Open the URL Vite prints (typically `http://localhost:5173`) in your browser. The header shows
   a live "Backend online/unreachable" indicator — if it shows unreachable, double-check the
   backend is running and `VITE_API_BASE_URL` in `frontend/.env` matches its address.
4. Select a transaction dataset CSV (e.g., `dataset/sample.csv` or `dataset/mixed_aml_dataset.csv`
   from the root directory), optionally type a natural-language query, and click
   **"Run Investigation"** to process the data and view the final AI narrative report.

#### Alternative: minimal same-origin UI (no Node required)
For a quick, dependency-free smoke test, the backend also serves a minimal static dashboard at
the same origin (no CORS setup needed):
```
http://127.0.0.1:8000/ui/
```
It supports the same upload + query + report flow with plain HTML/JS instead of React.

---

## 5. Intent Parsing

`backend/app/agents/intent_parser.py` classifies a natural-language query into one of
`investigate | summarize | detect_pattern | score_risk | customer_lookup | graph_query | unknown`,
plus `aml_pattern`, `transaction_type`, and structured filters (customer/account id, date range,
amount range, bank). It's a hybrid pipeline:

1. **Rule-based extraction** (regex/`dateparser`) for high-precision entities: dates, customer/
   account ids, amount thresholds, bank names, country codes, named AML typologies (structuring,
   smurfing, layering, mule accounts, shell company, round-tripping, etc.), and transaction types
   (cash, wire, crypto, cheque, card, ACH).
2. **LLM extraction** (Gemini) for the semantic `intent` field, guided by a prompt that gives an
   explicit definition and disambiguation rule for each intent — in particular, "risky"/"riskiest"
   language alone no longer biases the model toward `graph_query`; that label is reserved for
   queries that actually reference the account network (hubs, mules, clusters, connections).
3. **Deterministic correction pass**: an explicit customer/account id in the query always wins
   (forces `customer_lookup`), and a `graph_query` result without any network-language keyword is
   demoted to the best keyword-based guess. The regex-extracted `aml_pattern`/`transaction_type`
   backfill anything the LLM left null.
4. **Keyword fallback** covering all six intents (not just two) if the LLM call errors, times out,
   or returns malformed JSON, so classification degrades gracefully instead of collapsing to
   `unknown` whenever Gemini is unavailable.
