import os
import sys
import time

from dotenv import load_dotenv
from gradio_client import Client

load_dotenv()

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))

from configs.logger import get_logger, setup_logging
from src.store_vector.init_index import init_chroma_index

setup_logging()
logger = get_logger(__name__)
collection = init_chroma_index()[1]

# Cấu hình API embedding
EMBEDDING_API_ENDPOINT = "hieuailearning/BAAI_bge_m3_api"

# Backup models configuration for reference (không sử dụng nữa)
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


def search_relevant_embeddings(text, n_results=5, model_name=None):
    """
    Search for relevant embeddings using API-based embedding.

    Args:
        text (str): Query text
        n_results (int): Number of results to return
        model_name (str): Deprecated, kept for compatibility

    Returns:
        dict: Search results with cosine similarities
    """
    start_time = time.time()

    # Get embedding from API
    embedding_from_text = get_embedding_from_api(text)

    start_query_time = time.time()
    results = collection.query(
        query_embeddings=embedding_from_text,
        n_results=n_results,
        # where={"source": "article"},        # Tùy chọn: Lọc theo metadata (AND logic)
        # where_document={"$contains":"leave"} # Tùy chọn: Lọc theo nội dung document
    )
    end_query_time = time.time()

    # Tính cosine similarity từ distances (ChromaDB trả về cosine distances)
    # Cosine similarity = 1 - cosine distance
    logger.info(
        "Time to run with retrieving is %f",
        float(end_query_time - start_query_time),
    )
    cosine_similarities = []
    if results["distances"] and len(results["distances"][0]) > 0:
        cosine_similarities = [1 - distance for distance in results["distances"][0]]
    # Tạo dictionary mới với cosine similarities
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


if __name__ == "__main__":
    test_text = "Chương I điều 2 bộ luật hình sự."

    # Test với API embedding
    print("=== Testing with API embedding ===")
    res = search_relevant_embeddings(test_text, 5)

    # Test với text khác để kiểm tra API
    print("\n=== Testing with different text ===")
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
