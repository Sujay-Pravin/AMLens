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
]

def plan(parsed_intent: dict[str, Any]) -> list[str]:
    """Determine the optimal list of analytics tools to execute based on intent."""
    intent_type = parsed_intent.get("intent", "unknown")
    aml_pattern = parsed_intent.get("aml_pattern")
    
    logger.info(f"Planning execution for intent: '{intent_type}', pattern: '{aml_pattern}'")
    
    selected_tools = set()
    
    # 1. Investigate / Summarize -> Needs EDA
    if intent_type in ["investigate", "summarize", "unknown"]:
        selected_tools.add("run_eda")
        
    # 2. Pattern detection -> Needs Features + Rules
    if intent_type == "detect_pattern" or aml_pattern:
        selected_tools.add("generate_features")
        selected_tools.add("detect_rules")
        
    # 3. Risk Scoring & Deep Investigations -> Needs Anomaly + Risk
    if intent_type in ["score_risk", "detect_pattern", "investigate"]:
        # calculate_risk usually depends on detect_rules and detect_anomalies
        selected_tools.add("detect_rules")
        selected_tools.add("detect_anomalies")
        selected_tools.add("calculate_risk")
        
    # 4. Fallback / Unknown
    if not selected_tools or intent_type == "unknown":
        selected_tools.update(["run_eda", "detect_rules", "calculate_risk"])

    # 5. Sort the tools according to the master _EXECUTION_ORDER
    ordered_plan = [tool for tool in _EXECUTION_ORDER if tool in selected_tools]
    
    logger.debug(f"Generated execution plan: {ordered_plan}")
    return ordered_plan
