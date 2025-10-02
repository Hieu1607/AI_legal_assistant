#!/usr/bin/env python3
"""
Test script for the new title-based RAG functionality
"""

import asyncio
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.logic.rag_logic import test_title_based_rag


async def main():
    """Test the title-based RAG functionality with sample questions"""

    test_questions = [
        "Tôi muốn hỏi về việc tranh chấp hợp đồng lao động giữa người sử dụng lao động và người lao động. Trong trường hợp này, tôi cần tham khảo những quy định nào trong pháp luật để bảo vệ quyền lợi của mình?",
        "Quy định về an toàn lao động trong nhà máy?",
        "Làm thế nào để thành lập công ty trách nhiệm hữu hạn?",
        "Tôi muốn biết về quy định mua bán nhà đất?",
    ]

    print("=== TESTING TITLE-BASED RAG FUNCTIONALITY ===\n")

    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"TEST {i}: {question}")
        print("=" * 80)

        try:
            result = await test_title_based_rag(question)

            print(f"\n✅ ANSWER:")
            print(result["answer"])

            print(f"\n📊 METADATA:")
            print(f"  - Enhanced Question: {result['enhanced_question']}")
            print(f"  - Keywords: {result['keywords']}")
            print(f"  - Context Count: {result['context_count']}")

            print(f"\n🎯 RELEVANT TITLES FOUND:")
            if result["relevant_titles"]:
                for j, title in enumerate(result["relevant_titles"], 1):
                    print(f"  {j}. {title}")
            else:
                print("  - No specific titles found (using general search)")

            print(f"\n📚 SOURCES:")
            sources = list(
                set([chunk["document_name"] for chunk in result["relevant_chunks"]])
            )
            for j, source in enumerate(sources, 1):
                print(f"  {j}. {source}")

            print(f"\n⏱️ TIMING:")
            timing = result["timing"]
            print(f"  - Enhancement: {timing['enhancement_time']:.4f}s")
            print(f"  - Retrieving: {timing['retrieving_time']:.4f}s")
            print(f"  - LLM: {timing['llm_time']:.4f}s")
            print(f"  - Total: {timing['total_time']:.4f}s")

        except Exception as e:
            print(f"❌ ERROR: {e}")

        print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
