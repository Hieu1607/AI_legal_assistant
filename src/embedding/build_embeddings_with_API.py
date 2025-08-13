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
    Create embeddings for a list of chunks in batches.

    Args:
        all_chunks (list): List of dictionaries, each containing 'text' and other information.
        model (str): Name of the embedding model.
        batch_size (int): Maximum number of texts in each batch.
                          API limit for gemini-embedding-exp-03-07 is 250 sentences.

    Returns:
        list: List of dictionaries updated with 'embedding' field.
              Returns empty list if there are errors or no chunks.
    """
    genai.configure(api_key=os.getenv("Gemini_API_KEY"))  # type: ignore
    processed_chunks = []
    num_chunks = len(all_chunks)

    for i in range(0, num_chunks, batch_size):
        # Get a batch of chunks
        current_batch_chunks = all_chunks[i : i + batch_size]
        texts_to_embed = [chunk["text"] for chunk in current_batch_chunks]

        logger.info(
            "Processing batch from chunk %d to %d...",
            i,
            min(i + batch_size, num_chunks),
        )

        try:
            # Send embedding request for entire batch
            embedded_data = genai.embed_content(  # type: ignore
                model=model,
                content=texts_to_embed,
                task_type="RETRIEVAL_QUERY",  # Ensure task_type is appropriate for your purpose
            )

            # Check if embeddings are returned
            if embedded_data and "embedding" in embedded_data:
                embeddings_for_batch = embedded_data["embedding"]

                # Assign embedding back to each chunk in batch
                for j, current_chunk in enumerate(current_batch_chunks):
                    if j < len(
                        embeddings_for_batch
                    ):  # Ensure there are enough embeddings for chunk
                        current_chunk["embedding"] = embeddings_for_batch[j]
                        processed_chunks.append(current_chunk)
                    else:
                        print(
                            f"Warning: No embedding for chunk at position {j} in this batch."
                        )
            else:
                print(
                    f"Warning: API did not return embedding for batch from chunk {i}."
                )
            time.sleep(random.uniform(0.0, 2.0))  # Pause 100ms

        except (
            KeyError,
            TypeError,
            GoogleAPICallError,
        ) as e:
            print(f"Error processing batch from chunk {i}: {e}")
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
