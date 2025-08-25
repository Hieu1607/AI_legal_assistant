import os
import sys

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from google.api_core.exceptions import GoogleAPICallError
from huggingface_hub import hf_hub_download
from huggingface_hub.errors import HfHubHTTPError

# Load environment variables and configure Gemini API
load_dotenv()
genai.configure(api_key=os.getenv("Gemini_API_KEY"))  # type: ignore

# Set up logging
project_root = os.path.dirname(os.getcwd())
sys.path.insert(0, str(project_root))
from app.routers import rag, retrieve
from configs.logger import get_logger, setup_logging
from src.store_vector.init_index import init_chroma_index

setup_logging()
logger = get_logger(__name__)

app = FastAPI()

app.include_router(retrieve.router)
app.include_router(rag.router)


@app.get("/")
def root():
    """Root endpoint with service information"""
    return {
        "service": "AI Legal Assistant",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {"health": "/health", "retrieve": "/retrieve", "rag": "/rag"},
    }


@app.get("/health")
def health_check():
    try:
        # Check HuggingFace model availability
        hf_hub_download(
            repo_id="BAAI/bge-m3", filename="config.json", local_files_only=True
        )

        # Check ChromaDB collection
        _, legal_collection = init_chroma_index()
        collection_count = legal_collection.count()
        results = legal_collection.peek(limit=5)

        # Check Gemini API
        model = genai.GenerativeModel("gemini-2.5-pro")  # type: ignore
        model.generate_content("Hello")

        return JSONResponse(
            status_code=200,
            content={
                "service": "AI Legal Assistant",
                "status": "healthy",
                "services": {
                    "bge_m3_model": {
                        "status": "healthy",
                        "message": "Model files available locally",
                    },
                    "chroma_db": {
                        "status": "healthy",
                        "message": f"Collection accessible with {collection_count} documents",
                        "collection_info": {
                            "document_count": collection_count,
                            "sample_documents": (
                                len(results.get("ids", [])) if results else 0
                            ),
                        },
                    },
                    "gemini_api": {
                        "status": "healthy",
                        "message": "API responding correctly",
                    },
                },
            },
        )
    except HfHubHTTPError as e:
        return JSONResponse(
            status_code=500,
            content={
                "service": "AI Legal Assistant",
                "status": "unhealthy",
                "error": f"HuggingFace Hub error: {str(e)}",
            },
        )
    except GoogleAPICallError as e:
        return JSONResponse(
            status_code=500,
            content={
                "service": "AI Legal Assistant",
                "status": "unhealthy",
                "error": f"Gemini API error: {str(e)}",
            },
        )
    except Exception as e:  # pylint: disable=broad-except
        # This will catch ChromaDB errors and other unexpected errors
        error_message = str(e)
        if "chroma" in error_message.lower():
            error_type = "ChromaDB error"
        else:
            error_type = "Unexpected error"

        return JSONResponse(
            status_code=500,
            content={
                "service": "AI Legal Assistant",
                "status": "unhealthy",
                "error": f"{error_type}: {error_message}",
            },
        )


# Exception handler for validation error
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    logger.info("An error occured: %s", exc.errors())
    errors = [
        {
            "field": ".".join(str(loc) for loc in err["loc"][1:]),  # delete 'body'
            "error": err["msg"],
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "validation_error",
                "message": "Input data is not valid",
                "fields": errors,
            }
        },
    )
