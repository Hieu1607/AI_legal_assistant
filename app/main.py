import os
import sys
import time

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Set up logging
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(project_root))
from app import agent, rag, retrieve
from configs.logger import get_logger_app, setup_logging

setup_logging()
logger = get_logger_app()

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "https://ai-legal-assistant-production-1.onrender.com",  # Remove trailing slash
        "*"  # Allow all origins for development (remove this in production)
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(retrieve.router)
app.include_router(rag.router)
app.include_router(agent.router)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment platforms"""
    return {"status": "healthy", "service": "AI Legal Assistant"}


# Root endpoint
@app.get("/")
async def app_root():
    """Root endpoint with service information"""
    return {
        "service": "AI Legal Assistant",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
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
            "field": ".".join(str(loc) for loc in err["loc"][1:]),  # loại bỏ 'body'
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


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
