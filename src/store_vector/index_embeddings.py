import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()


# Get the root directory of the project
current_dir = os.path.dirname(os.path.abspath(__file__))
while True:
    # Check if 'data' and 'src' directories exist in current directory
    if os.path.isdir(os.path.join(current_dir, "data")) and os.path.isdir(
        os.path.join(current_dir, "src")
    ):
        root = current_dir
        break

    parent_dir = os.path.dirname(current_dir)
    if parent_dir == current_dir:  # Reached system root directory
        raise FileNotFoundError(
            "Check the project structure. 'data' and 'src' directories not found."
        )
    current_dir = parent_dir

# Set up logging
sys.path.insert(0, str(root))

from configs.logger import get_logger, setup_logging
from src.store_vector.init_index import init_chroma_index

setup_logging()
logger = get_logger(__name__)


def index_embeddings(embeddings, batch_size=64):
    """
    Index embeddings into ChromaDB collection in batches for better memory management.
    
    Args:
        embeddings: List of embedding dictionaries
        batch_size: Number of embeddings to process in each batch (default: 64)
    """
    collection = init_chroma_index()[1]
    total_embeddings = len(embeddings)
    
    logger.info(f"Starting to index {total_embeddings} embeddings in batches of {batch_size}")
    
    # Process embeddings in batches
    for i in range(0, total_embeddings, batch_size):
        batch_end = min(i + batch_size, total_embeddings)
        batch_embeddings = embeddings[i:batch_end]
        
        # Prepare batch data
        ids = []
        documents_content = []
        metadatas = []
        embeddings_list = []
        
        for embedding in batch_embeddings:
            ids.append(embedding["chunk_id"])
            documents_content.append(embedding["text"])
            metadata = {
                "title": embedding["title"],
                "update_day": embedding["update_day"],
                "date_of_issue": embedding["date_of_issue"]
            }
            metadatas.append(metadata)
            embeddings_list.append(embedding["embedding"])
        
        # Validate batch data consistency
        if len(ids) == len(documents_content) == len(metadatas) == len(embeddings_list):
            try:
                collection.add(
                    documents=documents_content,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings_list,
                )
                logger.info(f"Successfully indexed batch {i//batch_size + 1}/{(total_embeddings-1)//batch_size + 1} "
                           f"(embeddings {i+1}-{batch_end})")
            except Exception as e:
                logger.error(f"Error indexing batch {i//batch_size + 1}: {str(e)}")
                raise
        else:
            error_msg = f"Data consistency error in batch {i//batch_size + 1}: " \
                       f"ids={len(ids)}, documents={len(documents_content)}, " \
                       f"metadatas={len(metadatas)}, embeddings={len(embeddings_list)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    logger.info(f"Completed indexing all {total_embeddings} embeddings")


if __name__ == "__main__":
    file_path = os.path.join(
        root, "data/processed/bge_m3_embeddings_merged_20251007_065728.json"
    )
    with open(file_path, "r", encoding="utf-8") as f:
        datas = json.load(f)
        logger.info(f"Loaded {len(datas)} embeddings from {file_path}")
        index_embeddings(datas, batch_size=64)
