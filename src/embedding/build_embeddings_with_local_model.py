import json
import os
import sys

import numpy as np
from sentence_transformers import SentenceTransformer

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))

from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


# Because the time for loading the model is quite long, so we dont seperate the function for each sentence.
def make_embeddings(all_chunks, model="BAAI/bge-m3"):
    model = SentenceTransformer(model)
    logger.info("Done loading model")
    result = []
    for current_chunk in all_chunks:
        current_chunk["embedding"] = model.encode(
            current_chunk["text"], normalize_embeddings=True
        )
        result.append(current_chunk)
    logger.info("Done embedding all chunks")
    return result


if __name__ == "__main__":
    # Đọc dữ liệu gốc để lấy batch tiếp theo
    file_path = os.path.join(root, "data/processed/all_chunks.json")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        data = data[3000:27061]  # Lấy 1000 dữ liệu tiếp theo (index 1000-1999)
        all_embedded_chunks = make_embeddings(data)
        for chunk in all_embedded_chunks:
            if "embedding" in chunk and isinstance(chunk["embedding"], np.ndarray):
                chunk["embedding"] = chunk["embedding"].tolist()

    # Đọc file cũ để ghi tiếp
    saved_file_path = os.path.join(
        root, "data/processed/embedded_chunks_with_local_model.json"
    )

    # Đọc dữ liệu cũ nếu file tồn tại
    existing_data = []
    if os.path.exists(saved_file_path):
        with open(saved_file_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)

    # Gộp dữ liệu cũ với dữ liệu mới
    combined_data = existing_data + all_embedded_chunks

    # Ghi lại file với dữ liệu gộp
    with open(saved_file_path, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=4)
        logger.info("Done saving all. Total chunks: %d", len(combined_data))
