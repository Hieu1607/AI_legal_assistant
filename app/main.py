import os
import sys

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Set up logging
root = os.path.dirname(os.getcwd())
sys.path.insert(0, str(root))
from app.routers import rag, retrieve
from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

app = FastAPI()

app.include_router(retrieve.router)
app.include_router(rag.router)


@app.get("/")
def index():
    return {"Hello muhehehehe"}


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
