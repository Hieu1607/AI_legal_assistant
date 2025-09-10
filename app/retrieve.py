import os
import signal
import sys
import time

import fastapi
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(project_root))

from configs.logger import get_logger, setup_logging
from src.store_vector.search_embeddings import search_relevant_embeddings

setup_logging()
logger = get_logger(__name__)

router = APIRouter()


class QueryRequest(BaseModel):
    question: str
    top_k: int = Field(default=5, description="Number of top results to return", ge=1)


@router.post("/retrieve")
def retrieve_embeddings(request: QueryRequest):
    logger.info("The question is %s", request.question)
    logger.info("The number of returning chunks is %d", request.top_k)
    start_time = time.time()
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
        end_time = time.time()
        logger.info(f"All time: {start_time-end_time}")
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


def shutdown():
    os.kill(os.getpid(), signal.SIGTERM)
    return fastapi.Response(status_code=200, content="Server shutting down...")


@router.on_event("shutdown")
def on_shutdown():
    print("Server shutting down...")


router.add_api_route("/shutdown", shutdown, methods=["GET"])
