import os
import signal
import sys

import fastapi
import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Set up logging
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(root))

from configs.logger import get_logger, setup_logging
from src.store_vector.search_embeddings import search_relevant_embeddings

setup_logging()
logger = get_logger(__name__)

app = FastAPI()


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


@app.get("/")
def index():
    return {"Hello muhehehehe"}


@app.post("/retrieve")
def retrieve_embeddings(request: QueryRequest):
    logger.info("The question is %s", request.question)
    logger.info("The number of returning chunks is %d", request.top_k)
    try:
        relevant_embeddings = search_relevant_embeddings(
            request.question, request.top_k
        )
        result = []
        for i, chunk_id in enumerate(relevant_embeddings["ids"][0]):
            data = {}
            data["chunk_id"] = chunk_id
            data["distance"] = relevant_embeddings["distances"][0][i]
            data["metadatas"] = relevant_embeddings["metadatas"][0][i]
            data["score"] = relevant_embeddings["cosine_similarities"][0][i]
            data["content"] = relevant_embeddings["documents"][0][i]
            result.append(data)
        if not result:
            return JSONResponse(status_code=200, content=[])
        logger.info("Found %s valid chunk", len(result))
        return result
    except (IndexError, KeyError, FileNotFoundError, ImportError, ValueError) as e:
        logger.info(
            "An error occurred during embedding retrieval: %s", e, exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "internal_error",
                    "message": "An error occurred while processing your request",
                }
            },
        )


# Exception handler for validation error
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    logger.info("An error occured: %s", exc.errors())
    errors = [
        {
            "field": ".".join(str(loc) for loc in err["loc"][1:]),  # remove 'body'
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


def shutdown():
    os.kill(os.getpid(), signal.SIGTERM)
    return fastapi.Response(status_code=200, content="Server shutting down...")


@app.on_event("shutdown")
def on_shutdown():
    print("Server shutting down...")


app.add_api_route("/shutdown", shutdown, methods=["GET"])

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8000)
