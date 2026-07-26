from analytics.interfaces import RuleResult
from analytics.ml.schemas import MLResult
from analytics.rules.rules import RULES

from .schemas import RiskAssessment

MAX_RULE_SCORE = sum(rule.risk_points for rule in RULES)

ML_WEIGHT = 0.6
RULE_WEIGHT = 0.4

RISK_LEVEL_THRESHOLDS = (
    (0.25, "Low"),
    (0.5, "Medium"),
    (0.75, "High"),
)
DEFAULT_RISK_LEVEL = "Critical"

DECISIONS = {
    "Low": "Clear",
    "Medium": "Monitor",
    "High": "Investigate",
    "Critical": "Escalate / File SAR",
}


class RiskFusion:
    """
    Fuses rule-based and ML-based risk signals into a single assessment.
    """

    @staticmethod
    def fuse(rule_result: RuleResult, ml_result: MLResult) -> RiskAssessment:

        normalized_rule = 0.0
        if MAX_RULE_SCORE > 0:
            normalized_rule = min(
                max(rule_result.risk_score / MAX_RULE_SCORE, 0.0),
                1.0,
            )

        final_score = (
            ML_WEIGHT * ml_result.probability
            + RULE_WEIGHT * normalized_rule
        )

        risk_level = DEFAULT_RISK_LEVEL
        for threshold, level in RISK_LEVEL_THRESHOLDS:
            if final_score < threshold:
                risk_level = level
                break

        decision = DECISIONS[risk_level]

        reasons = list(rule_result.explanations)

        top_features = [
            fc.feature for fc in ml_result.top_positive_features
        ]
        if top_features:
            reasons.append(
                "ML model flagged elevated risk driven by: "
                + ", ".join(top_features)
            )

        return RiskAssessment(
            final_score=final_score,
            risk_level=risk_level,
            decision=decision,
            reasons=reasons,
        )
