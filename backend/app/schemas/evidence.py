"""
Pydantic response models for the real analytics investigation pipeline.

These mirror the dataclasses produced by the `analytics` package
(ValidationReport, RuleResult, MLResult, RiskAssessment, GraphMetrics) and
are used by the POST /investigate endpoint, which is the sole analytics
entry point for AMLens.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class ValidationReportOut(BaseModel):
    valid: bool
    total_rows: int
    total_columns: int
    missing_columns: List[str]
    duplicate_rows: int
    missing_values: dict[str, int]


class RuleResultOut(BaseModel):
    triggered_rules: List[str]
    risk_score: int
    explanations: List[str]


class FeatureContributionOut(BaseModel):
    feature: str
    value: float
    impact: float


class MLResultOut(BaseModel):
    prediction: int
    probability: float
    confidence: float
    shap_values: dict[str, float]
    top_positive_features: List[FeatureContributionOut]
    top_negative_features: List[FeatureContributionOut]


class RiskAssessmentOut(BaseModel):
    final_score: float
    risk_level: str
    decision: str
    reasons: List[str]


class GraphMetricsOut(BaseModel):
    node_count: int
    edge_count: int
    num_components: int
    hub_accounts: List[str]
    mule_accounts: List[str]
    cycles: List[List[str]]
    top_pagerank: dict[str, float] = Field(
        default_factory=dict,
        description="Top 10 accounts by PageRank score",
    )


class TransactionRiskSummary(BaseModel):
    row_index: int
    sender_entity_id: str
    receiver_entity_id: str
    amount_paid: float
    final_score: float
    risk_level: str


class InvestigationResponse(BaseModel):
    filename: str
    validation: ValidationReportOut
    top_transaction: TransactionRiskSummary
    rules: RuleResultOut
    ml: MLResultOut
    risk: RiskAssessmentOut
    graph: GraphMetricsOut
    transactions: List[TransactionRiskSummary]
    investigation_report: str
    recommendation: str
