"""
Explanation Agent — Phase 8.

Takes the raw JSON output from the analytics tools and translates it into a
plain-language, compliance-analyst-style narrative.
"""

import json
from google import genai
from google.genai import types

from app.config.settings import settings
from app.agents.state import AgentStateDict
from app.core.logging import get_logger

logger = get_logger(__name__)

# Initialize the Google GenAI client
client = genai.Client(api_key=settings.gemini_api_key)

PROMPT_TEMPLATE = """You are a senior AML (Anti-Money Laundering) compliance analyst.
Review the following analytics data and risk scores for a recent query.
Write a concise, professional 3-4 sentence summary explaining the findings.
Focus on the risk band, any critical anomalies, and rules triggered.
Do NOT output JSON. Write in plain, professional English.

Original Query: {query}
Intent: {intent}
Risk Results: {risk}
Tool Outputs:
{tools}
"""

def explain(state: AgentStateDict) -> str:
    """Generate a natural language explanation of the analytics results."""
    logger.info("[Agent: Explainer] Generating compliance narrative.")
    
    query = state.get("user_query", "Unknown query")
    intent = state.get("parsed_intent", {}).get("intent", "unknown")
    risk_results = state.get("risk_results") or "No risk calculated."
    
    # We serialize the tool outputs so the LLM can read them
    # Limit length to avoid massive prompts if data is huge
    tools_str = json.dumps(state.get("tool_outputs", {}), indent=2)[:3000]
    
    prompt = PROMPT_TEMPLATE.format(
        query=query,
        intent=intent,
        risk=risk_results,
        tools=tools_str
    )
    
    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )
        
        if not response.text:
            raise ValueError("Response text was empty (possible generation error).")
            
        text = response.text.strip()
        logger.debug(f"Generated explanation: {text}")
        return text
        
    except Exception as e:
        logger.error(f"Explanation generation failed: {type(e).__name__}: {e}")
        return "Explanation unavailable — review raw tool outputs above."
