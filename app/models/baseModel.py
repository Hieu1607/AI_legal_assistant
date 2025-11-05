"""
Base model for all Pydantic models.
"""

from pydantic import BaseModel, Field


class RAGRequest(BaseModel):
    """
    Request model for RAG endpoint.
    """

    query: str = Field(
        description="The question to ask.",
        min_length=5,
        max_length=200,
        json_schema_extra={"example": "Chương I điều 1 luật tố tụng dân sự mới nhất ?"}
    )
