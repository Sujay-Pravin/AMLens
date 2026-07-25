"""
Recommendation Agent — Phase 9.

Deterministic mapping that takes the computed risk band from the analytics tools
and translates it into a final, actionable recommendation.
"""

from app.agents.state import AgentStateDict
from app.core.logging import get_logger

logger = get_logger(__name__)

# Deterministic mapping for fast, auditable recommendations.
RECOMMENDATION_MAP = {
    "Critical": "Escalate immediately and file a report.",
    "High": "Escalate for manual review.",
    "Medium": "Flag for review within SLA.",
    "Low": "Continue monitoring, no action required.",
}

def recommend(state: AgentStateDict) -> str:
    """Generate an actionable recommendation based on the risk band."""
    logger.info("[Agent: Recommender] Generating recommendation.")
    
    risk_results = state.get("risk_results")
    if not risk_results or not isinstance(risk_results, dict):
        logger.warning("No valid risk_results found in state. Falling back.")
        return "Unknown risk level — manual review required."
        
    risk_band = risk_results.get("risk_band")
    
    recommendation = RECOMMENDATION_MAP.get(risk_band, "Unknown risk level — manual review required.")
    
    logger.debug(f"Generated recommendation: {recommendation}")
    return recommendation
