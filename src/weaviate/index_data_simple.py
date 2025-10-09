"""
Weaviate Cloud Data Indexing Module - Simplified Version

This module provides functionality to index legal document chunks to Weaviate Cloud.

Author: AI Legal Assistant Team  
Created: October 2025
"""

import json
import os
import sys
import time
from typing import Dict, List, Any
import logging
from datetime import datetime

import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Property, DataType
from dotenv import load_dotenv

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
    A class to handle indexing legal document data to Weaviate Cloud.
    """
    
    def __init__(self, 
                 weaviate_url: str = None,
                 weaviate_api_key: str = None,
                 class_name: str = "LegalDocument",
                 batch_size: int = 100):
        """
        Initialize the Weaviate indexer.
        """
        self.weaviate_url = weaviate_url or os.getenv("WEAVIATE_URL")
        self.weaviate_api_key = weaviate_api_key or os.getenv("WEAVIATE_API_KEY")
        self.class_name = class_name
        self.batch_size = batch_size
        self.client = None
        
        if not self.weaviate_url or not self.weaviate_api_key:
            raise ValueError("Weaviate URL and API key must be provided via parameters or environment variables")
    
    def connect(self) -> bool:
        """
        Establish connection to Weaviate Cloud.
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
    
    def create_schema(self) -> bool:
        """
        Create the schema for legal documents in Weaviate using v4 API.
        """
        try:
            # Check if collection already exists
            collections = self.client.collections.list_all()
            collection_names = [col.name for col in collections.values()]
            
            if self.class_name in collection_names:
                logger.info(f"Collection '{self.class_name}' already exists")
                return True
            
            # Create collection with properties
            collection = self.client.collections.create(
                name=self.class_name,
                description="Legal document chunks with embeddings for Vietnamese law",
                properties=[
                    Property(name="title", data_type=DataType.TEXT, description="Title of the legal document"),
                    Property(name="update_day", data_type=DataType.TEXT, description="Last update date of the document"),
                    Property(name="date_of_issue", data_type=DataType.TEXT, description="Date when the document was issued"),
                    Property(name="chunk_id", data_type=DataType.TEXT, description="Unique identifier for the text chunk"),
                    Property(name="text", data_type=DataType.TEXT, description="The actual text content of the chunk"),
                    Property(name="embedding_dimension", data_type=DataType.INT, description="Dimension of the embedding vector"),
                    Property(name="model_name", data_type=DataType.TEXT, description="Name of the model used to create embeddings"),
                    Property(name="created_at", data_type=DataType.DATE, description="Original creation timestamp"),
                    Property(name="indexed_at", data_type=DataType.DATE, description="Timestamp when indexed to Weaviate")
                ],
                vectorizer_config=None,  # We'll provide our own embeddings
            )
            
            logger.info(f"Successfully created collection '{self.class_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error creating schema: {str(e)}")
            return False
    
    def delete_collection(self) -> bool:
        """
        Delete the existing collection (useful for resetting data).
        """
        try:
            self.client.collections.delete(self.class_name)
            logger.info(f"Successfully deleted collection '{self.class_name}'")
            return True
        except Exception as e:
            logger.error(f"Error deleting collection: {str(e)}")
            return False
    
    def load_embedded_data(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Load embedded data from JSON file.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded {len(data)} chunks from {file_path}")
            return data
        except Exception as e:
            logger.error(f"Error loading data from {file_path}: {str(e)}")
            return []
    
    def upload_data(self, data: List[Dict[str, Any]], 
                   embedding_model: str = "unknown") -> Dict[str, int]:
        """
        Upload data objects to Weaviate in batches.
        """
        total_objects = len(data)
        successful_uploads = 0
        failed_uploads = 0
        current_time = datetime.now()
        
        logger.info(f"Starting upload of {total_objects} objects in batches of {self.batch_size}")
        
        try:
            collection = self.client.collections.get(self.class_name)
            
            # Process in batches
            for i in range(0, total_objects, self.batch_size):
                batch = data[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                total_batches = (total_objects + self.batch_size - 1) // self.batch_size
                
                try:
                    logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} objects)")
                    
                    # Prepare batch objects
                    batch_objects = []
                    for item in batch:
                        try:
                            # Extract embedding vector if present
                            vector = item.get('embedding', None)
                            if vector and isinstance(vector, list):
                                vector = [float(x) for x in vector]
                            
                            # Convert datetime strings to RFC3339 format with timezone
                            def format_datetime(dt_value):
                                if isinstance(dt_value, str):
                                    try:
                                        # Parse the string and add timezone if missing
                                        if dt_value.endswith('Z'):
                                            dt_value = dt_value[:-1] + '+00:00'
                                        elif '+' not in dt_value and 'T' in dt_value:
                                            dt_value = dt_value + '+00:00'
                                        
                                        dt = datetime.fromisoformat(dt_value)
                                        return dt.isoformat()
                                    except:
                                        # Fallback to current time with timezone
                                        import datetime as dt_module
                                        return current_time.replace(tzinfo=dt_module.timezone.utc).isoformat()
                                elif isinstance(dt_value, datetime):
                                    if dt_value.tzinfo is None:
                                        # Add UTC timezone if missing
                                        import datetime as dt_module
                                        dt_value = dt_value.replace(tzinfo=dt_module.timezone.utc)
                                    return dt_value.isoformat()
                                else:
                                    import datetime as dt_module
                                    return current_time.replace(tzinfo=dt_module.timezone.utc).isoformat()
                            
                            # Create properties dictionary
                            properties = {
                                "title": item.get("title", ""),
                                "update_day": item.get("update_day", ""),
                                "date_of_issue": item.get("date_of_issue", ""),
                                "chunk_id": item.get("chunk_id", ""),
                                "text": item.get("text", ""),
                                "embedding_dimension": item.get("embedding_dimension", 0),
                                "model_name": item.get("model_name", embedding_model),
                                "created_at": format_datetime(item.get("created_at", current_time)),
                                "indexed_at": format_datetime(current_time)
                            }
                            
                            # Use DataObject for proper vector handling
                            from weaviate.classes.data import DataObject
                            if vector:
                                data_obj = DataObject(
                                    properties=properties,
                                    vector=vector
                                )
                            else:
                                data_obj = DataObject(properties=properties)
                            
                            batch_objects.append(data_obj)
                            
                        except Exception as e:
                            logger.error(f"Error preparing object {item.get('chunk_id', 'unknown')}: {str(e)}")
                            failed_uploads += 1
                            continue
                    
                    # Insert batch
                    if batch_objects:
                        response = collection.data.insert_many(batch_objects)
                        
                        # Check for errors
                        if hasattr(response, 'errors') and response.errors:
                            error_count = len(response.errors)
                            logger.error(f"Batch {batch_num} had {error_count} errors")
                            failed_uploads += error_count
                            successful_uploads += len(batch_objects) - error_count
                        else:
                            successful_uploads += len(batch_objects)
                            logger.info(f"Batch {batch_num} uploaded successfully")
                    
                    # Small delay between batches
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error uploading batch {batch_num}: {str(e)}")
                    failed_uploads += len(batch)
        
        except Exception as e:
            logger.error(f"Error during upload process: {str(e)}")
            failed_uploads += total_objects - successful_uploads
        
        results = {
            "total_objects": total_objects,
            "successful_uploads": successful_uploads,
            "failed_uploads": failed_uploads,
            "success_rate": (successful_uploads / total_objects) * 100 if total_objects > 0 else 0
        }
        
        logger.info(f"Upload completed. Success rate: {results['success_rate']:.2f}%")
        return results
    
    def get_object_count(self) -> int:
        """
        Get the total number of objects in the collection.
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
        Test query to verify the indexed data.
        """
        try:
            collection = self.client.collections.get(self.class_name)
            
            # Perform a simple text search
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
                    "text": obj.properties.get("text", "")[:200] + "..." if len(obj.properties.get("text", "")) > 200 else obj.properties.get("text", ""),
                    "score": obj.metadata.score if hasattr(obj.metadata, 'score') else 0
                }
                results.append(result)
            
            logger.info(f"Found {len(results)} results for query: {query_text}")
            return results
            
        except Exception as e:
            logger.error(f"Error performing test query: {str(e)}")
            return []
    
    def close_connection(self):
        """Close the Weaviate client connection."""
        if self.client:
            self.client.close()
            logger.info("Weaviate connection closed")
    
    def close(self):
        """Alias for close_connection for convenience."""
        self.close_connection()


def main():
    """
    Main function to demonstrate the indexing process.
    """
    # Configuration
    DATA_FILE = os.path.join(root, "data", "processed", "filtered_data_sample.json")
    EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"  # From the data
    
    # Create indexer instance
    indexer = WeaviateIndexer(
        class_name="LegalDocument",
        batch_size=50  # Smaller batch size for stability
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
        
        # Step 4: Upload data
        logger.info("=== Step 4: Uploading Data ===")
        results = indexer.upload_data(data, EMBEDDING_MODEL)
        
        # Step 5: Verify upload
        logger.info("=== Step 5: Verifying Upload ===")
        count = indexer.get_object_count()
        
        # Step 6: Test query
        logger.info("=== Step 6: Testing Query ===")
        test_results = indexer.test_query("hình sự", limit=3)
        for i, result in enumerate(test_results, 1):
            logger.info(f"Result {i}: {result['chunk_id']} - Score: {result['score']:.4f}")
        
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