#!/usr/bin/env python3
"""
Script to run Weaviate indexing process for legal documents.

This script provides a command-line interface to index legal document data
to Weaviate Cloud with various options and configurations.

Usage:
    python run_weaviate_indexing.py [options]

Options:
    --data-file: Path to the JSON file containing embedded chunks
    --batch-size: Number of objects to upload per batch (default: 50)
    --class-name: Name of the Weaviate class (default: LegalDocument)
    --reset: Delete existing class before creating new one
    --test-only: Only run connection and schema tests, don't upload data
    --help: Show this help message

Example:
    python run_weaviate_indexing.py --data-file data/processed/sample_embedded_chunks_with_API.json --batch-size 100
"""

import argparse
import os
import sys
from pathlib import Path

# Add project root to path
root = Path(__file__).parent.absolute()
sys.path.insert(0, str(root))

from src.weaviate.index_data_simple import WeaviateIndexer
from configs.logger import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Index legal document data to Weaviate Cloud",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--data-file",
        type=str,
        default="data/processed/filtered_data_sample.json",
        help="Path to JSON file containing embedded chunks"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Number of objects to upload per batch"
    )
    
    parser.add_argument(
        "--class-name",
        type=str,
        default="LegalDocument",
        help="Name of the Weaviate class"
    )
    
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing class before creating new one"
    )
    
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Only test connection and schema, don't upload data"
    )
    
    parser.add_argument(
        "--embedding-model",
        type=str,
        default="models/embedding-001",
        help="Name of the embedding model used"
    )
    
    return parser.parse_args()


def validate_data_file(file_path: str) -> str:
    """
    Validate and resolve data file path.
    
    Args:
        file_path: Path to the data file
        
    Returns:
        Absolute path to the data file
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    # Make path relative to project root if not absolute
    if not os.path.isabs(file_path):
        file_path = os.path.join(root, file_path)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")
    
    return file_path


def main():
    """Main function to run the indexing process."""
    args = parse_arguments()
    
    try:
        # Validate data file
        data_file = validate_data_file(args.data_file)
        logger.info(f"Using data file: {data_file}")
        
        # Create indexer
        indexer = WeaviateIndexer(
            class_name=args.class_name,
            batch_size=args.batch_size
        )
        
        # Step 1: Connect to Weaviate
        logger.info("=== Connecting to Weaviate Cloud ===")
        if not indexer.connect():
            logger.error("Failed to connect to Weaviate Cloud")
            logger.error("Please check your WEAVIATE_URL and WEAVIATE_API_KEY in .env file")
            return 1
        
        # Step 2: Handle reset if requested
        if args.reset:
            logger.info("=== Resetting Existing Class ===")
            indexer.delete_class()
        
        # Step 3: Create schema
        logger.info("=== Creating/Verifying Schema ===")
        if not indexer.create_schema():
            logger.error("Failed to create schema")
            return 1
        
        # If test-only mode, stop here
        if args.test_only:
            logger.info("=== Test Mode: Connection and Schema OK ===")
            count = indexer.get_object_count()
            logger.info(f"Current object count: {count}")
            return 0
        
        # Step 4: Load and upload data
        logger.info("=== Loading Data ===")
        data = indexer.load_embedded_data(data_file)
        if not data:
            logger.error("No data loaded")
            return 1
        
        logger.info("=== Uploading Data ===")
        results = indexer.upload_data(data, args.embedding_model)
        
        # Step 5: Verify and test
        logger.info("=== Verifying Upload ===")
        final_count = indexer.get_object_count()
        
        logger.info("=== Testing Query ===")
        test_results = indexer.test_query("hình sự", limit=3)
        
        # Print summary
        logger.info("=== INDEXING COMPLETED ===")
        logger.info(f"Upload Results: {results}")
        logger.info(f"Final object count: {final_count}")
        logger.info(f"Test query returned {len(test_results)} results")
        
        # Determine success
        if results['success_rate'] >= 95:
            logger.info("✅ Indexing completed successfully!")
            return 0
        else:
            logger.warning(f"⚠️  Indexing completed with {results['success_rate']:.1f}% success rate")
            return 0
            
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1
    finally:
        # Always close connection
        if 'indexer' in locals():
            indexer.close_connection()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)