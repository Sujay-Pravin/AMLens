"""
Investigation Service — orchestrates the real analytics pipeline, then hands
the resulting evidence to the LangGraph agent for reasoning, for the
POST /investigate endpoint.

It imports the `analytics` package directly from the parent repo (a
separate, locked pipeline), runs validation + feature engineering exactly
once per request (the prerequisites every query needs), then hands the
engineered dataframe to the LangGraph workflow — which filters it by the
parsed query entities and conditionally runs the remaining analytics tools
(EDA, rule engine, ML inference, risk fusion, graph analytics) strictly
according to the planner's execution_plan. The LangGraph workflow
(app/agents/workflow.py) reasons over that evidence to produce the
investigation narrative and recommendation — it does not recompute fraud
detection itself.
"""

from __future__ import annotations

import dataclasses
import sys
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

from app.agents.workflow import workflow
from app.core.logging import get_logger
from app.schemas.evidence import (
    ValidationReportOut,
    RuleResultOut,
    MLResultOut,
    RiskAssessmentOut,
    GraphMetricsOut,
    EDASummaryOut,
    TransactionRiskSummary,
    TopTransactionOut,
    FeatureContributionOut,
    InvestigationResponse,
)

logger = get_logger(__name__)


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


def _eda_out(eda_result) -> EDASummaryOut:
    return EDASummaryOut(
        summary=eda_result.summary,
        missing_values={str(k): int(v) for k, v in eda_result.missing_values.items()},
        class_distribution={str(k): int(v) for k, v in eda_result.class_distribution.items()},
        metrics=eda_result.metrics,
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


def _top_transaction_out(index, row, rule_result, ml_result, risk, explanation) -> TopTransactionOut:
    return TopTransactionOut(
        row_index=int(index),
        sender_entity_id=str(row["sender_entity_id"]),
        receiver_entity_id=str(row["receiver_entity_id"]),
        amount_paid=float(row["amount_paid"]),
        risk_level=risk.risk_level,
        risk_score=risk.final_score,
        fraud_probability=ml_result.probability,
        triggered_rules=rule_result.triggered_rules,
        shap_top_contributors=[
            FeatureContributionOut(feature=fc.feature, value=fc.value, impact=fc.impact)
            for fc in ml_result.top_positive_features
        ],
        explanation=explanation,
    )


def run_investigation(
    df: pd.DataFrame, filename: str, query: str
) -> InvestigationResponse:
    """Run validation + feature engineering (always required), then invoke
    the query-driven LangGraph workflow, which filters the dataset by the
    parsed query entities and conditionally runs EDA/rules/ML/fusion/graph
    per the planner's execution_plan.
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

    logger.info(f"[Investigation] Query: '{query}' over '{filename}' ({len(features)} rows).")

    initial_state = {
        "user_query": query,
        "filters": {},
        "features_df": features,
        "validation": validation,
    }
    final_state = workflow.invoke(initial_state)
    if final_state.get("errors"):
        logger.warning(f"[Investigation] Agent reported errors: {final_state['errors']}")

    evaluated_transactions = final_state.get("evaluated_transactions") or []
    risk_assessment = final_state.get("risk_assessment")
    rule_result = final_state.get("rule_result")
    ml_result = final_state.get("ml_result")
    graph_metrics = final_state.get("graph_metrics")
    eda_result = final_state.get("eda_result")

    narrative = final_state.get("explanation") or ""
    recommendation = final_state.get("recommendation") or (
        risk_assessment.decision if risk_assessment else "No risk scoring performed for this query."
    )

    transactions = [
        _transaction_summary(index, row, risk)
        for index, row, _, _, risk, _ in evaluated_transactions
    ]
    top_transactions = [
        _top_transaction_out(index, row, rr, mr, risk, explanation)
        for index, row, rr, mr, risk, explanation in evaluated_transactions
    ]

    return InvestigationResponse(
        filename=filename,
        query=query,
        parsed_intent=final_state.get("parsed_intent") or {},
        filters_applied=final_state.get("filters") or {},
        execution_plan=final_state.get("execution_plan") or [],
        execution_trace=final_state.get("execution_trace") or {},
        validation=_validation_out(validation),
        eda=_eda_out(eda_result) if eda_result else None,
        top_transaction=transactions[0] if transactions else None,
        rules=_rule_out(rule_result) if rule_result else None,
        ml=_ml_out(ml_result) if ml_result else None,
        risk=_risk_out(risk_assessment) if risk_assessment else None,
        graph=_graph_out(graph_metrics) if graph_metrics else None,
        transactions=transactions,
        top_transactions=top_transactions,
        investigation_report=narrative,
        recommendation=recommendation,
    )
