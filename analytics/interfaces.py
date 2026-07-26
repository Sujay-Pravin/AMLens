from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd


@dataclass
class EDAResult:
    """
    Output of the Exploratory Data Analysis module.
    """

    summary: Dict[str, Any]
    missing_values: Dict[str, int]
    class_distribution: Dict[Any, int]
    metrics: Dict[str, Any] = field(default_factory=dict)
    plots: List[str] = field(default_factory=list)


@dataclass
class FeatureResult:
    """
    Output of the Feature Engineering module.
    """

    dataframe: pd.DataFrame
    feature_names: List[str]


@dataclass
class RuleResult:
    """
   Output of the Rule Engine.
    """

    triggered_rules: List[str]
    risk_score: int
    explanations: List[str]


@dataclass
class MLResult:
    """
    Output of the ML inference pipeline.
    """

    prediction: int
    probability: float
    feature_importance: Optional[Dict[str, float]] = None


@dataclass
class RiskAssessment:
    """
    Final risk assessment combining rules and ML.
    """

    final_score: float
    risk_level: str
    decision: str
    reasons: List[str]