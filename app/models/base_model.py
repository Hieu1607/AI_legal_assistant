"""
Base models for API request/response schemas.
Contains all Pydantic models for the application.
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator


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


class AgentRequest(BaseModel):
    """
    Request model for agent API endpoint.

    Attributes:
        question: Legal question to process (10-1000 characters)
        top_k: Number of top relevant chunks to retrieve (1-20)
        total_steps: Total number of processing steps (1-3)
        timeout_sec: Timeout for each step in seconds (5-300)
    """

    question: str = Field(
        default="Chương II điều 29 bộ luật hàng hải nói gì?",
        min_length=10,
        max_length=1000,
        description="Legal question to ask the agent (10-1000 characters)",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of top relevant chunks to retrieve (1-20)",
    )
    total_steps: int = Field(
        default=3, ge=1, le=3, description="Total number of steps to execute (1-3)"
    )
    timeout_sec: int = Field(
        default=20, ge=5, le=300, description="Timeout for each step in seconds (5-300)"
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, v):
        """Validate that question is not empty or whitespace only."""
        if not v or v.isspace():
            raise ValueError("Question cannot be empty or only whitespace")
        return v.strip()

    @field_validator("top_k")
    @classmethod
    def validate_top_k(cls, v):
        """Validate top_k parameter range."""
        if v < 1:
            raise ValueError("top_k must be at least 1")
        if v > 20:
            raise ValueError("top_k cannot exceed 20")
        return v

    @field_validator("total_steps")
    @classmethod
    def validate_total_steps(cls, v):
        """Validate total_steps parameter values."""
        if v not in [1, 2, 3]:
            raise ValueError("total_steps must be 1, 2, or 3")
        return v

    @field_validator("timeout_sec")
    @classmethod
    def validate_timeout(cls, v):
        """Validate timeout parameter range."""
        if v < 5:
            raise ValueError("timeout_sec must be at least 5 seconds")
        if v > 300:
            raise ValueError("timeout_sec cannot exceed 300 seconds (5 minutes)")
        return v


class AgentResponse(BaseModel):
    """
    Response model for agent API endpoint.

    Attributes:
        success: Whether the request was successful
        status_code: HTTP status code
        step_completed: Number of steps successfully completed
        data: Response data (varies by step)
        message: Human-readable message
        execution_time: Total execution time in seconds
    """

    success: bool
    status_code: int
    step_completed: int
    data: Any
    message: str
    execution_time: float
