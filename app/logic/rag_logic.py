"""
Business logic for RAG (Retrieval-Augmented Generation) operations
"""

import asyncio
import os
import sys
import time

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

# Set up logging
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))

from configs.logger import get_logger, setup_logging
from services.metrics import CHROMADB_EXCEPTIONS, GROQ_LLM_EXCEPTIONS
from src.store_vector.search_embeddings import search_relevant_embeddings

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
        CHROMADB_EXCEPTIONS.labels(operation="search").inc()
        logger.info(
            "An error occurred during embedding retrieval: %s", e, exc_info=True
        )
        return []


async def ask_LLM(relevant_sentences: list, question: str):
    """
    Generate answer using Groq LLM based on relevant context

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

    prompt = f"""Bạn là một trợ lý ảo pháp luật chuyên nghiệp. Phân tích kỹ câu hỏi và ngữ liệu pháp luật được cung cấp, sau đó trả lời CHÍNH XÁC theo một trong ba trường hợp:

NGỮ LIỆU PHÁP LUẬT:
{context}
CÂU HỎI: {question}

HƯỚNG DẪN XỬ LÝ:
1. ĐỌC KỸ từng đoạn ngữ liệu pháp luật trên
2. TÌM KIẾM thông tin trực tiếp liên quan đến câu hỏi
3. XÁC ĐỊNH chương, điều, bộ luật từ nội dung văn bản (KHÔNG sử dụng "Đoạn 1, Đoạn 2...")

QUY TẮC TRẢ LỜI - TUÂN THỦ NGHIÊM NGẶT:

TRƯỜNG HỢP 1: Tìm thấy thông tin phù hợp trong ngữ liệu
→ Format bắt buộc: "Theo [tên chương cụ thể] [tên điều cụ thể] [tên bộ luật cụ thể], [nội dung trả lời]"
→ VÍ DỤ: "Theo Chương II điều 29 Bộ luật Hàng hải, việc thanh tra kiểm tra về an toàn hàng hải..."
→ LƯU Ý: PHẢI trích xuất tên chương/điều/bộ luật THỰC TẾ từ văn bản, KHÔNG dùng "Đoạn X"

TRƯỜNG HỢP 2: KHÔNG tìm thấy thông tin phù hợp
→ Trả lời CHÍNH XÁC: "Không tìm thấy thông tin liên quan đến câu hỏi."

TRƯỜNG HỢP 3: Câu hỏi không liên quan pháp luật hoặc không rõ ràng  
→ Trả lời CHÍNH XÁC: "Chào bạn, tôi đã sẵn sàng trả lời với vai trò là một trợ lý ảo pháp luật. Tuy nhiên, có vẻ như bạn chưa cung cấp câu hỏi cụ thể hoặc câu hỏi của bạn không liên quan đến pháp luật. Vui lòng đặt câu hỏi lại để tôi có thể trả lời."

CẤM TUYỆT ĐỐI:
- KHÔNG sử dụng "Theo Đoạn 1", "Theo Đoạn 2" trong câu trả lời
- KHÔNG thêm bất kỳ thông tin nào ngoài 3 trường hợp trên
- KHÔNG giải thích lý do chọn trường hợp nào


BẮT ĐẦU TRẢ LỜI:"""

    end_propting_time = time.perf_counter()
    global prompting_time  # pylint: disable=global-statement
    prompting_time = end_propting_time - start_prompting_time

    try:
        # Initialize Groq client
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # Create chat completion
        response = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
                    max_tokens=1024,
                    temperature=0.1,
                ),
            ),
            timeout=60,
        )

        return response.choices[0].message.content

    except asyncio.TimeoutError:
        GROQ_LLM_EXCEPTIONS.labels(
            model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        ).inc()
        return "Hệ thống đang bận vui lòng thử lại sau."
    except ConnectionError as e:
        GROQ_LLM_EXCEPTIONS.labels(
            model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        ).inc()
        logger.info("Network error: %s, retrying...", e)
        try:
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
                        max_tokens=1024,
                        temperature=0.1,
                    ),
                ),
                timeout=15,
            )
            return response.choices[0].message.content
        except asyncio.TimeoutError:
            GROQ_LLM_EXCEPTIONS.labels(
                model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
            ).inc()
            return "Hệ thống đang bận vui lòng thử lại sau."
        except ConnectionError:
            GROQ_LLM_EXCEPTIONS.labels(
                model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
            ).inc()
            logger.info("Retry failed: %s", e)
            return "Lỗi mạng"
    except Exception as e:  # pylint: disable = broad-exception-caught
        GROQ_LLM_EXCEPTIONS.labels(
            model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        ).inc()
        logger.info("An error occured: %s", e)
        return "Lỗi hệ thống, vui lòng thử lại sau."


async def process_rag_query(question: str):
    """
    Process a complete RAG query including retrieval and generation

    Args:
        question (str): The user's question

    Returns:
        dict: Response containing answer, timing info, and metadata
    """
    start_retrieve_time = time.perf_counter()
    relevant_sentences = get_relevant_sentences(question)
    end_retrieve_time = time.perf_counter()
    retrieving_time = end_retrieve_time - start_retrieve_time

    start_ask_LLM_time = time.perf_counter()
    answer = await ask_LLM(relevant_sentences, question)
    end_ask_LLM_time = time.perf_counter()
    llm_time = end_ask_LLM_time - start_ask_LLM_time - prompting_time

    logger.info(
        "retrieving_time = %.4f, prompting_time = %.4f, llm_time = %.4f, total_time = %.4f ",
        retrieving_time,
        prompting_time,
        llm_time,
        retrieving_time + prompting_time + llm_time,
    )
    logger.info("RAG answer successfully")

    return {
        "answer": answer.strip(),
        "question": question,
        "context_count": len(relevant_sentences),
        "timing": {
            "retrieving_time": retrieving_time,
            "llm_time": llm_time,
            "total_time": retrieving_time + prompting_time + llm_time,
        },
    }
