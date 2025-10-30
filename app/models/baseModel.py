"""
Base model for all Pydantic models.
"""

from pydantic import BaseModel, Field


class RAGRequest(BaseModel):
    """
    Request model for RAG endpoint.
    """

    query: str = Field(
        json_schema_extra={"example": "Chương I điều 1 luật tố tụng dân sự mới nhất ?"}
    )
