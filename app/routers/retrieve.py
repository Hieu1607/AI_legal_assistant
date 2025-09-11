"""
Router/Controller for embedding retrieval endpoints
"""

import os
import sys

from fastapi import APIRouter
from fastapi.responses import JSONResponse

# Set up logging
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))

from app.constants.http_status import HTTP_STATUS_INTERNAL_SERVER_ERROR, HTTP_STATUS_OK
from app.logic.retrieve_logic import retrieve_embeddings_logic
from app.models.base_model import QueryRequest
from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

router = APIRouter()


@router.post("/retrieve")
def retrieve_embeddings(request: QueryRequest):
    """
    Endpoint to retrieve relevant embeddings for a query

    Args:
        request (QueryRequest): Query request containing question and top_k

    Returns:
        JSONResponse: List of relevant chunks or error response
    """
    try:
        result = retrieve_embeddings_logic(request.question, request.top_k)

        if not result:
            return JSONResponse(status_code=HTTP_STATUS_OK, content=[])

        return result

    except (IndexError, KeyError, FileNotFoundError, ImportError, ValueError) as e:
        logger.info(
            "An error occurred during embedding retrieval: %s", e, exc_info=True
        )
        return JSONResponse(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "type": "internal_error",
                    "message": "An error occurred while processing your request",
                }
            },
        )
