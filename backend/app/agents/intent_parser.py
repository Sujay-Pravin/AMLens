"""
Intent Parsing Agent — Phase 4.

Uses a hybrid approach:
1. Fast rule-based pass (regex, dateparser) for high-precision fields (dates, amounts, IDs).
2. LLM pass (HuggingFace) for semantic fields (intent label, AML pattern, transaction type).
3. Merge results, preferring rule-based extractions for exact matches.

This approach is highly resilient for demos and degrades gracefully if the LLM fails.
"""

import json
import re
from typing import Any

import dateparser
from google import genai
from google.genai import types

from app.config.settings import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Initialize the Google GenAI client
client = genai.Client(api_key=settings.gemini_api_key)

PROMPT_TEMPLATE = """Extract AML query intent as strict JSON.
Fields to extract:
- intent: one of ["investigate", "summarize", "detect_pattern", "score_risk", "unknown"]
- aml_pattern: identified pattern (e.g., "structuring", "smurfing", "layering") or null
- transaction_type: e.g., "cash", "wire", "crypto", or null
- threshold_amount: numeric threshold mentioned (if any) or null

Return ONLY valid JSON. No prose, no markdown formatting blocks (e.g. ```json).

Query: {query}
"""

def extract_rule_based(query: str) -> dict[str, Any]:
    """Extract high-precision entities using regex and dateparser."""
    entities: dict[str, Any] = {}

    # 1. Date extraction
    date_val = dateparser.parse(query, settings={'STRICT_PARSING': False})
    if date_val:
        entities["date"] = date_val.isoformat()

    # 2. Customer IDs (e.g., CUST-1023, cust 4455)
    ids = re.findall(r"CUST[- ]?\d+", query, re.IGNORECASE)
    if ids:
        entities["customer_ids"] = [uid.upper().replace(" ", "-") for uid in ids]

    # 3. Amounts (e.g., $10,000, ₹50,000)
    amounts = re.findall(r"[\$\u20b9£€]\s?\d[\d,]*", query)
    if amounts:
        entities["amounts"] = amounts

    # 4. Country Codes (ISO 3166-1 alpha-2 heuristics)
    # Simple lookup for common demo countries
    countries = []
    query_upper = query.upper()
    if "UAE" in query_upper or "UNITED ARAB EMIRATES" in query_upper:
        countries.append("AE")
    if "SINGAPORE" in query_upper:
        countries.append("SG")
    if "INDIA" in query_upper:
        countries.append("IN")
    if "NIGERIA" in query_upper:
        countries.append("NG")
    
    # Exact word matches for alpha-2
    words = set(re.findall(r"\b[A-Z]{2}\b", query_upper))
    if "AE" in words and "AE" not in countries: countries.append("AE")
    if "SG" in words and "SG" not in countries: countries.append("SG")
    if "NG" in words and "NG" not in countries: countries.append("NG")
    # We skip "IN" for 2-letter exact match because "in" is a common English preposition.
    
    if countries:
        entities["country_codes"] = countries

    return entities


def extract_llm(query: str) -> dict[str, Any]:
    """Extract semantic intent using Google AI Studio."""
    prompt = PROMPT_TEMPLATE.format(query=query)
    
    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
        )
        
        if not response.text:
            logger.error(f"Response text was empty. Full response: {response}")
            raise ValueError("Response text was empty.")
            
        text = response.text.strip()
        
        # Clean up common LLM formatting issues
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
            
        return json.loads(text.strip())
        
    except json.JSONDecodeError as e:
        logger.error(f"LLM returned malformed JSON: {e} | Raw text: {text}")
        return {"intent": "unknown", "error": "json_decode_failed"}
    except Exception as e:
        logger.error(f"LLM request failed: {e}")
        return {"intent": "unknown", "error": str(e)}


def parse_intent(query: str) -> dict[str, Any]:
    """Primary entry point: merge rule-based and LLM extractions."""
    logger.info(f"Parsing intent for query: '{query}'")
    
    rules_out = extract_rule_based(query)
    llm_out = extract_llm(query)
    
    # Merge, keeping LLM's structure but injecting rule-based entities if found
    merged = {**llm_out}
    
    # Also attach the rule-based entities under a specific key for the state schema
    merged["_entities"] = rules_out
    
    logger.debug(f"Parsed intent result: {merged}")
    return merged
