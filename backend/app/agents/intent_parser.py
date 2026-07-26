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
from datetime import datetime, timedelta
from typing import Any

import dateparser
from google import genai
from google.genai import types

from app.config.settings import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Initialize the Google GenAI client
client = genai.Client(api_key=settings.gemini_api_key)

PROMPT_TEMPLATE = """You are an intent classifier for an AML (anti-money-laundering) transaction \
investigation tool. Extract the query intent as strict JSON.

Fields to extract:
- intent: exactly one of ["investigate", "summarize", "detect_pattern", "score_risk", "customer_lookup", "graph_query", "unknown"]
- aml_pattern: the named typology if one is mentioned (e.g. "structuring", "smurfing", "layering", "mule accounts", "shell company", "round-tripping", "trade-based laundering") or null
- transaction_type: e.g. "cash", "wire", "crypto", "cheque", "card", or null
- threshold_amount: a single numeric amount threshold mentioned (if any) or null

Intent definitions (pick the SINGLE best match):
- "customer_lookup": asks about a specific, named customer/account id (e.g. "Is customer 4521 suspicious?", "Tell me about account 998").
- "graph_query": explicitly asks about the account NETWORK/GRAPH structure — hubs, mule accounts, clusters, cycles, or how accounts are CONNECTED to each other. Requires network/relationship language, not just the word "risky". (e.g. "Show the riskiest accounts in the network", "Which accounts form a hub?", "Find mule account clusters").
- "detect_pattern": asks to find/detect a specific named laundering typology or behavior pattern across transactions (e.g. "Find structuring patterns", "Detect smurfing", "Any layering activity?").
- "score_risk": asks for a risk score, rating, or ranking of transactions/customers WITHOUT naming a specific pattern or a single customer and WITHOUT asking about the account network (e.g. "What are the riskiest transfers?", "Score this data", "Rate the risk of these transactions", "Flag transactions above $5,000").
- "summarize": asks for an overview, summary, statistics, or "what happened" over the dataset, without asking for scoring or pattern detection (e.g. "Summarize wire transfers over $10,000", "What's the overall picture here?").
- "investigate": a general, open-ended request to investigate/review/examine the data that doesn't fit the more specific categories above (e.g. "Investigate this file", "Look into these transactions").
- "unknown": only if the query truly has no discernible AML analysis intent.

Disambiguation rules:
- The words "risky"/"riskiest" alone do NOT imply "graph_query" — only use "graph_query" when the query also references accounts being connected, networked, hubs, mules, or clusters.
- If a specific customer/account id number is mentioned, prefer "customer_lookup" over other intents.
- If a named typology/pattern is mentioned, prefer "detect_pattern" (or "graph_query" if it also asks about the network, e.g. "mule" clusters) over generic "investigate"/"score_risk".

Return ONLY valid JSON. No prose, no markdown formatting blocks (e.g. ```json).

Query: {query}
"""

_LOOKUP_KEYWORDS = ("customer", "account", "cust", "acc")
_GRAPH_KEYWORDS = (
    "graph", "network", "riskiest account", "hub", "mule", "cluster",
    "connected", "connections", "linked account", "link between",
    "relationship map", "cycle", "circular transfer",
)
_SCORE_KEYWORDS = (
    "score", "rate the risk", "how risky", "risk rating", "risk level",
    "rank", "flag transaction", "riskiest transfer", "riskiest transaction",
)
_SUMMARIZE_KEYWORDS = (
    "summarize", "summary", "overview", "overall", "what happened",
    "give me a report", "breakdown",
)
_DETECT_PATTERN_KEYWORDS = (
    "pattern", "structuring", "smurf", "layering", "shell compan",
    "round-trip", "round trip", "trade-based", "trade based",
    "funnel account", "cuckoo smurfing", "detect",
)
_INVESTIGATE_KEYWORDS = ("investigate", "look into", "check for", "examine", "review")

# Named AML typologies detected directly from the query text — used as an
# authoritative backstop when the LLM omits `aml_pattern` or is unavailable.
_AML_PATTERN_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bstructuring\b", "structuring"),
    (r"\bsmurf(?:ing)?\b", "smurfing"),
    (r"\blayering\b", "layering"),
    (r"\bmule\b|\bmule accounts?\b", "mule accounts"),
    (r"\bshell compan(?:y|ies)\b", "shell company"),
    (r"\bround[- ]tripping\b", "round-tripping"),
    (r"\btrade[- ]based\b", "trade-based laundering"),
    (r"\bfunnel account\b", "funnel account"),
    (r"\bcuckoo smurfing\b", "cuckoo smurfing"),
)

_TRANSACTION_TYPE_PATTERNS: tuple[tuple[str, str], ...] = (
    (r"\bcrypto(?:currency)?\b|\bbitcoin\b|\bbtc\b|\beth\b", "crypto"),
    (r"\bwire\b|\bswift\b", "wire"),
    (r"\bcash\b", "cash"),
    (r"\bcheques?\b|\bpersonal checks?\b|\bcashier'?s? checks?\b|\bcheck payments?\b", "cheque"),
    (r"\bcredit card\b|\bdebit card\b|\bcard\b", "card"),
    (r"\bach\b", "ach"),
)


def _extract_aml_pattern(query: str) -> str | None:
    q = query.lower()
    for regex, label in _AML_PATTERN_PATTERNS:
        if re.search(regex, q):
            return label
    return None


def _extract_transaction_type(query: str) -> str | None:
    q = query.lower()
    for regex, label in _TRANSACTION_TYPE_PATTERNS:
        if re.search(regex, q):
            return label
    return None


def _keyword_intent_fallback(query: str) -> str | None:
    """Best-effort intent classification used when the LLM call fails or
    returns "unknown", and as a sanity check on the LLM's own answer.

    Ordered by specificity: a named customer/account beats a network
    question, which beats a named pattern, which beats generic scoring or
    summarizing language.
    """
    q = query.lower()
    if any(kw in q for kw in _LOOKUP_KEYWORDS) and re.search(r"\d", query):
        return "customer_lookup"
    if any(kw in q for kw in _GRAPH_KEYWORDS):
        return "graph_query"
    if any(kw in q for kw in _DETECT_PATTERN_KEYWORDS) or _extract_aml_pattern(query):
        return "detect_pattern"
    if any(kw in q for kw in _SCORE_KEYWORDS):
        return "score_risk"
    if any(kw in q for kw in _SUMMARIZE_KEYWORDS):
        return "summarize"
    if any(kw in q for kw in _INVESTIGATE_KEYWORDS):
        return "investigate"
    return None

def extract_rule_based(query: str) -> dict[str, Any]:
    """Extract high-precision entities using regex and dateparser."""
    entities: dict[str, Any] = {}

    # 1. Date extraction — explicit date, or "last N days" relative range
    days_match = re.search(r"last\s+(\d+)\s+day", query, re.IGNORECASE)
    if days_match:
        n_days = int(days_match.group(1))
        entities["date_to"] = datetime.now().isoformat()
        entities["date_from"] = (datetime.now() - timedelta(days=n_days)).isoformat()
    date_val = dateparser.parse(query, settings={'STRICT_PARSING': False})
    if date_val:
        entities["date"] = date_val.isoformat()

    # 2. Customer IDs (e.g., CUST-1023, cust 4455, "customer 4521")
    ids = re.findall(r"CUST[- ]?\d+", query, re.IGNORECASE)
    if ids:
        ids = [uid.upper().replace(" ", "-") for uid in ids]
    else:
        raw_ids = re.findall(r"customer\s+#?(\d+)", query, re.IGNORECASE)
        ids = [f"CUST-{uid}" for uid in raw_ids]
    if ids:
        entities["customer_ids"] = ids
        entities["customer_id"] = ids[0]

    # 2b. Account IDs (e.g., ACC-1023, "account 998")
    acc_ids = re.findall(r"ACC[- ]?\d+", query, re.IGNORECASE)
    if acc_ids:
        acc_ids = [aid.upper().replace(" ", "-") for aid in acc_ids]
    else:
        raw_acc_ids = re.findall(r"account\s+#?(\d+)", query, re.IGNORECASE)
        acc_ids = [f"ACC-{aid}" for aid in raw_acc_ids]
    if acc_ids:
        entities["account_id"] = acc_ids[0]

    # 3. Amounts, with comparison direction
    amount_num = r"(\d[\d,]*(?:\.\d+)?)"
    more_than = re.search(
        r"(?:more than|over|above|greater than|exceed(?:ing|s)?)\s*[\$₹£€]?\s?" + amount_num,
        query, re.IGNORECASE,
    )
    less_than = re.search(
        r"(?:less than|below|under|fewer than)\s*[\$₹£€]?\s?" + amount_num,
        query, re.IGNORECASE,
    )
    if more_than:
        entities["amount_min"] = float(more_than.group(1).replace(",", ""))
    if less_than:
        entities["amount_max"] = float(less_than.group(1).replace(",", ""))

    amounts = re.findall(r"[\$₹£€]\s?\d[\d,]*", query)
    if amounts:
        entities["amounts"] = amounts

    # 3b. Bank names (best-effort, e.g. "Chase Bank", "HSBC Bank")
    bank_match = re.search(r"([A-Z][a-zA-Z&]+(?:\s[A-Z][a-zA-Z&]+)*\sBank)", query)
    if bank_match:
        entities["bank"] = bank_match.group(1)

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
        entities["country"] = countries[0]

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


_FILTER_KEYS = (
    "customer_id", "account_id", "date_from", "date_to",
    "amount_min", "amount_max", "country", "bank",
)


def parse_intent(query: str) -> dict[str, Any]:
    """Primary entry point: merge rule-based and LLM extractions.

    Returns a dict with semantic fields (intent, aml_pattern,
    transaction_type, threshold_amount), a flat "filters" dict
    (customer_id, account_id, date_from, date_to, amount_min, amount_max,
    country, bank) ready for dataset filtering, and "_entities" retaining
    the raw rule-based extraction for debugging/trace purposes.
    """
    logger.info(f"Parsing intent for query: '{query}'")

    rules_out = extract_rule_based(query)
    llm_out = extract_llm(query)

    # Merge, keeping LLM's structure but injecting rule-based entities if found
    merged = {**llm_out}

    # 1. If the LLM failed outright (error/unknown), fall back to keywords.
    if merged.get("intent") in (None, "unknown") or "error" in merged:
        fallback_intent = _keyword_intent_fallback(query)
        if fallback_intent:
            merged["intent"] = fallback_intent

    # 2. High-precision overrides that beat both the LLM and the keyword
    #    fallback, because they're backed by an unambiguous entity match.
    #
    #    a) An explicit customer/account id always means customer_lookup —
    #       this is the single most reliable signal in the query.
    if rules_out.get("customer_id") or rules_out.get("account_id"):
        merged["intent"] = "customer_lookup"

    #    b) "graph_query" is over-triggered by LLMs primed on the word
    #       "riskiest" (see prompt examples) even when the query has no
    #       network/relationship language at all. Demote it back to the
    #       best keyword-based guess in that case.
    elif merged.get("intent") == "graph_query":
        q_lower = query.lower()
        if not any(kw in q_lower for kw in _GRAPH_KEYWORDS):
            merged["intent"] = _keyword_intent_fallback(query) or "score_risk"

    # 3. Backstop aml_pattern / transaction_type extraction — the regex
    #    pass is authoritative for named typologies, so it fills gaps the
    #    LLM left null and corrects cases where the LLM missed a term the
    #    prompt explicitly lists.
    rule_pattern = _extract_aml_pattern(query)
    if rule_pattern and not merged.get("aml_pattern"):
        merged["aml_pattern"] = rule_pattern

    rule_txn_type = _extract_transaction_type(query)
    if rule_txn_type and not merged.get("transaction_type"):
        merged["transaction_type"] = rule_txn_type

    # Flat filters dict, consumed directly by app.agents.filters.apply_filters
    merged["filters"] = {key: rules_out[key] for key in _FILTER_KEYS if key in rules_out}

    # Also attach the raw rule-based entities under a specific key for the state schema
    merged["_entities"] = rules_out

    logger.debug(f"Parsed intent result: {merged}")
    return merged
