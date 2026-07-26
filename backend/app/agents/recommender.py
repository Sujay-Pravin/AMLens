"""
Recommendation Agent — Phase 9.

Surfaces the `decision` already computed by the real analytics pipeline's
RiskFusion stage (analytics.fusion.engine.RiskFusion) as the workflow's
final, actionable recommendation. The decision itself is not recomputed
here — this node only reads the fused risk assessment already present in
state.
"""

from app.agents.state import AgentStateDict
from app.core.logging import get_logger

logger = get_logger(__name__)

FALLBACK_RECOMMENDATION = "Unknown risk level — manual review required."


def recommend(state: AgentStateDict) -> str:
    """Surface the RiskAssessment.decision from state as the recommendation."""
    logger.info("[Agent: Recommender] Generating recommendation.")

    risk_assessment = state.get("risk_assessment")
    decision = getattr(risk_assessment, "decision", None)
    if not decision:
        logger.warning("No valid risk_assessment found in state. Falling back.")
        return FALLBACK_RECOMMENDATION

    logger.debug(f"Generated recommendation: {decision}")
    return decision
