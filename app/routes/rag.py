"""
Route/controller for RAG-related endpoints.
"""

from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.configs.logger import get_logger
from app.models.baseModel import RAGRequest
from app.services.rag_service import RAGService
from app.tools.cache_manager import RAGCacheManager, get_cache_manager
from app.tools.weaviate_search import WeaviateSearcher, get_searcher

logger = get_logger(__name__)

router = APIRouter()


@router.post("/rag")
async def rag_endpoint(
    request: RAGRequest,
) -> JSONResponse:
    """
    Endpoint to handle RAG requests.

    Args:
        request (RAGRequest): The RAG request payload.

    Returns:
        RAGResponse: The RAG response payload.
    """
    try:
        rag_service = RAGService()
        
        # Initialize dependencies internally to avoid exposing them as request parameters
        try:
            searcher = get_searcher()
            cache_manager = await get_cache_manager()
        except Exception as e:
            logger.error(f"Error initializing dependencies: {e}")
            return JSONResponse(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                content={
                    "status": "error",
                    "error": "Failed to initialize services.",
                },
            )
        
        response_data = await rag_service.process_query(
            request.query, searcher=searcher, cache_manager=cache_manager
        )
        return JSONResponse(
            status_code=HTTPStatus.OK,
            content={"status": "success", "data": response_data},
        )
    except TimeoutError as timeout_error:
        logger.error(f"Timeout error in /rag endpoint: {timeout_error}")
        return JSONResponse(
            status_code=HTTPStatus.GATEWAY_TIMEOUT,
            content={
                "status": "error",
                "error": "The request timed out. Please try again later.",
            },
        )

    except ValueError as value_error:
        logger.error(f"Value error in /rag endpoint: {value_error}")
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content={
                "status": "error",
                "error": str(value_error),
            },
        )

    except Exception as e:
        logger.error(f"Error in /rag endpoint: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "error": "An error occurred while processing the request.",
            },
        )
