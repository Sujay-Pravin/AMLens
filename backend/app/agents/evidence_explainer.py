"""
Evidence Explainer — narrates real analytics pipeline evidence.

Parallel to app/agents/explainer.py (which narrates the dummy-analytics
/query results). This module explains ALREADY-COMPUTED evidence from the
real analytics pipeline (ValidationReport, RuleResult, MLResult,
RiskAssessment, GraphMetrics) for the POST /investigate endpoint. The LLM
is instructed to explain the evidence, not recompute fraud detection.
"""

from google import genai

from app.config.settings import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

client = genai.Client(api_key=settings.gemini_api_key)

PROMPT_TEMPLATE = """You are a senior AML (Anti-Money Laundering) compliance analyst.
You are given evidence that has ALREADY been computed by an automated analytics
pipeline (data validation, rule engine, ML model with SHAP explainability, a
fused risk score, and transaction network graph metrics) for one transaction
flagged as the highest risk in an uploaded dataset.

Write a concise, professional 4-6 sentence investigation narrative explaining
WHY this transaction is risky, grounded strictly in the evidence below.
Do NOT invent numbers or recompute a risk score — only explain what the
evidence already shows. Do NOT output JSON. Write in plain, professional
English suitable for a compliance case file.

Dataset Validation:
- Rows: {total_rows}, Columns: {total_columns}
- Duplicate rows removed: {duplicate_rows}
- Missing columns: {missing_columns}

Rule Engine Findings:
- Triggered rules: {triggered_rules}
- Rule risk score: {rule_score}
- Explanations: {rule_explanations}

ML Model Prediction:
- Fraud probability: {ml_probability:.4f}
- Prediction label: {ml_prediction}
- Top features increasing risk: {ml_top_positive}
- Top features decreasing risk: {ml_top_negative}

Fused Risk Assessment:
- Final score: {final_score:.4f}
- Risk level: {risk_level}
- Decision: {decision}
- Reasons: {reasons}

Transaction Network Graph:
- Accounts: {node_count}, Transfers: {edge_count}, Connected clusters: {num_components}
- Hub accounts (unusually high connectivity): {hub_accounts}
- Suspected mule accounts (pass-through in/out patterns): {mule_accounts}
- Cycles detected (possible round-tripping): {cycle_count}
"""


def _fallback_report(validation, rule_result, ml_result, risk, graph_metrics) -> str:
    """Deterministic narrative used when the LLM call fails (e.g. no API key)."""

    parts = [
        f"Dataset validated with {validation.total_rows} rows across "
        f"{validation.total_columns} columns ({validation.duplicate_rows} "
        "duplicate rows removed).",
    ]

    if rule_result.triggered_rules:
        parts.append(
            "The rule engine triggered "
            f"{len(rule_result.triggered_rules)} rule(s) "
            f"({', '.join(rule_result.triggered_rules)}), contributing a rule "
            f"risk score of {rule_result.risk_score}."
        )
    else:
        parts.append("The rule engine triggered no rules for this transaction.")

    parts.append(
        f"The ML model estimated a fraud probability of "
        f"{ml_result.probability:.2%}, driven primarily by "
        f"{', '.join(f.feature for f in ml_result.top_positive_features[:3]) or 'no dominant features'}."
    )

    parts.append(
        f"Combining both signals, the fused risk assessment scored this "
        f"transaction at {risk.final_score:.2f} ({risk.risk_level} risk), "
        f"with a recommended action of: {risk.decision}."
    )

    if graph_metrics.hub_accounts or graph_metrics.mule_accounts:
        parts.append(
            "Network analysis flagged "
            f"{len(graph_metrics.hub_accounts)} hub account(s) and "
            f"{len(graph_metrics.mule_accounts)} suspected mule account(s) "
            "in the surrounding transaction graph."
        )

    return " ".join(parts)


def generate_investigation_report(
    validation,
    rule_result,
    ml_result,
    risk,
    graph_metrics,
) -> str:
    """Generate a natural-language investigation narrative from real evidence."""

    logger.info("[Agent: EvidenceExplainer] Generating investigation narrative.")

    prompt = PROMPT_TEMPLATE.format(
        total_rows=validation.total_rows,
        total_columns=validation.total_columns,
        duplicate_rows=validation.duplicate_rows,
        missing_columns=validation.missing_columns or "none",
        triggered_rules=rule_result.triggered_rules or "none",
        rule_score=rule_result.risk_score,
        rule_explanations=rule_result.explanations or "none",
        ml_probability=ml_result.probability,
        ml_prediction=ml_result.prediction,
        ml_top_positive=[f.feature for f in ml_result.top_positive_features] or "none",
        ml_top_negative=[f.feature for f in ml_result.top_negative_features] or "none",
        final_score=risk.final_score,
        risk_level=risk.risk_level,
        decision=risk.decision,
        reasons=risk.reasons or "none",
        node_count=graph_metrics.node_count,
        edge_count=graph_metrics.edge_count,
        num_components=graph_metrics.num_components,
        hub_accounts=graph_metrics.hub_accounts or "none",
        mule_accounts=graph_metrics.mule_accounts or "none",
        cycle_count=len(graph_metrics.cycles),
    )

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )

        if not response.text:
            raise ValueError("Response text was empty (possible generation error).")

        return response.text.strip()

    except Exception as e:
        logger.error(
            f"Investigation narrative generation failed: {type(e).__name__}: {e}"
        )
        return _fallback_report(validation, rule_result, ml_result, risk, graph_metrics)
