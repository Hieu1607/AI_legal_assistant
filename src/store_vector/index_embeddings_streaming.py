import json
import os
import sys
import time
from decimal import Decimal
from typing import Any, Dict, Generator

try:
    import ijson
except ImportError:
    print("ijson not installed. Installing...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "ijson"])
    import ijson

from dotenv import load_dotenv

load_dotenv()

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))

from configs.logger import get_logger, setup_logging
from src.store_vector.init_index import init_chroma_index

setup_logging()
logger = get_logger(__name__)


def stream_embeddings_from_json(
    file_path: str,
) -> Generator[Dict[str, Any], None, None]:
    logger.info("Starting to stream embeddings from %s", file_path)
    with open(file_path, "rb") as f:
        parser = ijson.items(f, "item")  # Sửa thành 'data.item' nếu JSON bọc trong dict

        count = 0
        for embedding in parser:
            count += 1
            if count % 1000 == 0:
                logger.info("Streamed %s embeddings so far...", count)
            yield embedding

        logger.info("Finished streaming total %s embeddings", count)


def index_embeddings_streaming(file_path: str, batch_size: int = 3000):
    collection = init_chroma_index()[1]
    id_counter = {}
    batch_embeddings = []
    batch_count = 0
    total_processed = 0

    logger.info("Starting streaming indexing with batch size %s", batch_size)

    for embedding in stream_embeddings_from_json(file_path):
        required_keys = [
            "chunk_id",
            "text",
            "title",
            "update_day",
            "date_of_issue",
            "embedding",
        ]
        if not all(k in embedding for k in required_keys):
            logger.warning("Skipping embedding with missing keys: %s", embedding)
            continue

        batch_embeddings.append(embedding)

        if len(batch_embeddings) >= batch_size:
            batch_count += 1
            total_processed += len(batch_embeddings)

            logger.info(
                "Processing batch %s with %s embeddings",
                batch_count,
                len(batch_embeddings),
            )
            process_batch(collection, batch_embeddings, id_counter, batch_count)

            batch_embeddings = []

    if batch_embeddings:
        batch_count += 1
        total_processed += len(batch_embeddings)
        logger.info(
            "Processing final batch %s with %s embeddings",
            batch_count,
            len(batch_embeddings),
        )
        process_batch(collection, batch_embeddings, id_counter, batch_count)

    logger.info(
        "Completed streaming indexing. Total processed: %s embeddings in %s batches",
        total_processed,
        batch_count,
    )


def process_batch(collection, batch_embeddings, id_counter, batch_num):
    ids = []
    documents_content = []
    metadatas = []
    embeddings_list = []

    for embedding in batch_embeddings:
        chunk_id = embedding["chunk_id"]

        if chunk_id in id_counter:
            id_counter[chunk_id] += 1
            unique_id = f"{chunk_id}_{id_counter[chunk_id]}"
            logger.debug(
                "Duplicate ID found: %s, using %s instead", chunk_id, unique_id
            )
        else:
            id_counter[chunk_id] = 0
            unique_id = chunk_id

        ids.append(unique_id)
        documents_content.append(embedding["text"])
        metadatas.append(
            {
                "title": embedding["title"],
                "update_day": embedding["update_day"],
                "date_of_issue": embedding["date_of_issue"],
            }
        )

        # Convert Decimal to float
        vector = embedding["embedding"]
        vector = [float(v) if isinstance(v, Decimal) else v for v in vector]
        embeddings_list.append(vector)

    if len(ids) == len(documents_content) == len(metadatas) == len(embeddings_list):
        logger.info(
            "Adding batch %s with %s embeddings to collection", batch_num, len(ids)
        )
        collection.add(
            documents=documents_content,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings_list,
        )
        logger.info("Successfully added batch %s", batch_num)
    else:
        logger.error(
            "Mismatch in batch data lengths: ids=%s, docs=%s, metadata=%s, embeddings=%s",
            len(ids),
            len(documents_content),
            len(metadatas),
            len(embeddings_list),
        )


if __name__ == "__main__":
    try:
        start_time = time.time()

        file_path = os.path.join(
            root, "data/processed/filtered_bge_embedded_chunks_with_local_model.json"
        )

        logger.info("Starting streaming indexing from %s", file_path)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size = os.path.getsize(file_path)
        logger.info("File size: %.2f MB", file_size / (1024 * 1024))

        index_embeddings_streaming(file_path, batch_size=3000)

        elapsed_time = time.time() - start_time
        logger.info(
            "Successfully completed streaming indexing in %.2f seconds", elapsed_time
        )

    except FileNotFoundError as e:
        logger.error("File not found: %s", e, exc_info=True)
    except json.JSONDecodeError as e:
        logger.error("JSON decode error: %s", e, exc_info=True)
    except OSError as e:
        logger.error("OS error during streaming indexing: %s", e, exc_info=True)
    except ValueError as e:
        logger.error("Value error during streaming indexing: %s", e, exc_info=True)
    except RuntimeError as e:
        logger.error("Runtime error during streaming indexing: %s", e, exc_info=True)
