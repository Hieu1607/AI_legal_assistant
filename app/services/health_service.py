import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
project_root = os.path.dirname(os.getcwd())
sys.path.insert(0, str(project_root))
from app.configs.logger import get_logger, setup_logging
from app.tools.weaviate_search import get_searcher

setup_logging()
logger = get_logger(__name__)


def health_check():
    # Check Weaviate Cloud connection
    searcher = get_searcher()
    if not searcher:
        raise Exception("Failed to create WeaviateSearcher instance")

    if not searcher.connect():
        raise Exception("Cannot connect to Weaviate Cloud")

    # Test basic query to check collection
    test_response = searcher.ask_question("test")
    if not test_response:
        raise Exception("Weaviate collection not responding properly")
    # Close Weaviate connection
    searcher.close()
