"""
LangGraph Workflow Orchestration — Phase 7.

This module stitches together the intent parser, planner, tool manager,
explainer, and recommender into a single directed graph.

Data flows through the graph via the AgentState dict.
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from langgraph.graph import StateGraph, END

from app.agents.state import AgentStateDict, dict_to_state, state_to_dict
from app.agents.intent_parser import parse_intent
from app.agents.planner import plan
from app.agents.filters import apply_filters
from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Bootstrap: make the `analytics` package (AMLens/) importable, same as
# investigation_service.py. Needed here because node_execute calls the
# analytics engines directly, conditionally, per the planner's output.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from analytics.eda.analyzer import EDAAnalyzer
from analytics.rules.engine import RuleEngine
from analytics.ml.inference import AMLInference
from analytics.fusion.engine import RiskFusion
from analytics.graph.engine import GraphAnalyzer

MAX_ROWS = 500
TOP_N = 5


@lru_cache(maxsize=1)
def _get_ml_engine() -> AMLInference:
    """Load the model + build the SHAP explainer once and reuse across requests."""
    return AMLInference()


# ---------------------------------------------------------------------------
# Node Functions
# ---------------------------------------------------------------------------

def node_intent(state: AgentStateDict) -> AgentStateDict:
    """Node 1: Extract intent and entities from the raw query."""
    query = state.get("user_query", "")
    logger.info(f"[Node: intent] Processing query: {query}")

    parsed = parse_intent(query)

    return {
        "parsed_intent": {k: v for k, v in parsed.items() if k not in ("_entities", "filters")},
        "entities": parsed.get("_entities", {}),
        "filters": parsed.get("filters", {}),
        "trace": state.get("trace", []) + ["intent_parsed"]
    }


def node_plan(state: AgentStateDict) -> AgentStateDict:
    """Node 2: Determine which analytics tools to run."""
    parsed_intent = state.get("parsed_intent", {})
    logger.info(f"[Node: plan] Planning based on intent: {parsed_intent.get('intent')}")

    execution_plan = plan(parsed_intent)

    return {
        "execution_plan": execution_plan,
        "trace": state.get("trace", []) + ["plan_created"]
    }


def _deterministic_transaction_explanation(rule_result, ml_result, risk) -> str:
    """One-line, no-LLM explanation for a single transaction (used for top-N)."""
    parts = []
    if rule_result.triggered_rules:
        parts.append(f"Triggered {', '.join(rule_result.triggered_rules)}")
    else:
        parts.append("No rules triggered")
    top_features = [fc.feature for fc in ml_result.top_positive_features[:3]]
    parts.append(f"ML fraud probability {ml_result.probability:.1%}")
    if top_features:
        parts.append(f"top drivers: {', '.join(top_features)}")
    parts.append(f"final risk {risk.final_score:.2f} ({risk.risk_level})")
    return "; ".join(parts) + "."


def node_execute(state: AgentStateDict) -> AgentStateDict:
    """Node 3: Execute ONLY the analytics tools selected by the planner.

    Validation and feature engineering already ran once upstream in
    investigation_service.run_investigation() (they're prerequisites every
    plan needs, not one of the gated tools). This node filters the
    engineered dataframe by the parsed entities, then conditionally runs
    EDA, the rule engine, ML inference, risk fusion, and graph analysis —
    strictly according to `state["execution_plan"]`.
    """
    errors = state.get("errors", []).copy()
    plan_list = state.get("execution_plan", [])
    df = state.get("features_df")

    execution_trace = {
        "validation": state.get("validation") is not None,
        "eda": False,
        "rules": False,
        "ml": False,
        "fusion": False,
        "graph": False,
    }

    result: dict[str, Any] = {}

    if df is None:
        errors.append("No features_df present in state — cannot execute analytics tools.")
        return {
            "errors": errors,
            "execution_trace": execution_trace,
            "trace": state.get("trace", []) + ["tools_executed"],
        }

    working_df = apply_filters(df, state.get("filters", {}))
    if len(working_df) == 0:
        errors.append("No transactions matched the requested filters.")
        working_df = df

    subset = working_df.iloc[:MAX_ROWS]

    if "run_eda" in plan_list:
        logger.info("[Node: execute] Running EDA.")
        result["eda_result"] = EDAAnalyzer.analyze(subset)
        execution_trace["eda"] = True

    rule_results: list = []
    ml_results: list = []

    if "detect_rules" in plan_list:
        logger.info(f"[Node: execute] Running rule engine on {len(subset)} row(s).")
        rule_results = [RuleEngine.evaluate_transaction(subset.iloc[i]) for i in range(len(subset))]
        execution_trace["rules"] = True

    if "detect_anomalies" in plan_list:
        logger.info(f"[Node: execute] Running ML inference on {len(subset)} row(s).")
        ml_engine = _get_ml_engine()
        ml_results = [ml_engine.predict(subset.iloc[[i]]) for i in range(len(subset))]
        execution_trace["ml"] = True

    if "calculate_risk" in plan_list and rule_results and ml_results:
        logger.info("[Node: execute] Fusing rule + ML risk signals.")
        evaluated = [
            (subset.index[i], subset.iloc[i], rule_results[i], ml_results[i],
             RiskFusion.fuse(rule_results[i], ml_results[i]))
            for i in range(len(subset))
        ]
        execution_trace["fusion"] = True

        evaluated.sort(key=lambda e: e[4].final_score, reverse=True)
        top = evaluated[:TOP_N]
        result["evaluated_transactions"] = [
            (index, row, rule_result, ml_result, risk, _deterministic_transaction_explanation(rule_result, ml_result, risk))
            for index, row, rule_result, ml_result, risk in top
        ]

        best_index, best_row, best_rule, best_ml, best_risk = evaluated[0]
        result["rule_result"] = best_rule
        result["ml_result"] = best_ml
        result["risk_assessment"] = best_risk

    if "analyze_graph" in plan_list:
        logger.info("[Node: execute] Running graph analysis.")
        result["graph_metrics"] = GraphAnalyzer.analyze(working_df)
        execution_trace["graph"] = True

    logger.info(f"[Node: execute] Execution trace: {execution_trace}")

    result["errors"] = errors
    result["execution_trace"] = execution_trace
    result["trace"] = state.get("trace", []) + ["tools_executed"]
    return result


def node_explain(state: AgentStateDict) -> AgentStateDict:
    """Node 4: Generate a compliance narrative explaining the real evidence."""
    from app.agents.evidence_explainer import generate_investigation_report

    logger.info("[Node: explain] Generating investigation narrative via LLM")

    explanation = generate_investigation_report(
        state.get("validation"),
        state.get("evaluated_transactions") or [],
        state.get("eda_result"),
        state.get("graph_metrics"),
        state.get("risk_assessment"),
        state.get("execution_trace", {}),
        state.get("user_query", ""),
    )

    return {
        "explanation": explanation,
        "trace": state.get("trace", []) + ["explanation_generated"]
    }


def node_recommend(state: AgentStateDict) -> AgentStateDict:
    """Node 5: Surface the final recommendation from the fused risk assessment."""
    from app.agents.recommender import recommend

    logger.info("[Node: recommend] Generating recommendation")

    recommendation = recommend(state)

    return {
        "recommendation": recommendation,
        "trace": state.get("trace", []) + ["recommendation_generated"]
    }


# ---------------------------------------------------------------------------
# Graph Definition
# ---------------------------------------------------------------------------

logger.info("Building LangGraph workflow...")

builder = StateGraph(AgentStateDict)

# Add all nodes
builder.add_node("intent", node_intent)
builder.add_node("plan", node_plan)
builder.add_node("execute", node_execute)
builder.add_node("explain", node_explain)
builder.add_node("recommend", node_recommend)

# Wire the edges
builder.set_entry_point("intent")
builder.add_edge("intent", "plan")
builder.add_edge("plan", "execute")
builder.add_edge("execute", "explain")
builder.add_edge("explain", "recommend")
builder.add_edge("recommend", END)

# Compile into a runnable application
workflow = builder.compile()

logger.info("LangGraph workflow compiled successfully.")
