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
from app.tools.tool_manager import call_tool
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
    """Node 3: Execute the planned analytics tools sequentially."""
    execution_plan = state.get("execution_plan", [])
    filters = state.get("filters", {})
    logger.info(f"[Node: execute] Running tools: {execution_plan}")
    
    tool_outputs = state.get("tool_outputs", {}).copy()
    errors = state.get("errors", []).copy()
    risk_results = state.get("risk_results")
    
    for tool_name in execution_plan:
        kwargs: dict[str, Any] = {"filters": filters}
        
        # calculate_risk has a special signature (requires outputs from previous tools)
        if tool_name == "calculate_risk":
            kwargs = {
                "rule_out": tool_outputs.get("detect_rules", {}),
                "ml_out": tool_outputs.get("detect_anomalies", {})
            }
            
        output = call_tool(tool_name, **kwargs)
        
        if "error" in output:
            errors.append(output["error"])
        else:
            if tool_name == "calculate_risk":
                risk_results = output
            else:
                tool_outputs[tool_name] = output

    return {
        "tool_outputs": tool_outputs,
        "risk_results": risk_results,
        "errors": errors,
        "trace": state.get("trace", []) + ["tools_executed"]
    }


def node_explain(state: AgentStateDict) -> AgentStateDict:
    """Node 4: Generate a compliance narrative explaining the results."""
    logger.info("[Node: explain] Generating explanation (stubbed for Phase 7)")
    
    # Phase 8: This will call app.agents.explainer
    # For now, we stub it so the graph compiles and runs.
    
    return {
        "explanation": "Explanation pending Phase 8 implementation.",
        "trace": state.get("trace", []) + ["explanation_generated"]
    }


def node_recommend(state: AgentStateDict) -> AgentStateDict:
    """Node 5: Generate a final recommendation based on the risk band."""
    logger.info("[Node: recommend] Generating recommendation (stubbed for Phase 7)")
    
    # Phase 9: This will call app.agents.recommender
    # For now, we stub it.
    
    return {
        "recommendation": "Recommendation pending Phase 9 implementation.",
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
