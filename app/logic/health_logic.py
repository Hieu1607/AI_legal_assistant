import os
import sys

from dotenv import load_dotenv
from groq import Groq
from huggingface_hub import hf_hub_download

# Load environment variables
load_dotenv()

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

    # Check Groq API
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    client.chat.completions.create(
        messages=[{"role": "user", "content": "Hello"}],
        model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
        max_tokens=10
    )
