"""
Health check service for Weaviate Cloud connection."""

from app.configs.logger import get_logger
from app.tools.weaviate_search import get_searcher

logger = get_logger(__name__)


async def health_check():
    searcher = None
    try:
        # Check Weaviate Cloud connection
        searcher = get_searcher()
        if not searcher:
            raise Exception("Failed to create WeaviateSearcher instance")

        if not await searcher.connect():
            raise Exception("Cannot connect to Weaviate Cloud")

        # Test basic query to check collection
        test_response = await searcher.ask_question("test")
        if not test_response:
            raise Exception("Weaviate collection not responding properly")
        # Close Weaviate connection
        await searcher.close()
    except Exception as e:
        logger.error(f"Weaviate Cloud health check failed: {e}")
        raise e
    finally:
        if searcher:
            await searcher.close()
