# AMLens — AI-Powered AML Investigation System

An end-to-end Anti-Money Laundering (AML) transaction investigation system: a
Python analytics pipeline (data validation → feature engineering → rule
engine → ML inference with SHAP → risk fusion → transaction graph analytics)
feeding a LangGraph-based AI agent that turns raw evidence into a
compliance-analyst-style investigation report.

This README documents the **analytics pipeline** (`analytics/`) in depth —
what each stage does, why it exists, and how it feeds an investigation — plus
how it's wired into the AI agent (`AMLens/`) and exposed through a FastAPI
endpoint and a minimal frontend.

---

## 1. Project Overview

Money laundering investigations start with a mountain of raw transaction
data and end with a human decision: clear, monitor, escalate, or file a
report. This system automates everything in between:

1. **Ingest & validate** a raw transaction CSV.
2. **Engineer behavioral features** (velocity, spikes, network spread) per transaction.
3. **Score** each transaction two ways — deterministic **rules** (auditable, explainable) and a trained **XGBoost model** (captures non-linear/behavioral patterns), each explained down to the individual feature via **SHAP**.
4. **Fuse** both signals into one risk score, level, and recommended decision.
5. **Analyze the transaction network** as a graph to surface hub accounts, suspected mule accounts, and cyclic (round-tripping) money flows.
6. **Hand all of that evidence to an LLM agent**, which writes a plain-English investigation narrative — explaining the evidence rather than recomputing it.
7. **Surface it all** through a REST API and a bare-bones upload-and-investigate web UI.

## 2. System Architecture

```
                 ┌────────────────────────────────────────────────────────────┐
                 │                     analytics/  (this repo)                │
                 │                                                            │
  CSV ──▶ Loader ──▶ Validator ──▶ Preprocessor ──▶ FeatureEngineer           │
                 │                                        │                  │
                 │                                        ▼                  │
                 │                                   RuleEngine               │
                 │                                        │                  │
                 │                                        ▼                  │
                 │                              AMLInference (XGBoost+SHAP)   │
                 │                                        │                  │
                 │                                        ▼                  │
                 │                                   RiskFusion               │
                 │                                        │                  │
                 │                            GraphAnalyzer (whole dataset)   │
                 └────────────────────────────────────────┼──────────────────┘
                                                            ▼
                 ┌────────────────────────────────────────────────────────────┐
                 │              AMLens/backend/  (LangGraph agent, locked)     │
                 │                                                            │
                 │  POST /investigate ──▶ investigation_service ──▶ evidence   │
                 │                                        │                  │
                 │                                        ▼                  │
                 │                          evidence_explainer (Gemini LLM)   │
                 │                                        │                  │
                 │                                        ▼                  │
                 │                          Investigation Report + Decision   │
                 └────────────────────────────────────────┼──────────────────┘
                                                            ▼
                                          Frontend (static/index.html, /ui)
```

Two independently-owned, independently-git-tracked codebases:

- **`analytics/`** — this contribution. A pure Python SDK, no web framework, no LLM. Fully testable standalone (`python test.py`).
- **`AMLens/`** — a teammate's LangGraph agent + FastAPI backend, handling natural-language queries, tool orchestration, and LLM narration. Its existing `/query` flow (NL query → dummy analytics → Gemini explanation) is untouched. This project adds one new, additive endpoint, `POST /investigate`, that runs the *real* analytics pipeline on an uploaded CSV and reuses AMLens's Gemini-agent plumbing to narrate the findings.

## 3. Analytics Pipeline

Each stage is a static-method class in `analytics/`, composable and independently testable.

### 3.1 Loader (`analytics/data/loader.py`)
**Why:** every pipeline needs one place that turns a file on disk into a DataFrame, without opinions about content.
**Produces:** a raw `pandas.DataFrame` read from CSV/Parquet.
**AML value:** decouples "where the data comes from" from everything downstream — the same pipeline works on a bank's batch export or an uploaded investigation file.

### 3.2 Validator (`analytics/data/validator.py`)
**Why:** garbage in, garbage out — the rule engine and model both assume a specific schema (sender/receiver, currencies, amounts, timestamps). Silent schema drift is how false negatives happen.
**Produces:** a `ValidationReport` (`valid`, `total_rows`, `total_columns`, `missing_columns`, `duplicate_rows`, `missing_values`).
**AML value:** the first artifact in every investigation report — reviewers need to know the data was complete *before* trusting the score.

### 3.3 Preprocessor (`analytics/data/preprocess.py`)
**Why:** normalizes the IBM-AML-style raw schema (`Timestamp`, `Amount Received`, `Account.1`, …) into a consistent internal shape: renamed snake_case columns, parsed timestamps, coerced numeric/string dtypes, deduplicated rows, chronologically sorted.
**Produces:** a clean `DataFrame` with `sender_entity_id`/`receiver_entity_id`, typed `timestamp`, numeric amounts.
**AML value:** velocity and rolling-window features (see below) are only correct if the data is deduplicated and time-ordered first.

### 4. Feature Engineering (`analytics/features/engineer.py`)

**Why:** raw transaction fields (amount, currency, timestamp) don't by themselves distinguish a normal transaction from a laundering pattern. Laundering shows up in *behavior over time* — bursts of activity, sudden new counterparties, amounts that don't match a sender's history.

**Produces** 17 engineered features per transaction, computed via a single chronological pass per sender/receiver:

| Feature | What it captures |
|---|---|
| `time_since_prev_tx` | Gap since this sender's last transaction |
| `sender_tx_count_1d` / `sender_tx_count_7d` | Sender velocity (structuring/smurfing signal) |
| `receiver_tx_count_7d` | Receiver velocity (funnel-account signal) |
| `rolling_amount_mean_5` / `rolling_amount_std_5` | Sender's recent amount baseline |
| `sender_unique_receivers_30d` | Fan-out — one sender, many counterparties |
| `amount_zscore_prior_5` | How far this amount deviates from the sender's own recent history |
| `same_currency` / `same_bank` | Cross-currency / cross-bank movement |
| `is_round_amount` | Round-number amounts (a classic structuring tell) |
| `hour` / `day_of_week` / `is_weekend` / `is_night_time` | Timing anomalies |
| `high_value_trans` | Above the reporting-threshold flag |
| `amount_diff` | Paid vs. received mismatch (FX slippage or misreporting) |

**AML value:** this is the shared feature set consumed by *both* the rule engine and the ML model — one engineering pass, two independent scoring lenses.

### 5. Rule Engine (`analytics/rules/engine.py`, `analytics/rules/rules.py`)

**Why:** compliance teams need deterministic, auditable, instantly-explainable triggers that don't depend on a model's internals — regulators expect to see "why was this flagged" in plain rule form.

**Produces** a `RuleResult` (`triggered_rules`, `risk_score`, `explanations`) from 11 independent rules (High Value, Night Transaction, Sender/Receiver Velocity, Amount Spike, Many Unique Receivers, Cross-Bank Transfer, Currency Switch, Round Amount, Large Amount Difference), each with a fixed point weight (max combined score: 114).

**AML value:** the first, fastest layer of defense — cheap to compute, trivial to justify to an auditor, and immune to model drift.

### 6. Machine Learning Pipeline (`analytics/ml/inference.py`)

**Why:** rules alone miss non-linear, multi-feature interactions (e.g. "night transaction + currency switch + high sender velocity, but only when the receiver is also new" isn't easily hand-written). A trained model generalizes across these interactions.

**Model:** an `XGBoost` classifier inside an `sklearn` `Pipeline` (`preprocessor` → `classifier`), trained on the 17 engineered features plus `Receiving Currency` / `Payment Currency` (one-hot). **`Payment Format` (transaction mode) was deliberately excluded from training and is explicitly dropped at inference time** (`AMLInference._prepare_for_model`) — it's a categorical field prone to encoding bias unrelated to actual laundering risk, so it never reaches the model even though it's still preserved in the DataFrame for EDA use elsewhere.
**Produces:** an `MLResult` (`prediction`, `probability`, `confidence`, plus SHAP explanations — see below).
**AML value:** catches patterns a fixed rule set can't articulate, while still being explainable per-transaction (next section) so it isn't a black box in a regulated context.

### 7. SHAP Explainability (part of `analytics/ml/inference.py`)

**Why:** an unexplained fraud probability is not actionable — an investigator (or regulator) needs to know *which features* pushed the score up or down, for *this specific transaction*.

**How:** `shap.TreeExplainer(classifier, feature_perturbation="tree_path_dependent")` computes local Shapley values for every transformed feature; `extract_pos_class_shap` extracts the positive (laundering) class's contributions.

**Produces:** the top 5 features increasing risk and top 5 decreasing risk (`top_positive_features` / `top_negative_features`, each a `FeatureContribution` with `feature`, `value`, `impact`), plus the full `shap_values` dict.

**AML value:** this is what lets the downstream LLM agent write "flagged primarily because of X, Y, Z" instead of a bare probability number — SHAP output is fed directly into the investigation narrative prompt.

### 8. Risk Fusion (`analytics/fusion/engine.py`)

**Why:** rules and ML each catch different things and each have blind spots; a single combined score is what a human decision-maker actually needs to act on.

**How:** `final_score = 0.6 × ML probability + 0.4 × normalized rule score` (rule score normalized against the 114-point maximum), bucketed into risk levels (`< 0.25` Low, `< 0.5` Medium, `< 0.75` High, else Critical), each mapped to a decision (Clear / Monitor / Investigate / Escalate & File SAR).

**Produces:** a `RiskAssessment` (`final_score`, `risk_level`, `decision`, `reasons` — combining rule explanations with the ML's top contributing features).

**AML value:** the single number and recommended action that drives triage — everything upstream is evidence, this is the verdict.

### 9. Graph Analytics (`analytics/graph/engine.py`)

**Why:** individual transactions can look clean while the *network* around them tells a different story — layering and round-tripping only show up when you look at the flow of funds across many accounts.

**How:** builds a directed `networkx` graph (sender → receiver, weighted by transaction count/amount) from the whole dataset, computes:

- In/out-degree and PageRank per account
- Weakly-connected component count
- Bounded-length cycle detection (round-tripping candidates)
- **Hub accounts** — unusually high total degree
- **Mule accounts** — accounts with balanced high in/out-degree and amount-in ≈ amount-out (pass-through heuristic)

**Produces:** a `GraphMetrics` object with all of the above.

**AML value:** surfaces network-level laundering patterns (funnel accounts, mule networks, circular transfers) that no single-transaction score can see.

## 10. Integration with AMLens

`AMLens/backend/` (a separate, teammate-owned, locked codebase) already implements a LangGraph agent with a natural-language `/query` endpoint. That endpoint's tool-calling seam (`app/tools/tool_manager.py`) is intentionally built against a thin, `filters: dict`-driven contract (`app/schemas/tool_io.py`) with no notion of an uploaded CSV — forcing our richer evidence (SHAP values, graph metrics) through it would be lossy and wouldn't match the evidence AMLens's agent was asked to consume. Instead, integration is **additive**:

| New file | Purpose |
|---|---|
| `AMLens/backend/app/services/investigation_service.py` | Imports `analytics/` directly (via a `sys.path` bootstrap, since AMLens is a separately-rooted nested repo) and runs the full pipeline on an uploaded CSV: scores every transaction, picks the highest-risk one as the investigation subject, and runs `GraphAnalyzer` dataset-wide. |
| `AMLens/backend/app/schemas/evidence.py` | Pydantic response models mirroring the analytics dataclasses (`ValidationReport`, `RuleResult`, `MLResult`, `RiskAssessment`, `GraphMetrics`) — separate from AMLens's existing `tool_io.py` contract, which is untouched. |
| `AMLens/backend/app/agents/evidence_explainer.py` | A new LLM narrative generator, parallel to AMLens's existing `explainer.py`. Reuses the same `google-genai` client/config pattern. Its prompt explicitly instructs the model to **explain the already-computed evidence, not recompute a risk score**. Falls back to a deterministic templated narrative if the Gemini call fails (e.g. no API key configured). |
| `AMLens/backend/app/api/routes.py` | One new route appended: `POST /investigate`. The existing `/query`, `/upload`, `/health`, `/status` routes, `workflow.py`, `planner.py`, `intent_parser.py`, `tool_manager.py`, and `dummy_analytics.py` are all **untouched**. |
| `AMLens/backend/app/main.py` | One addition: a `StaticFiles` mount at `/ui` for the minimal frontend. |

## 11. API Endpoints

All endpoints are served by the AMLens FastAPI app (`AMLens/backend/app/main.py`).

| Method | Path | Description |
|---|---|---|
| `POST` | `/investigate` | **New.** Upload a transaction CSV (multipart `file`). Runs the full analytics pipeline and returns validation, rule findings, ML prediction + SHAP, fused risk assessment, graph metrics, a per-transaction risk table, and an LLM-generated investigation report. |
| `GET` | `/health` | Liveness probe (pre-existing). |
| `GET` | `/status` | Agent/config readiness probe (pre-existing). |
| `POST` | `/query` | Natural-language query → LangGraph agent, currently backed by dummy/synthetic data (pre-existing, unmodified). |
| `POST` | `/upload` | Pre-existing stub, unmodified — not the real CSV upload path (use `/investigate` instead). |
| `GET` | `/ui/` | **New.** Minimal upload-and-investigate frontend. |
| `GET` | `/docs` | Auto-generated Swagger UI (FastAPI default). |

### `POST /investigate` response shape

```jsonc
{
  "filename": "sample.csv",
  "validation": { "valid": true, "total_rows": 52, "total_columns": 18, "missing_columns": [], "duplicate_rows": 0, "missing_values": {} },
  "top_transaction": { "row_index": 51, "sender_entity_id": "...", "receiver_entity_id": "...", "amount_paid": 5021.92, "final_score": 0.59, "risk_level": "High" },
  "rules": { "triggered_rules": ["Amount Spike", "Cross Bank Transfer"], "risk_score": 20, "explanations": [ "..." ] },
  "ml": { "prediction": 1, "probability": 0.87, "confidence": 0.87, "shap_values": { "...": 0.0 }, "top_positive_features": [ { "feature": "...", "value": 0.0, "impact": 0.0 } ], "top_negative_features": [ "..." ] },
  "risk": { "final_score": 0.59, "risk_level": "High", "decision": "Investigate", "reasons": [ "..." ] },
  "graph": { "node_count": 94, "edge_count": 52, "num_components": 50, "hub_accounts": [ "..." ], "mule_accounts": [], "cycles": [ [ "..." ] ], "top_pagerank": { "...": 0.0 } },
  "transactions": [ { "row_index": 0, "...": "...", "final_score": 0.09, "risk_level": "Low" } ],
  "investigation_report": "Dataset validated with 52 rows across 18 columns... The rule engine triggered 2 rule(s)...",
  "recommendation": "Investigate"
}
```

## 12. Folder Structure

```
aml_fraud_detection/
├── analytics/                  # This contribution — the analytics SDK (own git repo, gitignored at root)
│   ├── config.py                #   Paths, constants, random seed
│   ├── interfaces.py            #   Shared dataclasses (RuleResult, RiskAssessment, ...)
│   ├── data/                    #   Loader, Validator, Preprocessor, schema constants
│   ├── eda/                     #   Exploratory analysis + plots
│   ├── features/                #   FeatureEngineer
│   ├── rules/                   #   RuleEngine + rule definitions
│   ├── ml/                      #   AMLInference (XGBoost + SHAP), schemas
│   ├── fusion/                  #   RiskFusion, RiskAssessment schema
│   └── graph/                   #   GraphAnalyzer, GraphMetrics schema
├── dataset/                     # Sample transaction CSVs
├── models/                      # Trained joblib pipeline (xgboost_model.joblib) + feature_names.json
├── outputs/plots/                # EDA plot outputs
├── test.py                      # End-to-end analytics pipeline demo (no web framework)
├── AMLens/                      # Teammate's LangGraph agent (separate git repo, locked)
│   └── backend/
│       ├── app/
│       │   ├── main.py           #   FastAPI app (+ new /ui static mount)
│       │   ├── api/routes.py     #   Routes (+ new POST /investigate)
│       │   ├── services/         #   NEW — investigation_service.py
│       │   ├── schemas/          #   + NEW evidence.py (tool_io.py untouched)
│       │   ├── agents/           #   + NEW evidence_explainer.py (explainer.py untouched)
│       │   ├── tools/             #   Dummy analytics + tool registry (untouched)
│       │   └── config/, core/     #   Settings, logging, exceptions (untouched)
│       ├── static/index.html     #   NEW — minimal investigation frontend
│       └── requirements.txt      #   + analytics deps appended
└── README.md                    # This file
```

## 13. Running the Project

### Analytics pipeline only (no web server)

```bash
# From the repo root — uses the same Python environment as everything below
python test.py
```

Runs Loader → Validator → Preprocessor → FeatureEngineer → RuleEngine → AMLInference → RiskFusion → GraphAnalyzer on `dataset/sample.csv` and prints each stage's output.

### Full system (API + frontend)

This project verified everything in a single Python 3.12 environment that already has `fastapi`, `pandas`, `numpy`, `scikit-learn`, `xgboost`, `shap`, `networkx`, `joblib`, `langgraph`, `langchain-core`, `google-genai`, and `pydantic-settings` installed (AMLens's own README describes a separate Python 3.13 venv, which was never actually created — using one shared environment is simpler and was the tested path here).

```bash
# 1. Install any remaining AMLens dependencies into your environment
pip install -r AMLens/backend/requirements.txt

# 2. Add your Gemini API key (a placeholder is scaffolded so the app boots
#    without one, but you'll get deterministic fallback narratives instead
#    of live LLM ones until you add a real key)
#    Edit: AMLens/backend/.env  ->  GEMINI_API_KEY=<your key>

# 3. Run the API server
cd AMLens/backend
uvicorn app.main:app --reload --port 8000

# 4. Open the frontend
#    http://localhost:8000/ui/

# 5. Or call the API directly
curl -X POST http://localhost:8000/investigate \
  -F "file=@../../dataset/sample.csv"
```

## 14. Example Workflow

1. A compliance analyst uploads `dataset/sample.csv` via `/ui/` or `POST /investigate`.
2. The pipeline validates the file (52 rows, 18 columns, no missing values), engineers features, and scores all 52 transactions with both the rule engine and the ML model.
3. Transaction #51 comes back highest-risk: rules trigger "Amount Spike" and "Cross-Bank Transfer" (score 20); the ML model estimates an 87% fraud probability, driven mainly by unusual receiving-currency and amount-deviation features (per SHAP); fusion combines these into a final score of 0.59 (**High** risk, decision: **Investigate**).
4. `GraphAnalyzer` reports the dataset's broader network: 94 accounts, 1 hub account, no confirmed mule accounts, and 8 short self-referential cycles.
5. The LLM agent (or its deterministic fallback) turns all of this into a short investigation narrative, and the frontend renders validation summary, rule findings, ML/SHAP tables, risk card, graph metrics, the full per-transaction table, and the final report — ready for a human reviewer to act on.

## 15. Future Scope

- Wire graph metrics and real rule/ML evidence into the natural-language `/query` LangGraph path (currently still dummy-data-driven), once its `filters`-based contract is extended to reference an uploaded dataset.
- Richer mule-account detection (temporal pass-through window, not just aggregate in/out balance).
- Batch/async scoring for datasets larger than the current 500-row safety cap.
- Persist investigation results (currently stateless, per-request).
- Replace the placeholder Gemini key / add retry-with-backoff for the LLM call.
- Production-quality frontend (current one is intentionally minimal/temporary).
