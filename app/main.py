import os
import sys
import time

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Load environment variables
load_dotenv()

# Set up logging
project_root = os.path.dirname(os.getcwd())
sys.path.insert(0, str(project_root))
from app.constants.http_status import HTTP_STATUS_UNPROCESSABLE_ENTITY
from app.routers import agent, health, metrics, rag, retrieve
from app.logic.metrics_logic import increment_request_counter, record_request_latency
from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

app = FastAPI()

# Middleware to track metrics
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to track HTTP request metrics"""
    start_time = time.time()
    
    # Process the request
    response = await call_next(request)
    
    # Calculate latency
    latency = time.time() - start_time
    
    # Extract request info
    method = request.method
    endpoint = request.url.path
    status_code = str(response.status_code)
    
    # Record metrics
    try:
        increment_request_counter(method, endpoint, status_code)
        record_request_latency(method, endpoint, latency)
    except Exception as e:
        logger.error(f"Error recording metrics: {str(e)}")
    
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(retrieve.router)
app.include_router(rag.router)
app.include_router(agent.router)
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
            "agent": "/agent",
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
