"""
Business logic for metrics handling
"""

import os
import sys
from typing import Dict, Any

# Set up logging
project_root = os.path.dirname(os.getcwd())
sys.path.insert(0, str(project_root))
from configs.logger import get_logger, setup_logging
from services.metrics import REQUEST_COUNTER, LATENCY_HIST, GROQ_TOKENS

setup_logging()
logger = get_logger(__name__)


def get_metrics_data() -> Dict[str, Any]:
    """
    Get current metrics data
    
    Returns:
        Dict containing current metrics information
    """
    try:
        logger.info("Retrieving metrics data")
        
        # Get current metric values (this is mainly for logging/monitoring)
        metrics_info = {
            "request_counter": "Available",
            "latency_histogram": "Available", 
            "groq_tokens": "Available",
            "status": "healthy"
        }
        
        logger.info("Metrics data retrieved successfully")
        return metrics_info
        
    except Exception as e:
        logger.error(f"Error retrieving metrics data: {str(e)}")
        raise


def increment_request_counter(method: str, endpoint: str, status_code: str) -> None:
    """
    Increment the HTTP request counter
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint
        status_code: HTTP status code
    """
    try:
        REQUEST_COUNTER.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        logger.debug(f"Incremented request counter: {method} {endpoint} {status_code}")
    except Exception as e:
        logger.error(f"Error incrementing request counter: {str(e)}")


def record_request_latency(method: str, endpoint: str, latency: float) -> None:
    """
    Record request latency
    
    Args:
        method: HTTP method
        endpoint: API endpoint  
        latency: Request latency in seconds
    """
    try:
        LATENCY_HIST.labels(method=method, endpoint=endpoint).observe(latency)
        logger.debug(f"Recorded latency: {method} {endpoint} {latency}s")
    except Exception as e:
        logger.error(f"Error recording latency: {str(e)}")


def increment_groq_tokens(token_type: str, count: int = 1) -> None:
    """
    Increment Groq token usage counter
    
    Args:
        token_type: Type of tokens (input, output, etc.)
        count: Number of tokens to increment by
    """
    try:
        GROQ_TOKENS.labels(type=token_type).inc(count)
        logger.debug(f"Incremented Groq tokens: {token_type} +{count}")
    except Exception as e:
        logger.error(f"Error incrementing Groq tokens: {str(e)}")