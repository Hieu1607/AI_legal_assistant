"""
Business logic for the Retrieval-Augmented Generation (RAG) service.
"""

import os
import sys
import time

from dotenv import load_dotenv

from app.tools.weaviate_search import get_searcher

load_dotenv()

# root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# if root not in sys.path:
#     sys.path.append(root)
from app.configs.logger import get_logger, setup_logging
from app.tools.cache_manager import get_cache_manager

setup_logging()
logger = get_logger(__name__)

# Initialize cache manager
_cache_manager = get_cache_manager(
    ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", 3600)),
    max_size=int(os.getenv("CACHE_MAX_SIZE", 1000)),
)


class RAGService:
    """Service for handling RAG operations."""

    def __init__(self):
        # Initialize any required components, e.g., vector store, LLM, etc.
        pass

    async def process_query(self, question: str):
        """Process the RAG query and return response."""
        logger.info(f"Processing query: {question}")
        start_time = time.perf_counter()
        # Check cache first
        cached_response = _cache_manager.get(question)
        if cached_response:
            answer, original_question, context_count = cached_response
            cache_time = time.perf_counter() - start_time
            logger.info(f"Cache hit for question: {question} (time: {cache_time:.4f}s)")
            return {
                "answer": answer,
                "question": original_question,
                "context_count": context_count,
                "relevant_chunks": [],
                "total_time": cache_time,
                "cached": True,
            }

        logger.info(f"Cache miss for question: {question}")

        searcher = None

        try:
            searcher = get_searcher()
            if searcher:
                result = searcher.ask_question(question)
                _cache_manager.set(
                    question, str(result["answer"]), len(result["relevant_chunks"])
                )
                total_time = time.perf_counter() - start_time
                logger.info(f"Processed query in {total_time:.4f}s")
                return {
                    "answer": result["answer"].strip(),
                    "question": question,
                    "relevant_chunks": result["relevant_chunks"],
                    "context_count": len(result["relevant_chunks"]),
                    "total_time": total_time,
                    "cached": False,
                }
            else:
                logger.error("WeaviateSearcher instance is None.")
                return {
                    "answer": "Unable to process the question at this time.",
                    "question": question,
                    "relevant_chunks": [],
                    "context_count": 0,
                    "total_time": time.perf_counter() - start_time,
                    "cached": False,
                }
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return {
                "answer": "Đã xảy ra lỗi khi xử lý câu hỏi. Vui lòng thử lại.",
                "question": question,
                "relevant_chunks": [],
                "context_count": 0,
                "total_time": time.perf_counter() - start_time,
                "cached": False,
            }
