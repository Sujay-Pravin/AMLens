"""
Tool Integration Layer — Phase 6.

Centralized manager to execute analytics tools safely.
Includes a registry pattern, timeout enforcement, and error isolation.

When Member 2's real modules are ready, only the imports below need to change.
"""

import concurrent.futures
from typing import Any, Callable

from app.config.settings import settings
from app.core.logging import get_logger

# Import dummy analytics functions.
# Phase 12 Swap: Change these imports to Member 2's real module.
from app.tools.dummy_analytics import (
    run_eda,
    generate_features,
    detect_rules,
    detect_anomalies,
    calculate_risk,
)

logger = get_logger(__name__)

# Tool Registry: Maps string names (from the planner) to actual python functions.
REGISTRY: dict[str, Callable[..., dict[str, Any]]] = {
    "run_eda": run_eda,
    "generate_features": generate_features,
    "detect_rules": detect_rules,
    "detect_anomalies": detect_anomalies,
    "calculate_risk": calculate_risk,
}

def call_tool(name: str, **kwargs: Any) -> dict[str, Any]:
    """Execute a registered tool safely with a timeout and error handling.
    
    Args:
        name: Name of the tool to execute (e.g., "run_eda").
        **kwargs: Arguments to pass to the tool (usually `filters`, `rule_out`, `ml_out`).
        
    Returns:
        dict: The tool's output, or a dict containing an "error" key if execution failed.
    """
    logger.info(f"Executing tool: '{name}'")
    
    if name not in REGISTRY:
        error_msg = f"Unknown tool requested: '{name}'"
        logger.error(error_msg)
        return {"error": error_msg}
        
    tool_func = REGISTRY[name]
    
    # Execute with a timeout to prevent the agent from hanging indefinitely
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(tool_func, **kwargs)
            # Wait up to the configured timeout limit
            result = future.result(timeout=settings.tool_timeout_seconds)
            
            logger.debug(f"Tool '{name}' completed successfully.")
            return result
            
    except concurrent.futures.TimeoutError:
        error_msg = f"Tool '{name}' timed out after {settings.tool_timeout_seconds} seconds."
        logger.error(error_msg)
        return {"error": error_msg}
        
    except Exception as e:
        error_msg = f"Tool '{name}' failed with exception: {type(e).__name__}: {e}"
        logger.error(error_msg)
        return {"error": error_msg}
