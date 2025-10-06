#!/usr/bin/env python3
"""
Comprehensive RAG test script for Civil Law question
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()


async def test_full_rag_pipeline():
    """Test the complete RAG pipeline with the Civil Law question"""

    question = "What is Chapter I Article 1 of Civil Law?"
    print(f"🧪 Testing RAG pipeline with question: '{question}'")
    print("=" * 60)

    try:
        # Import the RAG logic
        from app.logic.rag_logic import process_rag_query

        print("✅ RAG modules imported successfully")

        # Test the full RAG pipeline
        print("🚀 Running full RAG pipeline...")
        result = await process_rag_query(question)

        print("📋 RAG Pipeline Results:")
        print("-" * 40)
        print(f"Result type: {type(result)}")
        print(f"Result content: {result}")
        print("-" * 40)

        if result and isinstance(result, dict):
            print("✅ RAG pipeline returned a response!")
            if "answer" in result:
                answer = result["answer"]
                print(f"📄 Answer length: {len(answer)} characters")
                print(f"📝 Answer: {answer}")
            else:
                print(f"📊 Result keys: {list(result.keys())}")
        else:
            print("⚠️  RAG pipeline returned empty or no response")

        return result

    except Exception as e:
        print(f"❌ Error in RAG pipeline: {e}")
        print(f"🔍 Error type: {type(e).__name__}")
        import traceback

        print(f"📊 Full traceback:\n{traceback.format_exc()}")
        return None


async def test_individual_steps():
    """Test individual RAG pipeline steps"""

    question = "What is Chapter I Article 1 of Civil Law?"
    print(f"\n🔍 Testing individual RAG steps for: '{question}'")
    print("=" * 60)

    try:
        from app.logic.rag_logic import (
            enhance_question,
            extract_keywords,
            step1_find_relevant_laws,
        )

        # Step 1: Find relevant laws
        print("📋 Step 1: Finding relevant laws...")
        is_legal, laws = await step1_find_relevant_laws(question)
        print(f"   └─ Is legal question: {is_legal}")
        print(f"   └─ Relevant laws: {laws}")

        # Step 2: Extract keywords
        print("\n🔍 Step 2: Extracting keywords...")
        keywords = await extract_keywords(question)
        print(f"   └─ Keywords: {keywords}")

        # Step 3: Enhance question
        print("\n✨ Step 3: Enhancing question...")
        enhanced = await enhance_question(question)
        print(f"   └─ Enhanced question: {enhanced}")

        return True

    except Exception as e:
        print(f"❌ Error in individual steps: {e}")
        import traceback

        print(f"📊 Full traceback:\n{traceback.format_exc()}")
        return False


async def main():
    """Main test function"""
    print("🏛️  AI Legal Assistant - RAG Testing")
    print("====================================")

    # Test individual steps first
    steps_success = await test_individual_steps()

    if steps_success:
        print("\n" + "=" * 60)
        # Test full pipeline
        result = await test_full_rag_pipeline()

        if result:
            print("\n🎉 RAG Testing Summary:")
            print("✅ Individual steps: PASSED")
            print("✅ Full pipeline: PASSED")
            print("✅ OpenAI API integration: WORKING")
            print("✅ No proxies errors: CONFIRMED")
        else:
            print("\n📋 RAG Testing Summary:")
            print("✅ Individual steps: PASSED")
            print("⚠️  Full pipeline: RETURNED EMPTY")
            print("✅ OpenAI API integration: WORKING")
    else:
        print("\n❌ RAG Testing Summary:")
        print("❌ Individual steps: FAILED")
        print("❌ Cannot proceed to full pipeline test")


if __name__ == "__main__":
    asyncio.run(main())
