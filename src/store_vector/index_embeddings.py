import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def get_project_root():
    """Get the root directory of the project."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while True:
        # Kiểm tra xem 'data' và 'src' có tồn tại trong thư mục hiện tại không
        if os.path.isdir(os.path.join(current_dir, "data")) and os.path.isdir(
            os.path.join(current_dir, "src")
        ):
            return current_dir

        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Đã đến thư mục gốc của hệ thống
            raise FileNotFoundError(
                "Check the project structure. 'data' and 'src' directories not found."
            )
        current_dir = parent_dir


# Set up logging
root = get_project_root()
sys.path.insert(0, str(root))

from configs.logger import get_logger, setup_logging
from src.store_vector.init_index import init_chroma_index

setup_logging()
logger = get_logger(__name__)


def index_embeddings(embeddings, batch_size=5000):
    """
    Index embeddings to ChromaDB in batches to avoid exceeding the max batch size limit.

    Args:
        embeddings (list): List of embeddings to index
        batch_size (int): Size of batches to process at once, default to 5000 (under ChromaDB's limit of 5461)
    """
    collection = init_chroma_index()[1]

    # Create a dictionary to keep track of seen IDs and their counts
    id_counter = {}

    # Process embeddings in batches
    total_embeddings = len(embeddings)
    total_batches = (
        total_embeddings + batch_size - 1
    ) // batch_size  # Ceiling division

    logger.info(
        "Processing %s embeddings in %s batches of %s",
        total_embeddings,
        total_batches,
        batch_size,
    )

    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min((batch_num + 1) * batch_size, total_embeddings)

        batch_embeddings = embeddings[start_idx:end_idx]

        ids = []
        documents_content = []
        metadatas = []
        embeddings_list = []

        for embedding in batch_embeddings:
            chunk_id = embedding["chunk_id"]

            # If the ID already exists, append a counter to it
            if chunk_id in id_counter:
                id_counter[chunk_id] += 1
                unique_id = ("%s_%s", chunk_id, id_counter[chunk_id])
                logger.info(
                    "Duplicate ID found: %s, using %s instead", chunk_id, unique_id
                )
            else:
                id_counter[chunk_id] = 0
                unique_id = chunk_id

            ids.append(unique_id)
            documents_content.append(embedding["text"])
            metadata = {}
            metadata["title"] = embedding["title"]
            metadata["update_day"] = embedding["update_day"]
            metadata["date_of_issue"] = embedding["date_of_issue"]
            metadatas.append(metadata)
            embeddings_list.append(embedding["embedding"])

        if len(ids) == len(documents_content) == len(metadatas) == len(embeddings_list):
            logger.info(
                "Adding batch %s/%s with %s embeddings to collection",
                batch_num + 1,
                total_batches,
                len(ids),
            )
            collection.add(
                documents=documents_content,
                metadatas=metadatas,
                ids=ids,
                embeddings=embeddings_list,
            )
            logger.info("Successfully added batch %s/%s", batch_num + 1, total_batches)


if __name__ == "__main__":
    try:
        import time

        start_time = time.time()

        file_path = os.path.join(
            root, "data/processed/embedded_chunks_with_local_model.json"
        )
        logger.info("Loading embeddings from %s", file_path)
        with open(file_path, "r", encoding="utf-8") as f:
            datas = json.load(f)
            logger.info("Loaded %s embeddings", len(datas))

            # Specify a batch size that's safely under ChromaDB's limit (which is 5461)
            batch_size = 5000
            index_embeddings(datas, batch_size=batch_size)

            elapsed_time = time.time() - start_time
            logger.info(
                "Successfully indexed all %s embeddings in %.2f seconds",
                len(datas),
                elapsed_time,
            )
    except FileNotFoundError as e:
        logger.error("File not found: %s", e, exc_info=True)
        import traceback

        logger.error("Traceback: %s", traceback.format_exc())
    except json.JSONDecodeError as e:
        logger.error("JSON decode error: %s", e, exc_info=True)
        import traceback

        logger.error("Traceback: %s", traceback.format_exc())
    except OSError as e:
        logger.error("OS error indexing embeddings: %s", e, exc_info=True)
        import traceback

        logger.error("Traceback: %s", traceback.format_exc())
