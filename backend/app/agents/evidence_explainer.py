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
pipeline, gated to only the tools relevant to the user's query (data
validation, and where applicable: exploratory data analysis, rule engine,
ML model with SHAP explainability, a fused risk score for the riskiest
transactions, and transaction network graph metrics).

Write a concise, professional investigation report (5-8 sentences) summarizing
the overall findings, referencing the highest-risk transactions, graph
findings, and EDA findings ONLY if that evidence is present below, and closing
with a recommendation. Do NOT invent numbers or recompute anything — only
explain what the evidence already shows. Do NOT output JSON. Write in plain,
professional English suitable for a compliance case file.

User query: {user_query}
Tools executed this run: {tools_executed}

Dataset Validation:
- Rows: {total_rows}, Columns: {total_columns}
- Duplicate rows removed: {duplicate_rows}
- Missing columns: {missing_columns}

{eda_section}
{transactions_section}
{graph_section}
"""


def _eda_section(eda_result) -> str:
    if eda_result is None:
        return "Exploratory Data Analysis: not run for this query.\n"
    return (
        "Exploratory Data Analysis:\n"
        f"- Dataset shape analyzed: {eda_result.summary.get('rows')} rows, "
        f"{eda_result.summary.get('columns')} columns\n"
        f"- Class distribution (is_laundering): {eda_result.class_distribution}\n"
        f"- Top sender banks: {list(eda_result.metrics.get('top_sender_banks', {}).keys())[:5]}\n"
    )


def _transactions_section(evaluated_transactions) -> str:
    if not evaluated_transactions:
        return "Highest-Risk Transactions: rule/ML scoring not run for this query.\n"
    lines = ["Highest-Risk Transactions (top {}):".format(len(evaluated_transactions))]
    for index, row, rule_result, ml_result, risk, explanation in evaluated_transactions:
        lines.append(
            f"- Row #{index}: final score {risk.final_score:.2f} ({risk.risk_level}). {explanation}"
        )
    return "\n".join(lines) + "\n"


def _graph_section(graph_metrics) -> str:
    if graph_metrics is None:
        return "Transaction Network Graph: not run for this query.\n"
    return (
        "Transaction Network Graph:\n"
        f"- Accounts: {graph_metrics.node_count}, Transfers: {graph_metrics.edge_count}, "
        f"Connected clusters: {graph_metrics.num_components}\n"
        f"- Hub accounts (unusually high connectivity): {graph_metrics.hub_accounts or 'none'}\n"
        f"- Suspected mule accounts (pass-through in/out patterns): {graph_metrics.mule_accounts or 'none'}\n"
        f"- Cycles detected (possible round-tripping): {len(graph_metrics.cycles)}\n"
    )


def _fallback_report(validation, evaluated_transactions, eda_result, graph_metrics, risk_assessment) -> str:
    """Deterministic narrative used when the LLM call fails (e.g. no API key)."""

    parts = [
        f"Dataset validated with {validation.total_rows} rows across "
        f"{validation.total_columns} columns ({validation.duplicate_rows} "
        "duplicate rows removed).",
    ]

    if evaluated_transactions:
        best = evaluated_transactions[0]
        best_risk = best[4]
        parts.append(
            f"{len(evaluated_transactions)} transaction(s) were scored; the "
            f"highest-risk transaction (row #{best[0]}) reached a final score of "
            f"{best_risk.final_score:.2f} ({best_risk.risk_level} risk). {best[5]}"
        )
    else:
        parts.append("Rule/ML risk scoring was not requested for this query.")

    if eda_result is not None:
        parts.append(
            "Exploratory analysis covered "
            f"{eda_result.summary.get('rows')} rows with class distribution "
            f"{eda_result.class_distribution}."
        )

    if graph_metrics is not None:
        parts.append(
            "Network analysis flagged "
            f"{len(graph_metrics.hub_accounts)} hub account(s) and "
            f"{len(graph_metrics.mule_accounts)} suspected mule account(s) "
            "in the surrounding transaction graph."
        )

    if risk_assessment is not None:
        parts.append(f"Recommended action: {risk_assessment.decision}.")

    return " ".join(parts)


def generate_investigation_report(
    validation,
    evaluated_transactions,
    eda_result,
    graph_metrics,
    risk_assessment,
    execution_trace,
    user_query="",
) -> str:
    """Generate a natural-language investigation narrative from real,
    plan-gated evidence. Exactly one LLM call per request, regardless of how
    many transactions are summarized."""

    logger.info("[Agent: EvidenceExplainer] Generating investigation narrative.")

    tools_executed = [name for name, ran in (execution_trace or {}).items() if ran]

    prompt = PROMPT_TEMPLATE.format(
        user_query=user_query or "(none provided)",
        tools_executed=tools_executed or "validation only",
        total_rows=validation.total_rows,
        total_columns=validation.total_columns,
        duplicate_rows=validation.duplicate_rows,
        missing_columns=validation.missing_columns or "none",
        eda_section=_eda_section(eda_result),
        transactions_section=_transactions_section(evaluated_transactions),
        graph_section=_graph_section(graph_metrics),
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
        return _fallback_report(validation, evaluated_transactions, eda_result, graph_metrics, risk_assessment)
