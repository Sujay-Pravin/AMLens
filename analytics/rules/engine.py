from typing import List

import pandas as pd

from analytics.interfaces import RuleResult
from .rules import RULES


class RuleEngine:
    """
    Evaluates AML rules against engineered transactions.
    """

    @staticmethod
    def evaluate_transaction(row: pd.Series) -> RuleResult:

        total_score = 0
        triggered = []
        explanations = []

        for rule in RULES:

            if rule.condition(row):

                total_score += rule.risk_points

                triggered.append(rule.name)
                explanations.append(rule.description)

        return RuleResult(
            triggered_rules=triggered,
            risk_score=total_score,
            explanations=explanations,
        )

    @staticmethod
    def evaluate_dataframe(df: pd.DataFrame) -> List[RuleResult]:

        return [
            RuleEngine.evaluate_transaction(row)
            for _, row in df.iterrows()
        ]