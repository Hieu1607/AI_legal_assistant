"""
Weaviate Cloud Data Indexing Module (Simplified Version)

This module provides functionality to index legal document chunks to Weaviate Cloud
using the stable v3 API.

Author: AI Legal Assistant Team
Created: October 2025
"""

import json
import logging
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

import weaviate
from dotenv import load_dotenv
from weaviate.classes.init import Auth
from weaviate.classes.config import Configure, Property, DataType
from weaviate.classes.data import DataObject

# Load environment variables
load_dotenv()

# Add project root to path for imports
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))

from configs.logger import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)


class WeaviateIndexer:
    """
    A class to handle indexing legal document data to Weaviate Cloud using v4 API.
    """

    def __init__(
        self,
        weaviate_url: str = None,
        weaviate_api_key: str = None,
        class_name: str = "LegalDocument",
        batch_size: int = 100,
    ):
        """
        Initialize the Weaviate indexer.

        Args:
            weaviate_url: Weaviate Cloud URL
            weaviate_api_key: Weaviate Cloud API key
            class_name: Name of the class to create in Weaviate
            batch_size: Number of objects to upload per batch
        """
        self.weaviate_url = weaviate_url or os.getenv("WEAVIATE_URL")
        self.weaviate_api_key = weaviate_api_key or os.getenv("WEAVIATE_API_KEY")
        self.class_name = class_name
        self.batch_size = batch_size
        self.client = None

        if not self.weaviate_url or not self.weaviate_api_key:
            raise ValueError(
                "Weaviate URL and API key must be provided via parameters or environment variables"
            )

    def connect(self) -> bool:
        """
        Establish connection to Weaviate Cloud.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Create client with authentication
            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=self.weaviate_url,
                auth_credentials=Auth.api_key(self.weaviate_api_key),
            )

            # Test connection
            if self.client.is_ready():
                logger.info("Successfully connected to Weaviate Cloud")
                return True
            else:
                logger.error("Failed to connect to Weaviate Cloud")
                return False

        except Exception as e:
            logger.error(f"Error connecting to Weaviate: {str(e)}")
            return False

    def create_schema(self, use_simple_vectorizer: bool = True) -> bool:
        """
        Create the schema for legal documents in Weaviate.

        Args:
            use_simple_vectorizer: If True, use no vectorizer (BM25 only). If False, use transformers.

        Returns:
            bool: True if schema created successfully, False otherwise
        """
        try:
            # Check if class already exists
            collections = self.client.collections.list_all()
            if self.class_name in [col.name for col in collections]:
                logger.info(f"Class '{self.class_name}' already exists")
                return True

            # Configure vectorizer based on parameter
            if use_simple_vectorizer:
                vectorizer_config = Configure.Vectorizer.none()
                logger.info("Using no vectorizer - BM25 keyword search only")
            else:
                vectorizer_config = Configure.Vectorizer.text2vec_transformers()
                logger.info("Using text2vec-transformers for semantic search")

            # Define the class schema without embeddings
            collection = self.client.collections.create(
                name=self.class_name,
                description="Legal document chunks for Vietnamese law",
                properties=[
                    Property(
                        name="title",
                        data_type=DataType.TEXT,
                        description="Title of the legal document",
                    ),
                    Property(
                        name="update_day",
                        data_type=DataType.TEXT,
                        description="Last update date of the document",
                    ),
                    Property(
                        name="date_of_issue",
                        data_type=DataType.TEXT,
                        description="Date when the document was issued",
                    ),
                    Property(
                        name="chunk_id",
                        data_type=DataType.TEXT,
                        description="Unique identifier for the text chunk",
                    ),
                    Property(
                        name="text",
                        data_type=DataType.TEXT,
                        description="The actual text content of the chunk",
                    ),
                    Property(
                        name="created_at",
                        data_type=DataType.DATE,
                        description="Timestamp when the object was indexed",
                    ),
                ],
                vectorizer_config=vectorizer_config,
                generative_config=None
            )

            logger.info(f"Successfully created class '{self.class_name}'")
            return True

        except Exception as e:
            logger.error(f"Error creating schema: {str(e)}")
            # If transformers failed, try with no vectorizer
            if not use_simple_vectorizer:
                logger.info("Transformers failed, trying with no vectorizer...")
                return self.create_schema(use_simple_vectorizer=True)
            return False

    def delete_class(self) -> bool:
        """
        Delete the existing class (useful for resetting data).

        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            self.client.collections.delete(self.class_name)
            logger.info(f"Successfully deleted class '{self.class_name}'")
            return True
        except Exception as e:
            logger.error(f"Error deleting class: {str(e)}")
            return False

    def load_embedded_data(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load embedded data from JSON file.

        Args:
            file_path: Path to the JSON file containing embedded chunks

        Returns:
            List of dictionaries containing the data
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} chunks from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {str(e)}")
            return []

    def prepare_objects(self, data: List[Dict[str, Any]]) -> List[DataObject]:
        """
        Prepare data objects for Weaviate upload without embeddings.
        Weaviate will automatically generate embeddings using its vectorizer.

        Args:
            data: List of dictionaries containing document chunks

        Returns:
            List of DataObject instances ready for upload
        """
        objects = []
        current_time = datetime.now()

        for item in data:
            try:
                # Create properties dictionary (no embedding needed)
                properties = {
                    "title": item.get("title", ""),
                    "update_day": item.get("update_day", ""),
                    "date_of_issue": item.get("date_of_issue", ""),
                    "chunk_id": item.get("chunk_id", ""),
                    "text": item.get("text", ""),
                    "created_at": current_time,
                }

                # Create data object without custom vector
                # Weaviate will automatically generate embeddings from the text
                data_object = DataObject(properties=properties)

                objects.append(data_object)

            except Exception as e:
                logger.error(
                    f"Error preparing object {item.get('chunk_id', 'unknown')}: {str(e)}"
                )
                continue

        logger.info(f"Prepared {len(objects)} objects for upload (embeddings will be auto-generated)")
        return objects

    def upload_data(self, objects: List[DataObject]) -> Dict[str, int]:
        """
        Upload data objects to Weaviate in batches.

        Args:
            objects: List of DataObject instances to upload

        Returns:
            Dictionary with upload statistics
        """
        collection = self.client.collections.get(self.class_name)

        total_objects = len(objects)
        successful_uploads = 0
        failed_uploads = 0

        logger.info(
            f"Starting upload of {total_objects} objects in batches of {self.batch_size}"
        )

        # Process in batches
        for i in range(0, total_objects, self.batch_size):
            batch = objects[i : i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (total_objects + self.batch_size - 1) // self.batch_size

            try:
                logger.info(
                    f"Uploading batch {batch_num}/{total_batches} ({len(batch)} objects)"
                )

                # Insert batch
                response = collection.data.insert_many(batch)

                # Check for errors
                if response.errors:
                    logger.error(f"Batch {batch_num} had errors: {response.errors}")
                    failed_uploads += len(response.errors)
                    successful_uploads += len(batch) - len(response.errors)
                else:
                    successful_uploads += len(batch)
                    logger.info(f"Batch {batch_num} uploaded successfully")

                # Small delay between batches to avoid rate limiting
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error uploading batch {batch_num}: {str(e)}")
                failed_uploads += len(batch)

        results = {
            "total_objects": total_objects,
            "successful_uploads": successful_uploads,
            "failed_uploads": failed_uploads,
            "success_rate": (
                (successful_uploads / total_objects) * 100 if total_objects > 0 else 0
            ),
        }

        logger.info(f"Upload completed. Success rate: {results['success_rate']:.2f}%")
        return results

    def get_object_count(self) -> int:
        """
        Get the total number of objects in the collection.

        Returns:
            Number of objects in the collection
        """
        try:
            collection = self.client.collections.get(self.class_name)
            response = collection.aggregate.over_all(total_count=True)
            count = response.total_count
            logger.info(f"Collection '{self.class_name}' contains {count} objects")
            return count
        except Exception as e:
            logger.error(f"Error getting object count: {str(e)}")
            return 0

    def test_query(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Test query using BM25 keyword search.

        Args:
            query_text: Text to search for
            limit: Maximum number of results to return

        Returns:
            List of search results
        """
        try:
            collection = self.client.collections.get(self.class_name)

            # Perform BM25 keyword search (works without vectorizer)
            response = collection.query.bm25(
                query=query_text, 
                limit=limit, 
                return_metadata=["score"]
            )

            results = []
            for obj in response.objects:
                result = {
                    "chunk_id": obj.properties.get("chunk_id"),
                    "title": obj.properties.get("title"),
                    "text": (
                        obj.properties.get("text")[:200] + "..."
                        if len(obj.properties.get("text", "")) > 200
                        else obj.properties.get("text")
                    ),
                    "score": obj.metadata.score if obj.metadata.score else 0,
                }
                results.append(result)

            logger.info(f"Found {len(results)} results for BM25 search: {query_text}")
            return results

        except Exception as e:
            logger.error(f"Error performing BM25 query: {str(e)}")
            return []
    
    def test_vector_query(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Test query using vector similarity search (requires vectorizer).

        Args:
            query_text: Text to search for
            limit: Maximum number of results to return

        Returns:
            List of search results
        """
        try:
            collection = self.client.collections.get(self.class_name)

            # Perform semantic vector search
            response = collection.query.near_text(
                query=query_text, 
                limit=limit, 
                return_metadata=["score", "distance"]
            )

            results = []
            for obj in response.objects:
                result = {
                    "chunk_id": obj.properties.get("chunk_id"),
                    "title": obj.properties.get("title"),
                    "text": (
                        obj.properties.get("text")[:200] + "..."
                        if len(obj.properties.get("text", "")) > 200
                        else obj.properties.get("text")
                    ),
                    "score": obj.metadata.score if obj.metadata.score else 0,
                    "distance": obj.metadata.distance if obj.metadata.distance else 0,
                }
                results.append(result)

            logger.info(f"Found {len(results)} results for vector search: {query_text}")
            return results

        except Exception as e:
            logger.error(f"Error performing vector query: {str(e)}")
            logger.info("Vector search failed - collection may not have vectorizer configured")
            return []
    
    def test_hybrid_query(self, query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Test hybrid query combining vector and keyword search.

        Args:
            query_text: Text to search for
            limit: Maximum number of results to return

        Returns:
            List of search results
        """
        try:
            collection = self.client.collections.get(self.class_name)

            # Perform hybrid search (vector + BM25)
            response = collection.query.hybrid(
                query=query_text, 
                limit=limit, 
                return_metadata=["score"]
            )

            results = []
            for obj in response.objects:
                result = {
                    "chunk_id": obj.properties.get("chunk_id"),
                    "title": obj.properties.get("title"),
                    "text": (
                        obj.properties.get("text")[:200] + "..."
                        if len(obj.properties.get("text", "")) > 200
                        else obj.properties.get("text")
                    ),
                    "score": obj.metadata.score if obj.metadata.score else 0,
                }
                results.append(result)

            logger.info(f"Found {len(results)} results for hybrid search: {query_text}")
            return results

        except Exception as e:
            logger.error(f"Error performing hybrid query: {str(e)}")
            return []

    def close_connection(self):
        """Close the Weaviate client connection."""
        if self.client:
            self.client.close()
            logger.info("Weaviate connection closed")


def main():
    """
    Main function to demonstrate the indexing process.
    """
    # Configuration
    DATA_FILE = os.path.join(
        root, "total_chunks_fixed.json"
    )

    # Create indexer instance
    indexer = WeaviateIndexer(
        class_name="LegalDocument", batch_size=50  # Smaller batch size for stability
    )

    try:
        # Step 1: Connect to Weaviate
        logger.info("=== Step 1: Connecting to Weaviate Cloud ===")
        if not indexer.connect():
            logger.error("Failed to connect to Weaviate Cloud")
            return

        # Step 2: Create schema
        logger.info("=== Step 2: Creating Schema ===")
        if not indexer.create_schema():
            logger.error("Failed to create schema")
            return

        # Step 3: Load data
        logger.info("=== Step 3: Loading Data ===")
        data = indexer.load_embedded_data(DATA_FILE)
        if not data:
            logger.error("No data loaded")
            return

        # Step 4: Prepare objects
        logger.info("=== Step 4: Preparing Objects ===")
        objects = indexer.prepare_objects(data)
        if not objects:
            logger.error("No objects prepared")
            return

        # Step 5: Upload data
        logger.info("=== Step 5: Uploading Data ===")
        results = indexer.upload_data(objects)

        # Step 6: Verify upload
        logger.info("=== Step 6: Verifying Upload ===")
        count = indexer.get_object_count()

        # Step 7: Test queries
        logger.info("=== Step 7: Testing Queries ===")
        
        # Test BM25 search (always works)
        logger.info("--- BM25 Keyword Search Test ---")
        bm25_results = indexer.test_query("hình sự", limit=3)
        for i, result in enumerate(bm25_results, 1):
            logger.info(
                f"BM25 Result {i}: {result['chunk_id']} - Score: {result['score']:.4f}"
            )
        
        # Test vector search (if vectorizer is available)
        logger.info("--- Vector Search Test ---")
        vector_results = indexer.test_vector_query("hình sự", limit=3)
        for i, result in enumerate(vector_results, 1):
            logger.info(
                f"Vector Result {i}: {result['chunk_id']} - Score: {result['score']:.4f}"
            )
        
        # Test hybrid search (if vectorizer is available)
        logger.info("--- Hybrid Search Test ---")
        hybrid_results = indexer.test_hybrid_query("hình sự", limit=3)
        for i, result in enumerate(hybrid_results, 1):
            logger.info(
                f"Hybrid Result {i}: {result['chunk_id']} - Score: {result['score']:.4f}"
            )

        logger.info("=== Indexing Process Completed Successfully ===")
        logger.info(f"Final Statistics: {results}")

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        # Always close the connection
        indexer.close_connection()


if __name__ == "__main__":
    main()
