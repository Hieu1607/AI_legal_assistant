"""
Base models for API request/response schemas.
Contains all Pydantic models for the application.
"""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for embedding retrieval queries"""

    question: str
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of top relevant chunks to retrieve (1-20)",
    )


class QueryQuestion(BaseModel):
    """Request model for RAG queries"""

    question: str
