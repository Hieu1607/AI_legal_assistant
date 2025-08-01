import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()


root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
