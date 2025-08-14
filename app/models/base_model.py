"""
Base models for API request/response schemas
"""

from pydantic import BaseModel


class QueryRequest(BaseModel):
    """Request model for embedding retrieval queries"""

    question: str
    top_k: int = 5


class QueryQuestion(BaseModel):
    """Request model for RAG queries"""

    question: str
