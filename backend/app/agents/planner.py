"""
Execution Planner Agent — Phase 5.

Takes the structured intent output from the Intent Parser and determines the exact
sequence of analytics tools to run.

This is deterministic and rule-based, ensuring that the system is predictable,
fast, and auditable.
"""

from typing import Any
from app.core.logging import get_logger

logger = get_logger(__name__)

# The definitive order of execution if multiple tools are selected.
# Tools must run in this order to satisfy data dependencies.
_EXECUTION_ORDER = [
    "run_eda",
    "generate_features",
    "detect_rules",
    "detect_anomalies",
    "calculate_risk",
    "analyze_graph",
]

def plan(parsed_intent: dict[str, Any]) -> list[str]:
    """Determine the optimal list of analytics tools to execute based on intent."""
    intent_type = parsed_intent.get("intent", "unknown")
    aml_pattern = parsed_intent.get("aml_pattern")

    logger.info(f"Planning execution for intent: '{intent_type}', pattern: '{aml_pattern}'")

    selected_tools = set()

    # 1. Customer lookup -> targeted scoring only, no EDA, no graph
    if intent_type == "customer_lookup":
        selected_tools.update(["detect_rules", "detect_anomalies", "calculate_risk"])
        ordered_plan = [tool for tool in _EXECUTION_ORDER if tool in selected_tools]
        logger.debug(f"Generated execution plan: {ordered_plan}")
        return ordered_plan

    # 2. Graph query -> network analysis only; rules optional, ML/fusion skipped
    if intent_type == "graph_query":
        selected_tools.add("analyze_graph")
        if aml_pattern:
            selected_tools.add("detect_rules")
        ordered_plan = [tool for tool in _EXECUTION_ORDER if tool in selected_tools]
        logger.debug(f"Generated execution plan: {ordered_plan}")
        return ordered_plan

    # 3. Investigate / Summarize -> Needs EDA + full network view
    if intent_type in ["investigate", "summarize", "unknown"]:
        selected_tools.add("run_eda")
        selected_tools.add("analyze_graph")

    # 4. Pattern detection -> Needs Features + Rules
    if intent_type == "detect_pattern" or aml_pattern:
        selected_tools.add("generate_features")
        selected_tools.add("detect_rules")

    # 5. Risk Scoring & Deep Investigations -> Needs Anomaly + Risk
    if intent_type in ["score_risk", "detect_pattern", "investigate"]:
        # calculate_risk usually depends on detect_rules and detect_anomalies
        selected_tools.add("detect_rules")
        selected_tools.add("detect_anomalies")
        selected_tools.add("calculate_risk")

    # 6. Fallback / Unknown
    if not selected_tools or intent_type == "unknown":
        selected_tools.update(["run_eda", "detect_rules", "detect_anomalies", "calculate_risk", "analyze_graph"])

    # 7. Sort the tools according to the master _EXECUTION_ORDER
    ordered_plan = [tool for tool in _EXECUTION_ORDER if tool in selected_tools]

    logger.debug(f"Generated execution plan: {ordered_plan}")
    return ordered_plan
