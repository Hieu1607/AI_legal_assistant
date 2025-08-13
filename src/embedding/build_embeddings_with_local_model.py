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
    # Read original data to get next batch
    file_path = os.path.join(root, "data/processed/all_chunks.json")
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        data = data[3000:27061]  # Get next 1000 data points (index 1000-1999)
        all_embedded_chunks = make_embeddings(data)
        for chunk in all_embedded_chunks:
            if "embedding" in chunk and isinstance(chunk["embedding"], np.ndarray):
                chunk["embedding"] = chunk["embedding"].tolist()

    # Read old file to append to
    saved_file_path = os.path.join(
        root, "data/processed/embedded_chunks_with_local_model.json"
    )

    # Read old data if file exists
    existing_data = []
    if os.path.exists(saved_file_path):
        with open(saved_file_path, "r", encoding="utf-8") as f:
            existing_data = json.load(f)

    # Merge old data with new data
    combined_data = existing_data + all_embedded_chunks

    # Write file with merged data
    with open(saved_file_path, "w", encoding="utf-8") as f:
        json.dump(combined_data, f, ensure_ascii=False, indent=4)
        logger.info("Done saving all. Total chunks: %d", len(combined_data))
