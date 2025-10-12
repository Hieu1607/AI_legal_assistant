"""
Business logic for RAG (Retrieval-Augmented Generation) operations
"""

import asyncio
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

# Set up logging
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))

from configs.logger import get_logger, setup_logging
from src.store_vector.weaviate_search import search_relevant_embeddings, get_searcher

setup_logging()
logger = get_logger(__name__)

prompting_time = 0


def get_relevant_sentences(question: str):
    """
    Retrieve relevant sentences for a given question

    Args:
        question (str): The input question

    Returns:
        list: List of relevant sentences or empty list if error occurs
    """
    logger.info("The question is %s", question)
    try:
        relevant_embeddings = search_relevant_embeddings(question, 5)
        relevant_sentences = []
        for sentence in relevant_embeddings["documents"][0]:
            relevant_sentences.append(sentence)
        return relevant_sentences
    except (IndexError, KeyError, FileNotFoundError, ImportError, ValueError) as e:
        logger.info(
            "An error occurred during embedding retrieval: %s", e, exc_info=True
        )
        return []


async def ask_LLM(relevant_sentences: list, question: str):
    """
    Generate answer using LLM based on relevant context

    Args:
        relevant_sentences (list): List of relevant context sentences
        question (str): The user's question

    Returns:
        str: Generated answer from the LLM
    """
    start_prompting_time = time.perf_counter()

    if not relevant_sentences:
        return "Không tìm thấy thông tin liên quan để trả lời câu hỏi của bạn."

    # Create relevant sentences set
    context = ""
    for i, sentence in enumerate(relevant_sentences, 1):
        context += f"Đoạn {i}: {sentence}\n\n"

    prompt = f"""Với vai trò là 1 trợ lý ảo pháp luật, dựa trên các nội dung sau:
        {context}
        Câu hỏi: {question}
        Vui lòng trả lời câu hỏi dựa trên thông tin được cung cấp ở trên.

        Trả lời câu hỏi theo 3 trường hợp
        Trường hợp 1: Nếu tìm thấy nội dung thích hợp trong tài liệu, trả lời 'Theo chương ... điều ... bộ luật abc ..., nội dung'
        Trường hợp 2: Nếu không tìm thấy nội dung thích hợp trong tài liệu, trả lời: 'Không tìm thấy thông tin liên quan đến câu hỏi.'
        Trường hợp 3: Nếu câu hỏi linh tinh hoặc không liên quan đến pháp luật, trả lời: "Chào bạn, tôi đã sẵn sàng trả lời với vai trò là một trợ lý ảo pháp luật.Tuy nhiên, có vẻ như bạn chưa cung cấp câu hỏi cụ thể hoặc câu hỏi của bạn không liên quan đến pháp luật. Vui lòng đặt câu hỏi lại để tôi có thể trả lời."
        Trả lời ngắn gọn.
    """

    end_propting_time = time.perf_counter()
    global prompting_time  # pylint: disable=global-statement
    prompting_time = end_propting_time - start_prompting_time
    # Note: This function is deprecated as we now use Weaviate Query Agent for RAG
    # The Weaviate Query Agent handles both retrieval and generation in one step
    logger.warning("generate_answer_llm is deprecated, use process_rag_query_with_weaviate instead")
    return "Chức năng này đã được thay thế bởi Weaviate Query Agent. Vui lòng sử dụng endpoint RAG mới."


async def process_rag_query_with_weaviate(question: str):
    """
    Process a RAG query using Weaviate Query Agent (retrieval + generation in one step)

    Args:
        question (str): The user's question

    Returns:
        dict: Response containing answer, timing info, metadata, and relevant chunks
    """
    start_time = time.perf_counter()
    searcher = None
    
    try:
        # Use Weaviate Query Agent for integrated retrieval and generation
        searcher = get_searcher()
        result = await searcher.ask_question_with_context(question)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        logger.info("Query Agent processing time = %.4f", total_time)
        logger.info("RAG answer successfully processed by Query Agent")
        
        return {
            "answer": result["answer"].strip(),
            "question": question,
            "relevant_chunks": result["relevant_chunks"],
            "context_count": len(result["relevant_chunks"]),
            "timing": {
                "retrieving_time": 0.0,  # Integrated in Query Agent
                "llm_time": total_time,
                "total_time": total_time,
            },
        }
        
    except Exception as e:
        logger.error(f"Error in Query Agent processing: {e}")
        return {
            "answer": "Đã xảy ra lỗi khi xử lý câu hỏi. Vui lòng thử lại.",
            "question": question,
            "relevant_chunks": [],
            "context_count": 0,
            "timing": {
                "retrieving_time": 0.0,
                "llm_time": 0.0,
                "total_time": 0.0,
            },
        }
    finally:
        # Clean up connections for RAG endpoint
        if searcher:
            searcher.close()


async def process_rag_query(question: str):
    """
    Process a complete RAG query - now uses Weaviate Query Agent by default

    Args:
        question (str): The user's question

    Returns:
        dict: Response containing answer, timing info, and metadata
    """
    # Use the new Weaviate Query Agent method by default
    return await process_rag_query_with_weaviate(question)
