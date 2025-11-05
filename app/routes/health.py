"""
Router/Controller for health check endpoint
"""

from http import HTTPStatus

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.configs.logger import get_logger
from app.services.health_service import health_check


logger = get_logger(__name__)

router = APIRouter()


@router.get("/health")
def process_health_check():
    try:
        health_check()
        return JSONResponse(
            status_code=HTTPStatus.OK,
            content={
                "service": "AI Legal Assistant",
                "status": "healthy",
                "services": {
                    "weaviate_cloud": {"status": "healthy"},
                    "gemini_api": {
                        "status": "healthy",
                        "message": "API responding correctly",
                    },
                },
            },
        )

    except Exception as e:  # pylint: disable=broad-except
        # This will catch Weaviate errors and other unexpected errors
        error_message = str(e)
        if "weaviate" in error_message.lower():
            error_type = "Weaviate error"
        else:
            error_type = "Unexpected error"
        logger.error(f"Health check failed: {error_message}")
        return JSONResponse(
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
            content={
                "service": "AI Legal Assistant",
                "status": "unhealthy",
                "error": f"{error_type}",
            },
        )
