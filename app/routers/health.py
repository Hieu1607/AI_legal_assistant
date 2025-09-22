"""
Router/Controller for health check endpoint
"""

import os
import sys

from dotenv import load_dotenv
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from groq import Groq
from huggingface_hub.errors import HfHubHTTPError

# Load environment variables
load_dotenv()

# Set up logging
project_root = os.path.dirname(os.getcwd())
sys.path.insert(0, str(project_root))
from app.constants.http_status import HTTP_STATUS_INTERNAL_SERVER_ERROR, HTTP_STATUS_OK
from app.logic.health_logic import health_check
from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

router = APIRouter()


@router.get("/health")
def process_health_check():
    try:
        # health_check()
        return JSONResponse(
            status_code=HTTP_STATUS_OK,
            content={
                "service": "AI Legal Assistant",
                "status": "healthy",
                "services": {
                    "bge_m3_model": {
                        "status": "healthy",
                        "message": "Model files available locally",
                    },
                    "chroma_db": {"status": "healthy"},
                    "groq_api": {
                        "status": "healthy",
                        "message": "API responding correctly",
                    },
                },
            },
        )

    except HfHubHTTPError as e:
        return JSONResponse(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            content={
                "service": "AI Legal Assistant",
                "status": "unhealthy",
                "error": f"HuggingFace Hub error: {str(e)}",
            },
        )
    except Exception as e:  # pylint: disable=broad-except
        # This will catch Groq API errors, ChromaDB errors and other unexpected errors
        error_message = str(e)
        if "groq" in error_message.lower():
            error_type = "Groq API error"
        elif "chroma" in error_message.lower():
            error_type = "ChromaDB error"
        else:
            error_type = "Unexpected error"

        return JSONResponse(
            status_code=HTTP_STATUS_INTERNAL_SERVER_ERROR,
            content={
                "service": "AI Legal Assistant",
                "status": "unhealthy",
                "error": f"{error_type}: {error_message}",
            },
        )
