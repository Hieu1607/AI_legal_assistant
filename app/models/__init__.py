"""
Models package for data models.
Contains all Pydantic models for the application.
"""

from .base_model import QueryQuestion, QueryRequest

__all__ = [
    "QueryRequest",
    "QueryQuestion",
]
