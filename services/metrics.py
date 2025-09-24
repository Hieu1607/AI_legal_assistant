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
GROQ_TOKENS = Counter("groq_tokens_total", "Total tokens used in Groq API", ["type"])
CHROMADB_EXCEPTIONS = Counter(
    "chromadb_exceptions_total", "Total ChromaDB exceptions", ["operation"]
)
HF_EMBEDDINGS_EXCEPTIONS = Counter(
    "hf_embeddings_exceptions_total",
    "Total Hugging Face embeddings exceptions",
    ["model"],
)
GROQ_LLM_EXCEPTIONS = Counter(
    "groq_llm_exceptions_total", "Total Groq LLM exceptions", ["model"]
)
