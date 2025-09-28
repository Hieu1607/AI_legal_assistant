"""
Business logic for metrics handling
"""

import os
import sys
from typing import Any, Dict

# Set up logging
project_root = os.path.dirname(os.getcwd())
sys.path.insert(0, str(project_root))
from configs.logger import get_logger, setup_logging
from services.metrics import (
    CHROMADB_EXCEPTIONS,
    GROQ_LLM_EXCEPTIONS,
    GROQ_TOKENS,
    HF_EMBEDDINGS_EXCEPTIONS,
    LATENCY_HIST,
    REQUEST_COUNTER,
)

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

        # Initialize some sample data if metrics are empty
        # This ensures metrics appear in Prometheus
        try:
            # Initialize with zero values if not already set
            REQUEST_COUNTER.labels(
                method="GET", endpoint="/health", status_code="200"
            ).inc(0)
            REQUEST_COUNTER.labels(
                method="POST", endpoint="/agent", status_code="200"
            ).inc(0)
            REQUEST_COUNTER.labels(
                method="GET", endpoint="/metrics", status_code="200"
            ).inc(0)

            LATENCY_HIST.labels(method="GET", endpoint="/health").observe(0)
            LATENCY_HIST.labels(method="POST", endpoint="/agent").observe(0)

            GROQ_TOKENS.labels(type="input").inc(0)
            GROQ_TOKENS.labels(type="output").inc(0)
            GROQ_TOKENS.labels(type="total").inc(0)

            # Initialize new exception metrics
            CHROMADB_EXCEPTIONS.labels(operation="search").inc(0)
            CHROMADB_EXCEPTIONS.labels(operation="query").inc(0)
            CHROMADB_EXCEPTIONS.labels(operation="retrieve").inc(0)

            HF_EMBEDDINGS_EXCEPTIONS.labels(model="hieuailearning/BAAI_bge_m3_api").inc(
                0
            )

            GROQ_LLM_EXCEPTIONS.labels(model="openai/gpt-oss-20b").inc(0)

            logger.info("Metrics initialized successfully")
        except Exception as e:
            logger.warning(f"Error initializing sample metrics: {str(e)}")

        # Get current metric values (this is mainly for logging/monitoring)
        metrics_info = {
            "request_counter": "Available",
            "latency_histogram": "Available",
            "groq_tokens": "Available",
            "chromadb_exceptions": "Available",
            "hf_embeddings_exceptions": "Available",
            "groq_llm_exceptions": "Available",
            "status": "healthy",
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
        REQUEST_COUNTER.labels(
            method=method, endpoint=endpoint, status_code=status_code
        ).inc()
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


def increment_chromadb_exceptions(operation: str, count: int = 1) -> None:
    """
    Increment ChromaDB exception counter

    Args:
        operation: Type of operation (search, query, retrieve)
        count: Number of exceptions to increment by
    """
    try:
        CHROMADB_EXCEPTIONS.labels(operation=operation).inc(count)
        logger.debug(f"Incremented ChromaDB exceptions: {operation} +{count}")
    except Exception as e:
        logger.error(f"Error incrementing ChromaDB exceptions: {str(e)}")


def increment_hf_embeddings_exceptions(model: str, count: int = 1) -> None:
    """
    Increment Hugging Face embeddings exception counter

    Args:
        model: Model name or endpoint
        count: Number of exceptions to increment by
    """
    try:
        HF_EMBEDDINGS_EXCEPTIONS.labels(model=model).inc(count)
        logger.debug(f"Incremented HF embeddings exceptions: {model} +{count}")
    except Exception as e:
        logger.error(f"Error incrementing HF embeddings exceptions: {str(e)}")


def increment_groq_llm_exceptions(model: str, count: int = 1) -> None:
    """
    Increment Groq LLM exception counter

    Args:
        model: Model name
        count: Number of exceptions to increment by
    """
    try:
        GROQ_LLM_EXCEPTIONS.labels(model=model).inc(count)
        logger.debug(f"Incremented Groq LLM exceptions: {model} +{count}")
    except Exception as e:
        logger.error(f"Error incrementing Groq LLM exceptions: {str(e)}")
