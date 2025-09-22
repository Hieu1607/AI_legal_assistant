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

from app.constants.http_status import HTTP_STATUS_OK, HTTP_STATUS_INTERNAL_SERVER_ERROR
from app.logic.rag_logic import process_rag_query
from app.models.base_model import QueryQuestion
from configs.logger import get_logger, setup_logging
from src.cache.cache_manager import get_cache_manager

setup_logging()
logger = get_logger(__name__)

router = APIRouter()


@router.post("/rag")
async def ask_model(request: QueryQuestion):
    """
    Endpoint to process RAG queries using LLM with caching

    Args:
        request (QueryQuestion): Query request containing the question

    Returns:
        JSONResponse: Response containing answer and metadata or error response
    """
    try:
        # Initialize cache manager
        cache_ttl = int(os.getenv("CACHE_TTL_SECONDS", "3600"))
        cache_max_size = int(os.getenv("CACHE_MAX_SIZE", "1000"))
        cache_manager = get_cache_manager(ttl_seconds=cache_ttl, max_size=cache_max_size)
        
        # Check cache first
        cached_result = cache_manager.get(request.question)
        if cached_result:
            answer, question, context_count = cached_result
            logger.info("Cache hit for question: %s", question[:50])
            
            return JSONResponse(
                status_code=HTTP_STATUS_OK,
                content={
                    "status": "success",
                    "data": {
                        "answer": answer,
                        "question": question,
                        "context_count": context_count,
                        "from_cache": True,
                    },
                },
            )
        
        # Cache miss - process query normally
        logger.info("Cache miss for question: %s", request.question[:50])
        result = await process_rag_query(request.question)
        
        # Cache the result
        cache_manager.set(
            question=result["question"],
            answer=result["answer"],
            context_count=result["context_count"]
        )

        return JSONResponse(
            status_code=HTTP_STATUS_OK,
            content={
                "status": "success",
                "data": {
                    "answer": result["answer"],
                    "question": result["question"],
                    "context_count": result["context_count"],
                    "from_cache": False,
                    "timing": result.get("timing", {}),
                },
            },
        )

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.info("An error occurred during asking model: %s", e)
        return JSONResponse(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "error": {
                    "type": "internal_error",
                    "message": "An error occurred while processing your question",
                },
            },
        )
