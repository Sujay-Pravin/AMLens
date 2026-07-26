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
* **`static/`** — Minimal HTML5/JS dashboard.

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
│   ├── static/                  # Minimal UI dashboard
│   │   └── index.html           #   Upload interface & results viewer
│   └── requirements.txt         # Pinned backend and analytics dependencies
├── models/                      # XGBoost trained pipeline joblib files
├── test.py                      # Standalone pipeline validation script (no web server needed)
└── README.md                    # This documentation file
```

---

## 4. Running the Project

All setup and execution are handled inside the `AMLens` python environment.

### 4.1 Prerequisites
* Python 3.12 (standard stable release)
* A Google AI Studio API Key (for Gemini narrative generation)

### 4.2 Setup
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

### 4.3 Running the Analytics Verification
To run a standalone check of the analytics pipeline (Loader → Validator → Preprocessor → FeatureEngineer → RuleEngine → ML → Fusion → Graph) without booting the web server:
```bash
python test.py
```
This processes `../dataset/sample.csv` and prints the structured evidence output of each step.

### 4.4 Running the Web Application
1. Start the FastAPI backend server:
   ```bash
   cd backend
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
2. Open your browser and navigate to the dashboard UI:
   ```
   http://127.0.0.1:8000/ui/
   ```
3. Select a transaction dataset CSV (e.g., `dataset/sample.csv` or `dataset/mixed_aml_dataset.csv` from the root directory) and click **"Run Investigation"** to process the data and view the final AI narrative report.
