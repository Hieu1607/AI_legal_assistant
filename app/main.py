"""Fast API application entry point."""

import time
from http import HTTPStatus

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from app.configs.logger import get_logger, setup_logging
from app.routes import all_router
from app.routes.metrics import get_metrics_collector

setup_logging()
logger = get_logger(__name__)


def create_app() -> FastAPI:
    """Create FastAPI application."""
    main_app = FastAPI(title="AI Legal Assistant", version="1.0.0")

    # Set up CORS middleware
    main_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception handler for validation error
    @main_app.exception_handler(RequestValidationError)
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
            status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "type": "validation_error",
                    "message": "Input data is not valid",
                    "fields": errors,
                }
            },
        )

    @main_app.middleware("http")
    async def track_metrics(request: Request, call_next):
        """Middleware to track metrics for each request."""
        start_time = time.time()
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000  # in milliseconds

        collector = get_metrics_collector()
        collector.record_request(
            endpoint=request.url.path,
            status_code=response.status_code,
            latency_ms=process_time,
            method=request.method,
        )

        return response

    # Include API routers (all_router is a list of APIRouter instances)
    for router in all_router:
        main_app.include_router(router, prefix="/api")

    @main_app.get("/")
    async def read_root():
        return {"message": "Welcome to the AI Legal Assistant API!"}

    return main_app


app = create_app()
