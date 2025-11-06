"""
Business logic for the Retrieval-Augmented Generation (RAG) service.
"""

import time
from http import HTTPStatus

import weaviate

from app.configs.logger import get_logger
from app.tools.cache_manager import RAGCacheManager, get_cache_manager
from app.tools.weaviate_search import WeaviateSearcher

logger = get_logger(__name__)


class RAGService:
    """Service for handling RAG operations."""

    async def process_query(
        self,
        question: str,
        searcher: WeaviateSearcher | None = None,
        cache_manager: RAGCacheManager | None = None,
    ) -> dict:
        """Process the RAG query and return response."""
        logger.info(f"Processing query: {question}")
        start_time = time.perf_counter()
        # Check cache first
        if cache_manager is None:
            cache_manager = await get_cache_manager()
        cached_response = await cache_manager.get(question)
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

        try:
            if searcher and await searcher.connect():
                result = await searcher.ask_question(question)
                await cache_manager.set(
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
            logger.error("WeaviateSearcher instance is None.")
            return {
                "answer": "Unable to process the question at this time.",
                "question": question,
                "relevant_chunks": [],
                "context_count": 0,
                "total_time": time.perf_counter() - start_time,
                "cached": False,
            }
        except TimeoutError as timeout_error:
            logger.error(f"Timeout error processing query: {timeout_error}")
            return {
                "answer": "The request timed out. Please try again later.",
                "question": question,
                "relevant_chunks": [],
                "context_count": 0,
                "total_time": time.perf_counter() - start_time,
                "cached": False,
            }

        except weaviate.exceptions.WeaviateConnectionError as conn_error:
            logger.error(f"Weaviate connection error: {conn_error}")
            return {
                "answer": "Failed to connect to the Weaviate server.",
                "question": question,
                "relevant_chunks": [],
                "context_count": 0,
                "total_time": time.perf_counter() - start_time,
                "cached": False,
            }
        except weaviate.exceptions.WeaviateQueryError as query_error:
            logger.error(f"Weaviate query error: {query_error}")
            return {
                "answer": "An error occurred while querying the Weaviate server.",
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
        finally:
            if searcher:
                await searcher.close()
