"""
Prometheus metrics definitions for the AI Legal Assistant
"""

from prometheus_client import Counter, Histogram

# Define metrics
REQUEST_COUNTER = Counter(
    "http_requests_total", "Total http requests", ["method", "endpoint", "status_code"]
)
LATENCY_HIST = Histogram(
    "request_latency_seconds", "Histogram of request latency", ["method", "endpoint"]
)
OPENAI_TOKENS = Counter(
    "openai_tokens_total", "Total tokens used in OpenAI API", ["type"]
)
CHROMADB_EXCEPTIONS = Counter(
    "chromadb_exceptions_total", "Total ChromaDB exceptions", ["operation"]
)
HF_EMBEDDINGS_EXCEPTIONS = Counter(
    "hf_embeddings_exceptions_total",
    "Total Hugging Face embeddings exceptions",
    ["model"],
)
OPENAI_LLM_EXCEPTIONS = Counter(
    "openai_llm_exceptions_total", "Total OpenAI LLM exceptions", ["model"]
)
