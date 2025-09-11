"""
Router/Controller for RAG (Retrieval-Augmented G        return JSONResponse(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "error": {
                    "type": "internal_error",
                    "message": "An error occurred while processing your question",
                },
            },
        ) endpoints
"""

import os
import sys

from fastapi import APIRouter
from fastapi.responses import JSONResponse

# Set up logging
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))

from app.constants.http_status import HTTP_STATUS_OK
from app.logic.rag_logic import process_rag_query
from app.models.base_model import QueryQuestion
from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

router = APIRouter()


@router.post("/rag")
async def ask_model(request: QueryQuestion):
    """
    Endpoint to process RAG queries using LLM

    Args:
        request (QueryQuestion): Query request containing the question

    Returns:
        JSONResponse: Response containing answer and metadata or error response
    """
    try:
        result = await process_rag_query(request.question)

        return JSONResponse(
            status_code=HTTP_STATUS_OK,
            content={
                "status": "success",
                "data": {
                    "answer": result["answer"],
                    "question": result["question"],
                    "context_count": result["context_count"],
                },
            },
        )

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.info("An error occurred during asking model: %s", e)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": {
                    "type": "internal_error",
                    "message": "An error occurred while processing your request",
                },
            },
        )
