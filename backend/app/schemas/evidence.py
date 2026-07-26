"""
Pydantic response models for the real analytics investigation pipeline.

These mirror the dataclasses produced by the `analytics` package
(ValidationReport, RuleResult, MLResult, RiskAssessment, GraphMetrics) and
are used by the POST /investigate endpoint, which is the sole analytics
entry point for AMLens.
"""

from __future__ import annotations

from typing import Any, List, Optional

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


class TopTransactionOut(BaseModel):
    row_index: int
    sender_entity_id: str
    receiver_entity_id: str
    amount_paid: float
    risk_level: str
    risk_score: float
    fraud_probability: float
    triggered_rules: List[str]
    shap_top_contributors: List[FeatureContributionOut]
    explanation: str


class EDASummaryOut(BaseModel):
    summary: dict[str, Any]
    missing_values: dict[str, int]
    class_distribution: dict[str, int]
    metrics: dict[str, Any]


class InvestigationResponse(BaseModel):
    filename: str
    query: str
    parsed_intent: dict[str, Any]
    filters_applied: dict[str, Any]
    execution_plan: List[str]
    execution_trace: dict[str, bool]
    validation: ValidationReportOut
    eda: Optional[EDASummaryOut] = None
    top_transaction: Optional[TransactionRiskSummary] = None
    rules: Optional[RuleResultOut] = None
    ml: Optional[MLResultOut] = None
    risk: Optional[RiskAssessmentOut] = None
    graph: Optional[GraphMetricsOut] = None
    transactions: List[TransactionRiskSummary] = Field(default_factory=list)
    top_transactions: List[TopTransactionOut] = Field(default_factory=list)
    investigation_report: str
    recommendation: str
