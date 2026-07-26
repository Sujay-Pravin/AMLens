"""
Investigation Service — orchestrates the real analytics pipeline, then hands
the resulting evidence to the LangGraph agent for reasoning, for the
POST /investigate endpoint.

It imports the `analytics` package directly from the parent repo (a
separate, locked pipeline), runs it exactly once per request, and converts
its dataclass outputs into the Pydantic response models in
app/schemas/evidence.py. The LangGraph workflow (app/agents/workflow.py)
then reasons over that evidence to produce the investigation narrative and
recommendation — it does not recompute fraud detection itself.
"""

from __future__ import annotations

import dataclasses
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Bootstrap: make the `analytics` package (repo root, two levels above
# AMLens/) importable. AMLens is a separately-rooted nested repo, so it is
# not on sys.path by default.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[3]
if not (_REPO_ROOT / "analytics").exists():
    raise RuntimeError(
        f"Expected the analytics package at {_REPO_ROOT / 'analytics'}, "
        "but it was not found. Refresh your directory mapping."
    )
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from analytics.data.validator import DataValidator
from analytics.data.preprocess import DataPreprocessor
from analytics.features.engineer import FeatureEngineer
from analytics.rules.engine import RuleEngine
from analytics.ml.inference import AMLInference
from analytics.fusion.engine import RiskFusion
from analytics.graph.engine import GraphAnalyzer

from app.agents.workflow import workflow
from app.core.logging import get_logger
from app.schemas.evidence import (
    ValidationReportOut,
    RuleResultOut,
    MLResultOut,
    RiskAssessmentOut,
    GraphMetricsOut,
    TransactionRiskSummary,
    InvestigationResponse,
)

logger = get_logger(__name__)

MAX_ROWS = 500


@lru_cache(maxsize=1)
def _get_ml_engine() -> AMLInference:
    """Load the model + build the SHAP explainer once and reuse across requests."""
    return AMLInference()


def _validation_out(validation) -> ValidationReportOut:
    data = dataclasses.asdict(validation)
    data["missing_values"] = {k: int(v) for k, v in data["missing_values"].items()}
    return ValidationReportOut(**data)


def _rule_out(rule_result) -> RuleResultOut:
    return RuleResultOut(**dataclasses.asdict(rule_result))


def _ml_out(ml_result) -> MLResultOut:
    return MLResultOut(**dataclasses.asdict(ml_result))


def _risk_out(risk) -> RiskAssessmentOut:
    return RiskAssessmentOut(**dataclasses.asdict(risk))


def _graph_out(graph_metrics) -> GraphMetricsOut:
    top_pagerank = dict(
        sorted(graph_metrics.pagerank.items(), key=lambda kv: kv[1], reverse=True)[:10]
    )
    return GraphMetricsOut(
        node_count=graph_metrics.node_count,
        edge_count=graph_metrics.edge_count,
        num_components=graph_metrics.num_components,
        hub_accounts=graph_metrics.hub_accounts,
        mule_accounts=graph_metrics.mule_accounts,
        cycles=graph_metrics.cycles,
        top_pagerank=top_pagerank,
    )


def _transaction_summary(index, row, risk) -> TransactionRiskSummary:
    return TransactionRiskSummary(
        row_index=int(index),
        sender_entity_id=str(row["sender_entity_id"]),
        receiver_entity_id=str(row["receiver_entity_id"]),
        amount_paid=float(row["amount_paid"]),
        final_score=risk.final_score,
        risk_level=risk.risk_level,
    )


def run_investigation(
    df: pd.DataFrame, filename: str, max_rows: int = MAX_ROWS
) -> InvestigationResponse:
    """Run the full analytics pipeline on an uploaded transaction CSV and
    return the evidence + LLM-generated investigation narrative for the
    single highest-risk transaction, alongside dataset-wide graph metrics.
    """

    validation = DataValidator.validate(df)
    if not validation.valid:
        raise ValueError(
            f"Uploaded CSV is missing required columns: {validation.missing_columns}"
        )

    clean = DataPreprocessor.preprocess(df)
    feature_result = FeatureEngineer.engineer(clean)
    features = feature_result.dataframe

    if len(features) == 0:
        raise ValueError("Uploaded CSV contains no rows after preprocessing.")

    subset = features.iloc[:max_rows]
    ml_engine = _get_ml_engine()

    logger.info(f"[Investigation] Scoring {len(subset)} transaction(s) from '{filename}'.")

    evaluated = []
    for i in range(len(subset)):
        row = subset.iloc[i]
        rule_result = RuleEngine.evaluate_transaction(row)
        ml_result = ml_engine.predict(subset.iloc[[i]])
        risk = RiskFusion.fuse(rule_result, ml_result)
        evaluated.append((subset.index[i], row, rule_result, ml_result, risk))

    best_index, best_row, best_rule, best_ml, best_risk = max(
        evaluated, key=lambda e: e[4].final_score
    )

    graph_metrics = GraphAnalyzer.analyze(features)

    initial_state = {
        "user_query": f"Investigate the highest-risk transaction in '{filename}'.",
        "filters": {},
        "validation": validation,
        "rule_result": best_rule,
        "ml_result": best_ml,
        "risk_assessment": best_risk,
        "graph_metrics": graph_metrics,
    }
    final_state = workflow.invoke(initial_state)
    if final_state.get("errors"):
        logger.warning(f"[Investigation] Agent reported errors: {final_state['errors']}")

    narrative = final_state.get("explanation") or ""
    recommendation = final_state.get("recommendation") or best_risk.decision

    transactions = [
        _transaction_summary(index, row, risk) for index, row, _, _, risk in evaluated
    ]

    return InvestigationResponse(
        filename=filename,
        validation=_validation_out(validation),
        top_transaction=_transaction_summary(best_index, best_row, best_risk),
        rules=_rule_out(best_rule),
        ml=_ml_out(best_ml),
        risk=_risk_out(best_risk),
        graph=_graph_out(graph_metrics),
        transactions=transactions,
        investigation_report=narrative,
        recommendation=recommendation,
    )
