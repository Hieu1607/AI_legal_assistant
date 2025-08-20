import os
import sys

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()


# Get the root directory of the project
current_dir = os.path.dirname(os.path.abspath(__file__))
while True:
    # Check if 'data' and 'src' directories exist in current directory
    if os.path.isdir(os.path.join(current_dir, "data")) and os.path.isdir(
        os.path.join(current_dir, "src")
    ):
        root = current_dir
        break

    parent_dir = os.path.dirname(current_dir)
    if parent_dir == current_dir:  # Reached system root directory
        raise FileNotFoundError(
            "Check the project structure. 'data' and 'src' directories not found."
        )
    current_dir = parent_dir

# Set up logging
sys.path.insert(0, str(root))

from configs.logger import get_logger, setup_logging
from src.store_vector.init_index import init_chroma_index

setup_logging()
logger = get_logger(__name__)
collection = init_chroma_index()[1]

# Global model variable to cache the loaded model
model = None
MODEL_NAME = "BAAI/bge-m3"
MODEL_DIR = os.path.join(root, "models", MODEL_NAME.replace("/", "_"))

def check_model_exists():
    """Check if model exists in local models directory"""
    # Check for key model files
    required_files = ["config.json", "pytorch_model.bin", "tokenizer.json"]
    
    if not os.path.exists(MODEL_DIR):
        return False
    
    for file in required_files:
        if not os.path.exists(os.path.join(MODEL_DIR, file)):
            return False
    
    return True

def load_model():
    """Load the embedding model with local storage and error handling"""
    global model
    
    if model is not None:
        return model
    
    logger.info(f"Checking for {MODEL_NAME} model in local directory...")
    logger.info(f"Model directory: {MODEL_DIR}")
    
    # Ensure models directory exists
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    try:
        if check_model_exists():
            # Load from local directory
            logger.info("Model found locally, loading from disk...")
            model = SentenceTransformer(MODEL_DIR)
            logger.info("Model loaded successfully from local directory")
            return model
        else:
            # Download and save to local directory
            logger.info("Model not found locally, downloading...")
            
            # Remove offline restrictions to download
            if "TRANSFORMERS_OFFLINE" in os.environ:
                del os.environ["TRANSFORMERS_OFFLINE"]
            if "HF_HUB_OFFLINE" in os.environ:
                del os.environ["HF_HUB_OFFLINE"]
            
            # Download the model
            temp_model = SentenceTransformer(MODEL_NAME)
            
            # Save to local directory
            temp_model.save(MODEL_DIR)
            logger.info(f"Model downloaded and saved to {MODEL_DIR}")
            
            # Load from saved location
            model = SentenceTransformer(MODEL_DIR)
            logger.info("Model loaded successfully from saved location")
            
            return model
            
    except Exception as e:
        logger.error(f"Failed to load/download model: {e}")
        return None


def search_relevant_embeddings(text, n_results):
    try:
        # Load model when needed (lazy loading with caching)
        current_model = load_model()
        
        if current_model is None:
            logger.error("Model is not loaded. Cannot perform embedding search.")
            return {
                "ids": [[]],
                "distances": [[]],
                "metadatas": [[]],
                "documents": [[]],
                "embeddings": [[]],
                "cosine_similarities": [[]],
            }
        
        # Use the loaded model to encode the text
        embedding_from_text = current_model.encode(text, normalize_embeddings=True)
        results = collection.query(
            query_embeddings=embedding_from_text,
            n_results=n_results,
            # where={"source": "article"},        # Optional: Filter by metadata (AND logic)
            # where_document={"$contains":"leave"} # Optional: Filter by document content
        )

        # Calculate cosine similarity from distances (ChromaDB returns cosine distances)
        # Cosine similarity = 1 - cosine distance
        cosine_similarities = []
        if results["distances"] and len(results["distances"][0]) > 0:
            cosine_similarities = [1 - distance for distance in results["distances"][0]]

        # Create new dictionary with cosine similarities
        enhanced_results = {
            "ids": results["ids"],
            "distances": results["distances"],
            "metadatas": results["metadatas"],
            "documents": results["documents"],
            "embeddings": results["embeddings"],
            "cosine_similarities": [cosine_similarities],
        }

        return enhanced_results
    
    except Exception as e:
        logger.error(f"Error during embedding search: {e}")
        return {
            "ids": [[]],
            "distances": [[]],
            "metadatas": [[]],
            "documents": [[]],
            "embeddings": [[]],
            "cosine_similarities": [[]],
        }


if __name__ == "__main__":
    test_text = "Chương I điều 2 bộ luật hình sự."
    res = search_relevant_embeddings(test_text, 5)
    if res["documents"] and len(res["documents"][0]) > 0:
        print("Documents:")
        for i, doc in enumerate(res["documents"][0]):
            print(f"  {i+1}. {doc[:100]}...")

        print("\nCosine Similarities:")
        for i, score in enumerate(res["cosine_similarities"][0]):
            print(f"  {i+1}. {score:.4f}")

        print("\nDistances:")
        if res["distances"] and len(res["distances"][0]) > 0:
            for i, dist in enumerate(res["distances"][0]):
                print(f"  {i+1}. {dist:.4f}")
    else:
        print("No documents found.")
