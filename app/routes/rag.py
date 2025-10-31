"""
Route/controller for RAG-related endpoints.
"""

import os
import sys
from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.configs.logger import get_logger, setup_logging
from app.models.baseModel import RAGRequest
from app.services.rag_service import RAGService

setup_logging()
logger = get_logger(__name__)

router = APIRouter()


@router.post("/rag")
async def rag_endpoint(request: RAGRequest):
    """
    Endpoint to handle RAG requests.

    Args:
        request (RAGRequest): The RAG request payload.

    Returns:
        RAGResponse: The RAG response payload.
    """
    rag_service = RAGService()
    try:
        response_data = await rag_service.process_query(request.query)
        return JSONResponse(
            status_code=HTTPStatus.OK,
            content={"status": "success", "data": response_data},
        )
    except Exception as e:
        logger.error(f"Error in /rag endpoint: {e}")
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "error": "An error occurred while processing the request.",
            },
        )
