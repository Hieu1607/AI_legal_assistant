#!/usr/bin/env python3
"""
Test script for RAG endpoint with relevant chunks
"""

import json
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
root = Path(__file__).parent.absolute()
sys.path.insert(0, str(root))

from app.logic.rag_logic import process_rag_query

async def test_rag_with_chunks():
    """Test RAG with relevant chunks"""
    
    test_question = "Hình phạt cho tội trộm cắp là gì?"
    
    print("🔍 Testing RAG with relevant chunks...")
    print(f"📋 Question: {test_question}")
    print("=" * 60)
    
    try:
        result = await process_rag_query(test_question)
        
        print(f"✅ Success!")
        print(f"📄 Answer: {result['answer']}")
        print(f"📊 Context count: {result['context_count']}")
        print(f"⏱️ Total time: {result['timing']['total_time']:.3f}s")
        
        print("\n📚 Relevant Chunks:")
        print("-" * 40)
        for i, chunk in enumerate(result.get('relevant_chunks', []), 1):
            print(f"{i}. {chunk[:200]}...")
            print()
        
        # Print as JSON for API testing
        print("\n🔗 JSON Response:")
        print("-" * 40)
        print(json.dumps({
            "status": "success",
            "data": {
                "answer": result["answer"],
                "question": result["question"],
                "context_count": result["context_count"],
                "relevant_chunks": result.get("relevant_chunks", []),
                "timing": result.get("timing", {})
            }
        }, ensure_ascii=False, indent=2))
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    try:
        asyncio.run(test_rag_with_chunks())
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()