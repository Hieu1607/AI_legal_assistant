import os
import sys
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

# Set up logging
project_root = os.path.dirname(os.getcwd())
sys.path.insert(0, str(project_root))
from app.constants.http_status import HTTP_STATUS_UNPROCESSABLE_ENTITY
from app.routers import health, metrics, rag, retrieve
from app.routers.metrics import metrics_collector
from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

app = FastAPI()


# Add middleware to track metrics
@app.middleware("http")
async def track_metrics(request: Request, call_next):
    """Middleware to track request metrics"""

    start_time = time.time()
    response = await call_next(request)
    latency_ms = (time.time() - start_time) * 1000

    # Record metrics
    endpoint = request.url.path
    method = request.method
    metrics_collector.record_request(endpoint, response.status_code, latency_ms, method)

    return response


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
app.include_router(health.router)
app.include_router(metrics.router)


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
            "metrics": "/metrics",
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
