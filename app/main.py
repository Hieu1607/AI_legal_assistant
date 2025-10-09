import os
import sys

import google.generativeai as genai
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables and configure Gemini API
load_dotenv()
genai.configure(api_key=os.getenv("Gemini_API_KEY"))  # type: ignore

# Set up logging
project_root = os.path.dirname(os.getcwd())
sys.path.insert(0, str(project_root))
from app.constants.http_status import HTTP_STATUS_UNPROCESSABLE_ENTITY
from app.routers import agent, health, rag, retrieve
from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

app = FastAPI()

# Configure CORS to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(retrieve.router)
app.include_router(rag.router)
app.include_router(agent.router)
app.include_router(health.router)


@app.get("/")
def root():
    """Root endpoint with service information"""
    return {
        "service": "AI Legal Assistant",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "retrieve": "/retrieve",
            "rag": "/rag",
            "agent": "/agent",
        },
    }


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
        status_code=HTTP_STATUS_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "validation_error",
                "message": "Input data is not valid",
                "fields": errors,
            }
        },
    )
