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


def index_embeddings(embeddings):
    collection = init_chroma_index()[1]
    ids = []
    documents_content = []
    metadatas = []
    embeddings_list = []
    for embedding in embeddings:
        ids.append(embedding["chunk_id"])
        documents_content.append(embedding["text"])
        metadata = {}
        metadata["title"] = embedding["title"]
        metadata["update_day"] = embedding["update_day"]
        metadata["date_of_issue"] = embedding["date_of_issue"]
        metadatas.append(metadata)
        embeddings_list.append(embedding["embedding"])
    if len(ids) == len(documents_content) == len(metadatas) == len(embeddings_list):
        collection.add(
            documents=documents_content,
            metadatas=metadatas,
            ids=ids,
            embeddings=embeddings_list,
        )


if __name__ == "__main__":
    file_path = os.path.join(
        root, "data/processed/sample_embedded_chunks_with_local_model.json"
    )
    with open(file_path, "r", encoding="utf-8") as f:
        datas = json.load(f)
        index_embeddings(datas)
