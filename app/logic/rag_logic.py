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
        list: List of dictionaries containing sentence and document name, 
              or empty list if error occurs
              Format: [{"sentence": str, "document_name": str}, ...]
    """
    logger.info("The question is %s", question)
    try:
        relevant_embeddings = search_relevant_embeddings(question, 5)
        relevant_sentences = []
        documents = relevant_embeddings["documents"][0] if relevant_embeddings["documents"] else []
        metadatas = relevant_embeddings["metadatas"][0] if relevant_embeddings["metadatas"] else []
        
        for i, sentence in enumerate(documents):
            # Extract document name from metadata, default to "Unknown Document" if not available
            document_name = "Unknown Document"
            if i < len(metadatas) and metadatas[i]:
                metadata = metadatas[i]
                # Use title field from metadata which contains the document name
                document_name = metadata.get("title", "Unknown Document")
            
            relevant_sentences.append({
                "sentence": sentence,
                "document_name": document_name
            })
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

    # Create relevant sentences set with document names
    context = ""
    for i, item in enumerate(relevant_sentences, 1):
        if isinstance(item, dict):
            sentence = item.get("sentence", "")
            document_name = item.get("document_name", "Unknown Document")
            context += f"Đoạn {i} (Từ {document_name}): {sentence}\n\n"
        else:
            # Backward compatibility for old format
            context += f"Đoạn {i}: {item}\n\n"

    prompt = f"""Bạn là một trợ lý ảo pháp luật chuyên nghiệp. Phân tích kỹ câu hỏi và trả lời CHÍNH XÁC theo một trong hai trường hợp:

CÂU HỎI: {question}

HƯỚNG DẪN XỬ LÝ:
1. TÌM KIẾM thông tin trực tiếp liên quan đến câu hỏi
2. XÁC ĐỊNH chương, điều, và TÊN VĂN BẢN CHÍNH XÁC 

QUY TẮC TRẢ LỜI - TUÂN THỦ NGHIÊM NGẶT:

TRƯỜNG HỢP 1: Tìm thấy thông tin phù hợp trong ngữ liệu
→ Format bắt buộc: "Theo [điểm cụ thể nếu có] [khoản cụ thể nếu có] [điều cụ thể] [chương cụ thể] của [tên văn bản chính xác], [nội dung trả lời]"
→ VÍ DỤ: "Theo điểm 1 khoản 1 Điều 29 chương II của Luật Hàng hải Việt Nam, việc thanh tra kiểm tra về an toàn hàng hải..."
→ LƯU Ý 1: PHẢI sử dụng tên văn bản CHÍNH XÁC ,đồng thời diễn tả lại nội dung trả lời cho dễ nghe, không sao chép nguyên văn
 → LƯU Ý 2: Tự trả lời theo thông tin bạn có về pháp luật Việt Nam theo format trên. Nếu chính bản thân không có thông tin, hãy trả lời 'Tôi không có đủ thông tin để trả lời câu hỏi của bạn.'
TRƯỜNG HỢP 2: Câu hỏi không liên quan đến lĩnh vực pháp luật hoặc không rõ ràng, không thể hiểu được
→ Trả lời CHÍNH XÁC: "Câu hỏi không liên quan đến pháp luật hoặc không rõ ràng. Vui lòng đặt câu hỏi lại."

CẤM TUYỆT ĐỐI:
- KHÔNG thêm bất kỳ thông tin nào ngoài 2 trường hợp trên
- KHÔNG giải thích lý do chọn trường hợp nào
- Chỉ trả lời trong 1 dòng duy nhất, không cách dòng
- Chỉ sử dụng các luật từ năm 2024 trở về trước
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
