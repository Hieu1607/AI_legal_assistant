import json
import os
import random
import sys
import time

import google.generativeai as genai
import numpy as np
from dotenv import load_dotenv
from google.api_core.exceptions import GoogleAPICallError

load_dotenv()


root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

sys.path.insert(0, str(root))

from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def make_embeddings(all_chunks, model="models/embedding-001", batch_size=100):
    """
    Tạo embeddings cho một danh sách các chunks theo từng batch.

    Args:
        all_chunks (list): Danh sách các dictionary, mỗi dictionary chứa 'text' và các thông tin khác.
        model (str): Tên của mô hình embedding.
        batch_size (int): Số lượng văn bản tối đa trong mỗi batch.
                          Giới hạn API cho gemini-embedding-exp-03-07 là 250 câu.

    Returns:
        list: Danh sách các dictionary đã được cập nhật thêm trường 'embedding'.
              Trả về danh sách rỗng nếu có lỗi hoặc không có chunks nào.
    """
    genai.configure(api_key=os.getenv("Gemini_API_KEY"))  # type: ignore
    processed_chunks = []
    num_chunks = len(all_chunks)

    for i in range(0, num_chunks, batch_size):
        # Get a batch of chunks
        current_batch_chunks = all_chunks[i : i + batch_size]
        texts_to_embed = [chunk["text"] for chunk in current_batch_chunks]

        logger.info(
            "Đang xử lý batch từ chunk %d đến %d...", i, min(i + batch_size, num_chunks)
        )

        try:
            # Gửi yêu cầu embedding cho toàn bộ batch
            embedded_data = genai.embed_content(  # type: ignore
                model=model,
                content=texts_to_embed,
                task_type="RETRIEVAL_QUERY",  # Đảm bảo task_type phù hợp với mục đích của bạn
            )

            # Kiểm tra xem có embeddings được trả về không
            if embedded_data and "embedding" in embedded_data:
                embeddings_for_batch = embedded_data["embedding"]

                # Gán embedding trở lại cho từng chunk trong batch
                for j, current_chunk in enumerate(current_batch_chunks):
                    if j < len(
                        embeddings_for_batch
                    ):  # Đảm bảo có đủ embedding cho chunk
                        current_chunk["embedding"] = embeddings_for_batch[j]
                        processed_chunks.append(current_chunk)
                    else:
                        print(
                            f"Cảnh báo: Không có embedding cho chunk tại vị trí {j} trong batch này."
                        )
            else:
                print(f"Cảnh báo: API không trả về embedding cho batch từ chunk {i}.")
            time.sleep(random.uniform(0.0, 2.0))  # Dừng 100ms

        except (
            KeyError,
            TypeError,
            GoogleAPICallError,
        ) as e:
            print(f"Lỗi khi xử lý batch từ chunk {i}: {e}")
            continue
    return processed_chunks


if __name__ == "__main__":
    file_path = os.path.join(root, "data/processed/all_chunks.json")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        sample_100_chunks = random.sample(data, 100)
        all_embedded_chunks = make_embeddings(sample_100_chunks)
        for chunk in all_embedded_chunks:
            if "embedding" in chunk and isinstance(chunk["embedding"], np.ndarray):
                chunk["embedding"] = chunk["embedding"].tolist()
    saved_file_path = os.path.join(
        root, "data/processed/sample_embedded_chunks_with_API.json"
    )
    with open(saved_file_path, "w", encoding="utf-8") as f:
        json.dump(all_embedded_chunks, f, ensure_ascii=False, indent=4)
        logger.info("Done saving file")
