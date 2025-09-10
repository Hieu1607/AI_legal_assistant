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
    # print(f"Kiểm tra thư mục lưu trữ Chroma tại: {CHROMA_DB_PATH}")
    chroma_token = os.getenv("x-chromadb-token")
    if chroma_token is None:
        raise ValueError("Environment variable 'x-chromadb-token' is not set.")
    client = chromadb.HttpClient(
        ssl=True,
        host="api.trychroma.com",
        tenant="eacc7fce-0948-49c8-a52b-5ed4969db763",
        database="AI legal assistant ChromaDB",
        headers={"x-chroma-token": chroma_token},
    )
    logger.info("Client ChromaDB created successfully.")
    logger.info("Kiểm tra hoặc tạo collection: '%s'...", COLLECTION_NAME)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={
            "hnsw:space": "cosine",  # Độ đo cosine cho tìm kiếm văn bản
            "hnsw:construction_ef": 200,  # Tăng exploration khi xây dựng để đảm bảo độ chính xác cao
            "hnsw:M": 32,  # Tăng số kết nối để cải thiện chất lượng index
            "hnsw:search_ef": 50,  # Tăng exploration khi tìm kiếm để cân bằng tốc độ và độ chính xác
            "hnsw:num_threads": 8,  # Sử dụng 8 luồng để tăng tốc xử lý
            "hnsw:resize_factor": 1.5,  # Tỷ lệ tăng trưởng lớn để hỗ trợ mở rộng dữ liệu
            "hnsw:batch_size": 200,  # Batch size lớn hơn để xử lý dữ liệu nhanh
            "hnsw:sync_threshold": 1000,  # Đồng bộ sau mỗi 1000 vector để giảm I/O
        },
    )
    logger.info("Collection '%s' đã sẵn sàng.", COLLECTION_NAME)
    # print("\n--- Cấu hình Index của ChromaDB ---")
    # print(json.dumps(INDEX_CONFIG, indent=4, ensure_ascii=False))

    return client, collection


if __name__ == "__main__":
    chroma_client, legal_collection = init_chroma_index()
    print(f"Số lượng documents: {legal_collection.count()}")
    results = legal_collection.peek(limit=5)  # Lấy 5 item đầu tiên
    print(results)
