#!/usr/bin/env python3
"""
Test script to check if the RAG API is working without the proxies error
"""

import os
import sys

from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Test the specific function that was causing the error
try:
    import asyncio

    from app.logic.rag_logic import step1_find_relevant_laws

    print("Testing step1_find_relevant_laws function...")

    # Test the function directly (it's async)
    async def test_function():
        result = await step1_find_relevant_laws(
            "What is Chapter I Article 1 of Civil Law?"
        )
        return result

    result = asyncio.run(test_function())

    print(f"Function returned: {result}")
    print("✅ Success! No proxies error occurred.")

except Exception as e:
    print(f"❌ Error occurred: {e}")
    print(f"Error type: {type(e).__name__}")

    # Check if it's the specific proxies error
    if "proxies" in str(e).lower():
        print("🔍 This is the proxies error we're trying to fix.")
    else:
        print("🔍 This is a different error.")
