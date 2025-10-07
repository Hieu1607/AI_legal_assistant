import os
import sys

import chromadb
from dotenv import load_dotenv

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))
load_dotenv()
from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

CHROMA_DB_PATH = os.path.join(root, "data/processed/vector_store")
COLLECTION_NAME = "legal_assistant_collection"
INDEX_CONFIG = {
    "collection_name": COLLECTION_NAME,
    "db_path": CHROMA_DB_PATH,
    "notes": "ChromaDB tự động quản lý dimension và sử dụng Cosine Similarity mặc định. "
    "Dimension sẽ được suy luận khi vector đầu tiên được thêm vào. "
    "Để đảm bảo collection được khởi tạo với dimension mong muốn, "
    "chúng ta có thể thêm một vector placeholder hoặc đảm bảo vector đầu tiên có đúng kích thước.",
}


def init_chroma_index():
    # print(f"Check Chroma storage directory at: {CHROMA_DB_PATH}")
    chroma_token = os.getenv("x-chromadb-token")
    if chroma_token is None:
        raise ValueError("Environment variable 'x-chromadb-token' is not set.")
    client = chromadb.CloudClient(
        api_key="ck-AUYSBFn4sdFQx19yBiMFrDNJ2m8xp6FHLWRrR5pQvPs4",
        tenant="d40f9c23-a637-4bf6-9608-d5b48b5dc739",
        database="AI legal assistant",
    )
    logger.info("Client ChromaDB created successfully.")
    logger.info("Kiểm tra hoặc tạo collection: '%s'...", COLLECTION_NAME)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "hnsw:space": "cosine",  # Cosine metric for text search
            "hnsw:construction_ef": 200,  # Increase exploration during construction for high accuracy
            "hnsw:M": 32,  # Increase connections to improve index quality
            "hnsw:search_ef": 50,  # Increase exploration during search to balance speed and accuracy
            "hnsw:num_threads": 8,  # Use 8 threads to speed up processing
            "hnsw:resize_factor": 1.5,  # Large growth ratio to support data expansion
            "hnsw:batch_size": 200,  # Larger batch size for faster data processing
            "hnsw:sync_threshold": 1000,  # Sync after every 1000 vectors to reduce I/O
        },
    )
    logger.info("Collection '%s' đã sẵn sàng.", COLLECTION_NAME)
    # print("\n--- ChromaDB Index Configuration ---")
    # print(json.dumps(INDEX_CONFIG, indent=4, ensure_ascii=False))

    return client, collection


if __name__ == "__main__":
    chroma_client, legal_collection = init_chroma_index()
    print(f"Số lượng documents: {legal_collection.count()}")
    results = legal_collection.peek(limit=5)  # Get first 5 items
    print(results)
