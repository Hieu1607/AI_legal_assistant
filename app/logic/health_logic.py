import os
import sys

import google.generativeai as genai
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download

# Load environment variables and configure Gemini API
load_dotenv()
genai.configure(api_key=os.getenv("Gemini_API_KEY"))  # type: ignore

# Set up logging
project_root = os.path.dirname(os.getcwd())
sys.path.insert(0, str(project_root))
from configs.logger import get_logger, setup_logging
from src.store_vector.init_index import init_chroma_index

setup_logging()
logger = get_logger(__name__)


def health_check():
    # Check HuggingFace model availability
    hf_hub_download(
        repo_id="BAAI/bge-m3", filename="config.json", local_files_only=True
    )

    # Check ChromaDB collection
    _, legal_collection = init_chroma_index()
    collection_count = legal_collection.count()
    results = legal_collection.peek(limit=5)

    # Check Gemini API
    model = genai.GenerativeModel("gemini-2.5-pro")  # type: ignore
    model.generate_content("Hello")
