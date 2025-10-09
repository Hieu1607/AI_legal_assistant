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
from src.store_vector.weaviate_search import get_searcher

setup_logging()
logger = get_logger(__name__)


def health_check():
    # Check Weaviate Cloud connection
    searcher = get_searcher()
    if not searcher.connect():
        raise Exception("Cannot connect to Weaviate Cloud")
    
    # Test basic query to check collection
    test_response = searcher.ask_question("test")
    if not test_response:
        raise Exception("Weaviate collection not responding properly")

    # Check Gemini API
    model = genai.GenerativeModel("gemini-2.5-pro")  # type: ignore
    model.generate_content("Hello")
    
    # Close Weaviate connection
    searcher.close()
