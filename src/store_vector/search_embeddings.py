import os
import sys
import time

from dotenv import load_dotenv
from gradio_client import Client

load_dotenv()

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))

from configs.logger import get_logger, setup_logging
from services.metrics import CHROMADB_EXCEPTIONS, HF_EMBEDDINGS_EXCEPTIONS
from src.store_vector.init_index import init_chroma_index

setup_logging()
logger = get_logger(__name__)
collection = init_chroma_index()[1]

# API embedding configuration
EMBEDDING_API_ENDPOINT = "hieuailearning/BAAI_bge_m3_api"

# Backup models configuration for reference (no longer used)
# DEFAULT_MODEL = "BAAI/bge-m3"
# ALTERNATIVE_MODELS = {
#     "vietnamese": "keepitreal/vietnamese-sbert",
#     "multilingual": "paraphrase-multilingual-MiniLM-L12-v2",
#     "fast": "all-MiniLM-L6-v2",
#     "quality": "all-mpnet-base-v2",
#     "lightweight": "distiluse-base-multilingual-cased",
# }


def get_embedding_from_api(text, max_retries=3, timeout=30):
    """
    Get embedding from Gradio API endpoint with retry logic.

    Args:
        text (str): Input text to embed
        max_retries (int): Maximum number of retry attempts
        timeout (int): Request timeout in seconds

    Returns:
        list: Embedding vector

    Raises:
        Exception: If all retry attempts fail
    """
    import time

    for attempt in range(max_retries):
        try:
            client = Client(EMBEDDING_API_ENDPOINT)
            embedding = client.predict(text_input=text, api_name="/predict")
            logger.info(
                "Successfully got embedding from API (attempt %d) for text length: %d",
                attempt + 1,
                len(text),
            )
            return embedding

        except Exception as e:
            HF_EMBEDDINGS_EXCEPTIONS.labels(model=EMBEDDING_API_ENDPOINT).inc()
            logger.warning(
                "Attempt %d failed to get embedding from API: %s", attempt + 1, str(e)
            )

            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 1  # Exponential backoff: 1s, 2s, 3s
                logger.info("Retrying in %d seconds...", wait_time)
                time.sleep(wait_time)
            else:
                logger.error(
                    "All %d attempts failed to get embedding from API", max_retries
                )
                raise Exception(
                    f"Failed to get embedding after {max_retries} attempts: {str(e)}"
                )


def search_relevant_embeddings(text, n_results=5, model_name=None, title=None):
    """
    Search for relevant embeddings using API-based embedding.

    Args:
        text (str): Query text
        n_results (int): Number of results to return
        model_name (str): Deprecated, kept for compatibility
        title (str): Optional title to filter by metadata. If None, search without metadata filter

    Returns:
        dict: Search results with cosine similarities
    """
    start_time = time.time()

    # Get embedding from API
    embedding_from_text = get_embedding_from_api(text)

    start_query_time = time.time()
    try:
        # Prepare query parameters
        query_params = {
            "query_embeddings": embedding_from_text,
            "n_results": n_results,
        }

        # Add metadata filter if title is provided
        if title:
            query_params["where"] = {"title": title}
            logger.info("Searching with metadata filter - title: %s", title)
        else:
            logger.info("Searching without metadata filter")

        results = collection.query(**query_params)
    except Exception as e:
        CHROMADB_EXCEPTIONS.labels(operation="query").inc()
        logger.error("ChromaDB query failed: %s", str(e))
        raise e
    end_query_time = time.time()

    # Calculate cosine similarity from distances (ChromaDB returns cosine distances)
    # Cosine similarity = 1 - cosine distance
    logger.info(
        "Time to run with retrieving is %f",
        float(end_query_time - start_query_time),
    )
    cosine_similarities = []
    if results["distances"] and len(results["distances"][0]) > 0:
        cosine_similarities = [1 - distance for distance in results["distances"][0]]
    # Create new dictionary with cosine similarities
    enhanced_results = {
        "ids": results["ids"],
        "distances": results["distances"],
        "metadatas": results["metadatas"],
        "documents": results["documents"],
        "embeddings": results["embeddings"],
        "cosine_similarities": [cosine_similarities],
    }
    end_time = time.time()
    logger.info("Time to run search_embeddings is %f", float(end_time - start_time))
    return enhanced_results


def batch_search_relevant_embeddings(queries_and_titles, n_results=5):
    """
    Batch search for multiple queries with their corresponding title filters.
    This is more efficient than individual searches as it reduces API calls for embeddings.

    Args:
        queries_and_titles (list): List of tuples (query_text, title), where title can be None
        n_results (int): Number of results to return per query

    Returns:
        list: List of search results, same order as input queries
    """
    start_time = time.time()

    if not queries_and_titles:
        return []

    # Extract unique queries to minimize embedding API calls
    unique_queries = {}
    query_embeddings = {}

    for query_text, title in queries_and_titles:
        if query_text not in unique_queries:
            unique_queries[query_text] = True

    # Get embeddings for all unique queries
    logger.info(
        "Getting embeddings for %d unique queries in batch", len(unique_queries)
    )

    for query_text in unique_queries.keys():
        try:
            query_embeddings[query_text] = get_embedding_from_api(query_text)
        except Exception as e:
            logger.error(
                "Failed to get embedding for query '%s': %s", query_text, str(e)
            )
            query_embeddings[query_text] = None

    # Perform searches for each query-title combination
    results = []
    start_query_time = time.time()

    for query_text, title in queries_and_titles:
        if query_embeddings[query_text] is None:
            # Return empty result for failed embedding
            empty_result = {
                "ids": [[]],
                "distances": [[]],
                "metadatas": [[]],
                "documents": [[]],
                "embeddings": [[]],
                "cosine_similarities": [[]],
            }
            results.append(empty_result)
            continue

        try:
            # Prepare query parameters
            query_params = {
                "query_embeddings": query_embeddings[query_text],
                "n_results": n_results,
            }

            # Add metadata filter if title is provided
            if title:
                query_params["where"] = {"title": title}

            search_result = collection.query(**query_params)

            # Calculate cosine similarities
            cosine_similarities = []
            if search_result["distances"] and len(search_result["distances"][0]) > 0:
                cosine_similarities = [
                    1 - distance for distance in search_result["distances"][0]
                ]

            # Create enhanced result
            enhanced_result = {
                "ids": search_result["ids"],
                "distances": search_result["distances"],
                "metadatas": search_result["metadatas"],
                "documents": search_result["documents"],
                "embeddings": search_result["embeddings"],
                "cosine_similarities": [cosine_similarities],
            }
            results.append(enhanced_result)

        except Exception as e:
            CHROMADB_EXCEPTIONS.labels(operation="query").inc()
            logger.error(
                "ChromaDB batch query failed for query '%s' with title '%s': %s",
                query_text,
                title,
                str(e),
            )
            # Return empty result for failed query
            empty_result = {
                "ids": [[]],
                "distances": [[]],
                "metadatas": [[]],
                "documents": [[]],
                "embeddings": [[]],
                "cosine_similarities": [[]],
            }
            results.append(empty_result)

    end_time = time.time()
    logger.info(
        "Batch search completed for %d queries in %.4f seconds",
        len(queries_and_titles),
        end_time - start_time,
    )
    logger.info("Query execution time: %.4f seconds", end_time - start_query_time)

    return results


if __name__ == "__main__":
    test_text = "Chương I điều 2 bộ luật hình sự."

    # Test with API embedding (no title filter)
    print("=== Testing with API embedding (no title filter) ===")
    res = search_relevant_embeddings(test_text, 5)

    # Test with title filter
    print("\n=== Testing with title filter ===")
    try:
        res_with_title = search_relevant_embeddings(
            test_text, 5, title="Bộ luật Hình sự"
        )
        print("API embedding test with title filter successful")
    except Exception as e:
        print(f"API embedding test with title filter failed: {e}")
        res_with_title = res

    # Test with different text to check API
    print("\n=== Testing with different text (no title filter) ===")
    try:
        res_vn = search_relevant_embeddings("Điều 3 Luật Hình sự quy định gì?", 5)
        print("API embedding test 2 successful")
    except Exception as e:
        print(f"API embedding test 2 failed: {e}")
        res_vn = res

    if res["documents"] and len(res["documents"][0]) > 0:
        print("Documents:")
        for i, doc in enumerate(res["documents"][0]):
            print(f"  {i+1}. {doc[:100]}...")

        print("\nCosine Similarities:")
        for i, score in enumerate(res["cosine_similarities"][0]):
            print(f"  {i+1}. {score:.4f}")
    else:
        print("No documents found.")
