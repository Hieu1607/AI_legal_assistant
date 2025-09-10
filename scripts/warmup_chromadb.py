#!/usr/bin/env python3
"""
Script warm up ChromaDB Cloud và API embedding trước khi start API server
- Kiểm tra kết nối ChromaDB Cloud
- Test API embedding service
- Verify authentication và collection access
"""

import logging
import sys
import time
from pathlib import Path


def setup_path():
    """Add project root to Python path"""
    current_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(current_dir))


def setup_logging():
    """Configure logging for the warm up script"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


def warmup_chromadb(logger):
    """
    Warm up ChromaDB Cloud connection and verify accessibility

    Args:
        logger: Logger instance for output

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("🔥 Starting ChromaDB Cloud warm up...")

        # pylint: disable=import-outside-toplevel
        from src.store_vector.init_index import init_chroma_index

        # Initialize ChromaDB Cloud connection
        start_time = time.time()
        client, collection = init_chroma_index()

        # Test cloud connection
        logger.info("✅ ChromaDB Cloud client connected successfully")

        # Check collection count (lightweight operation)
        count = collection.count()
        logger.info("📊 Collection contains %d documents", count)

        # Test a lightweight query if collection has data
        if count > 0:
            try:
                # Test peek operation (no embedding needed)
                results = collection.peek(limit=1)
                if results and results.get("documents"):
                    logger.info("✅ Collection access test successful")
                else:
                    logger.warning("⚠️ Collection appears empty on peek")
            except Exception as query_error:  # pylint: disable=broad-except
                logger.warning("⚠️ Collection access test failed: %s", query_error)
        else:
            logger.info("ℹ️ Collection is empty - skipping query test")

        elapsed = time.time() - start_time
        logger.info("🎉 ChromaDB Cloud warm up completed in %.2f seconds", elapsed)

        return True

    except Exception as error:  # pylint: disable=broad-except
        logger.error("❌ ChromaDB Cloud warm up failed: %s", error)
        logger.error(
            "💡 Check: 1) Network connection, 2) API token, 3) Collection exists"
        )
        return False


def warmup_sentence_transformer(logger):
    """
    Warm up API embedding connection

    Args:
        logger: Logger instance for output

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("🔥 Starting API embedding warm up...")

        # pylint: disable=import-outside-toplevel
        from gradio_client import Client

        start_time = time.time()
        # Test API connection
        client = Client("hieuailearning/BAAI_bge_m3_api")

        # Test encoding with API
        test_text = "This is a test sentence for warm up"
        embedding = client.predict(text_input=test_text, api_name="/predict")

        elapsed = time.time() - start_time
        logger.info("✅ API embedding warm up completed in %.2f seconds", elapsed)
        logger.info("📐 Test embedding length: %d", len(embedding) if embedding else 0)

        return True

    except Exception as error:  # pylint: disable=broad-except
        logger.error("❌ API embedding warm up failed: %s", error)
        logger.error("💡 Check: 1) Internet connection, 2) Gradio API status")
        return False


def main():
    """
    Main warm up function - chỉ warm up trước khi start
    """
    # Setup path and logging
    setup_path()
    logger = setup_logging()

    logger.info("🚀 Starting AI Legal Assistant warm up sequence...")

    success = True

    # Warm up API embedding first
    if not warmup_sentence_transformer(logger):
        success = False

    # Small delay between tests
    time.sleep(1)

    # Warm up ChromaDB Cloud connection
    if not warmup_chromadb(logger):
        success = False

    if success:
        logger.info("🎉 Warm up completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Some warm up tasks failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
