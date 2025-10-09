#!/usr/bin/env python3

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.store_vector.weaviate_search import search_relevant_embeddings

def test_retrieve():
    """Test the retrieve functionality"""
    
    print("🔍 Testing retrieve functionality...")
    print("=" * 60)
    
    question = "Tôi bị hiếp dâm thì tôi có thể kiện không?"
    top_k = 5
    
    print(f"📋 Question: {question}")
    print(f"📊 Top K: {top_k}")
    print("=" * 60)
    
    try:
        result = search_relevant_embeddings(question, top_k)
        
        print("✅ Success!")
        print(f"📄 Result structure: {list(result.keys())}")
        
        if 'documents' in result and result['documents']:
            documents = result['documents'][0]
            print(f"📊 Found {len(documents)} documents")
            
            for i, doc in enumerate(documents):
                print(f"\n{i+1}. {doc[:100]}...")
        else:
            print("❌ No documents found")
            
        print(f"\n🔗 Full result: {result}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up connections
        from src.store_vector.weaviate_search import cleanup
        cleanup()
        print("\n🔧 Cleaned up connections")

if __name__ == "__main__":
    test_retrieve()