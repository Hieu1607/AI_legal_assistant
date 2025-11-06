"""
Base model for all Pydantic models.
"""

from pydantic import BaseModel, Field, field_validator


class RAGRequest(BaseModel):
    """
    Request model for RAG endpoint.
    """

    query: str = Field(
        description="The question to ask.",
        min_length=5,
        max_length=200,
        json_schema_extra={"example": "Chương I điều 1 luật tố tụng dân sự mới nhất ?"},
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, v):
        # Remove potential injection attempts
        dangerous_patterns = ["<script>", "javascript:", "eval("]
        for pattern in dangerous_patterns:
            if pattern.lower() in v.lower():
                raise ValueError(f"Query contains dangerous pattern: {pattern}")
        return v.strip()
