"""
LangGraph Workflow Orchestration — Phase 7.

This module stitches together the intent parser, planner, tool manager, 
explainer, and recommender into a single directed graph.

Data flows through the graph via the AgentState dict.
"""

from typing import Any

from langgraph.graph import StateGraph, END

from app.agents.state import AgentStateDict, dict_to_state, state_to_dict
from app.agents.intent_parser import parse_intent
from app.agents.planner import plan
from app.core.logging import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Node Functions
# ---------------------------------------------------------------------------

def node_intent(state: AgentStateDict) -> AgentStateDict:
    """Node 1: Extract intent and entities from the raw query."""
    query = state.get("user_query", "")
    logger.info(f"[Node: intent] Processing query: {query}")
    
    parsed = parse_intent(query)
    
    return {
        "parsed_intent": {k: v for k, v in parsed.items() if k != "_entities"},
        "entities": parsed.get("_entities", {}),
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


def node_execute(state: AgentStateDict) -> AgentStateDict:
    """Node 3: Confirm the real analytics evidence for this state is present.

    Analytics (validation, rule engine, ML inference, risk fusion, graph
    analytics) has already run exactly once, upstream, in
    investigation_service.run_investigation() — this node does not call any
    analytics tool itself. It exists so the graph's shape (intent → plan →
    execute → explain → recommend) is preserved, and so downstream nodes can
    rely on evidence having been validated before they run.
    """
    errors = state.get("errors", []).copy()

    required = ("validation", "rule_result", "ml_result", "risk_assessment", "graph_metrics")
    missing = [name for name in required if state.get(name) is None]
    if missing:
        errors.append(f"Missing real analytics evidence for: {', '.join(missing)}")

    logger.info(
        "[Node: execute] Real analytics evidence present."
        if not missing else f"[Node: execute] Missing evidence: {missing}"
    )

    return {
        "errors": errors,
        "trace": state.get("trace", []) + ["tools_executed"]
    }


def node_explain(state: AgentStateDict) -> AgentStateDict:
    """Node 4: Generate a compliance narrative explaining the real evidence."""
    from app.agents.evidence_explainer import generate_investigation_report

    logger.info("[Node: explain] Generating investigation narrative via LLM")

    explanation = generate_investigation_report(
        state.get("validation"),
        state.get("rule_result"),
        state.get("ml_result"),
        state.get("risk_assessment"),
        state.get("graph_metrics"),
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
