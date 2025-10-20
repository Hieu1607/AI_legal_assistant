"""
Business logic for embedding retrieval operations
"""

import os
import sys

# Set up logging
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))

from configs.logger import get_logger, setup_logging
from src.store_vector.weaviate_search import search_relevant_embeddings

setup_logging()
logger = get_logger(__name__)


def retrieve_embeddings_logic(question: str, top_k: int):
    """
    Core logic for retrieving relevant embeddings

    Args:
        question (str): The search query
        top_k (int): Number of top results to return

    Returns:
        list: List of relevant chunks with metadata

    Raises:
        Exception: Various exceptions related to embedding retrieval
    """
    logger.info("The question is %s", question)
    logger.info("The number of returning chunks is %d", top_k)

    relevant_embeddings = search_relevant_embeddings(question, top_k)
    result = []

    for i, chunk_id in enumerate(relevant_embeddings["ids"][0]):
        data = {}
        data["chunk_id"] = chunk_id
        data["distance"] = relevant_embeddings["distances"][0][i]
        data["metadatas"] = relevant_embeddings["metadatas"][0][i]
        data["score"] = relevant_embeddings["cosine_similarities"][0][i]
        data["content"] = relevant_embeddings["documents"][0][i]

        # Extract title and other metadata for display
        metadata = relevant_embeddings["metadatas"][0][i]
        data["title"] = metadata.get("title", "Không có tiêu đề")
        data["date_of_issue"] = metadata.get("date_of_issue", "")
        data["update_day"] = metadata.get("update_day", "")

        result.append(data)

    if result:
        logger.info("Found %s valid chunk", len(result))

    return result
