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
def make_embeddings(all_chunks, model_name="BAAI/bge-m3", batch_size=32):
    model = SentenceTransformer(model_name)
    logger.info("Done loading model")
    texts = [chunk["text"] for chunk in all_chunks]
    embeddings = model.encode(
        texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=True
    )  # Thêm thanh tiến trình để dễ theo dõi

    # 3. Gán embedding trở lại cho từng chunk
    result = []
    for i, current_chunk in enumerate(all_chunks):
        current_chunk["embedding"] = embeddings[i]
        result.append(current_chunk)

    logger.info("Done embedding all chunks")
    return result


if __name__ == "__main__":
    # Đọc dữ liệu gốc để lấy batch tiếp theo
    file_path = os.path.join(root, "data/processed/new_all_chunks.json")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        # data = data[1:20]
        all_embedded_chunks = make_embeddings(data)
        for chunk in all_embedded_chunks:
            if "embedding" in chunk and isinstance(chunk["embedding"], np.ndarray):
                chunk["embedding"] = chunk["embedding"].tolist()

    # Đọc file cũ để ghi tiếp
    saved_file_path = os.path.join(
        root, "data/processed/filtered_bge_embedded_chunks_with_local_model.json"
    )

    # Đọc dữ liệu cũ nếu file tồn tại
    existing_data = []
    if os.path.exists(saved_file_path):
        try:
            with open(saved_file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:  # Kiểm tra nếu file không trống
                    existing_data = json.loads(content)
                else:
                    logger.warning(
                        "File %s is empty, starting with empty data", saved_file_path
                    )
                    existing_data = []
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(
                "Failed to read JSON file %s: %s. Starting with empty data.",
                saved_file_path,
                e,
            )
            existing_data = []
        except (OSError, IOError) as e:
            logger.error(
                "Failed to read file %s: %s. Starting with empty data.",
                saved_file_path,
                e,
            )
            existing_data = []

    # Gộp dữ liệu cũ với dữ liệu mới
    combined_data = existing_data + all_embedded_chunks

    # Ghi lại file với dữ liệu gộp
    try:
        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(os.path.dirname(saved_file_path), exist_ok=True)

        with open(saved_file_path, "w", encoding="utf-8") as f:
            json.dump(combined_data, f, ensure_ascii=False, indent=4)
        logger.info("Done saving all. Total chunks: %d", len(combined_data))
    except (OSError, IOError) as e:
        logger.error("Failed to save file %s: %s", saved_file_path, e)
        raise
