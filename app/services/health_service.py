import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.configs.logger import get_logger, setup_logging
from app.tools.weaviate_search import get_searcher

setup_logging()
logger = get_logger(__name__)


searcher = get_searcher()


def health_check():
    # Check Weaviate Cloud connection
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
