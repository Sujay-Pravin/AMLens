from dataclasses import dataclass
from typing import Dict, List


@dataclass
class FeatureContribution:
    feature: str
    value: float
    impact: float


@dataclass
class MLResult:
    prediction: int
    probability: float
    confidence: float
    shap_values: Dict[str, float]
    top_positive_features: List[FeatureContribution]
    top_negative_features: List[FeatureContribution]