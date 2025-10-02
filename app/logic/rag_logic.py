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


async def extract_keywords(question: str) -> list:
    """
    Extract 3 most relevant legal keywords from the question using LLM

    Args:
        question (str): The input question

    Returns:
        list: List of 3 keywords related to legal topics
    """
    prompt = f"""Từ câu hỏi pháp luật sau, hãy trích xuất chính xác 3 từ khóa/cụm từ quan trọng nhất liên quan đến pháp luật Việt Nam và bộ luật mới nhất đi kèm.

Câu hỏi: {question}

Yêu cầu:
- Chỉ trả về 3 từ khóa/cụm từ, mỗi từ khóa trên 1 dòng
- Không giải thích, không đánh số
- Tập trung vào khái niệm pháp luật cốt lõi
- Ưu tiên thuật ngữ pháp lý chính thức

Ví dụ:
Câu hỏi: "Nam giới phải đi nghĩa vụ quân sự như nào?"
Từ khóa:
Nghĩa vụ quân sự Luật nghĩa vụ quân sự 2015
Độ tuổi nghĩa vụ Luật nghĩa vụ quân sự 2015
Nam giới Luật nghĩa vụ quân sự 2015

Từ khóa cho câu hỏi trên:"""

    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=os.getenv("LLM_MODEL", "openai/gpt-oss-20b"),
                    max_tokens=2000,
                    temperature=0.1,
                ),
            ),
            timeout=15,
        )

        content = response.choices[0].message.content
        if content:
            # Parse keywords from response - split by lines and clean
            keywords = [kw.strip() for kw in content.strip().split("\n") if kw.strip()]
            return keywords[:3]  # Ensure only 3 keywords
        return []

    except Exception as e:
        logger.error("Error extracting keywords: %s", e)
        return []


async def enhance_question(question: str) -> str:
    """
    Enhance the original question for better embedding search

    Args:
        question (str): The original question

    Returns:
        str: Enhanced question optimized for embedding search
    """
    prompt = f"""Hãy viết lại câu hỏi sau để tối ưu cho việc tìm kiếm trong cơ sở dữ liệu pháp luật Việt Nam.

Câu hỏi gốc: {question}

Yêu cầu:
- Sử dụng thuật ngữ pháp lý chính thức
- Mở rộng ngữ cảnh để bao gồm các khái niệm liên quan
- Làm rõ ý định tìm kiếm
- Giữ nguyên ý nghĩa chính
- Trả về chỉ câu hỏi được cải thiện, không giải thích

Ví dụ:
Gốc: "Tuổi nghỉ hưu là bao nhiêu?"
Cải thiện: "Tuổi nghỉ hưu theo quy định pháp luật lao động Việt Nam đối với nam giới và nữ giới trong các ngành nghề khác nhau"

Câu hỏi được cải thiện:"""

    try:
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=os.getenv("LLM_MODEL", "openai/gpt-oss-20b"),
                    max_tokens=2000,
                    temperature=0.1,
                ),
            ),
            timeout=15,
        )

        enhanced = response.choices[0].message.content
        return enhanced.strip() if enhanced else question

    except Exception as e:
        logger.error("Error enhancing question: %s", e)
        return question


async def get_relevant_sentences_enhanced(
    question: str, keywords: list, enhanced_question: str
):
    """
    Retrieve relevant sentences using keywords and enhanced question

    Args:
        question (str): Original question
        keywords (list): List of extracted keywords
        enhanced_question (str): Enhanced version of the question

    Returns:
        list: List of dictionaries containing sentence and document name
    """
    logger.info("Original question: %s", question)
    logger.info("Keywords: %s", keywords)
    logger.info("Enhanced question: %s", enhanced_question)

    try:
        # Search with enhanced question and keywords
        search_queries = [enhanced_question] + keywords
        all_relevant_sentences = []

        # Use asyncio.gather to search all queries concurrently
        search_tasks = []
        for query in search_queries:
            task = asyncio.get_event_loop().run_in_executor(
                None, lambda q=query: search_relevant_embeddings(q, 3)
            )
            search_tasks.append(task)

        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Process results from all searches
        seen_sentences = set()  # To avoid duplicates

        for result in search_results:
            if isinstance(result, Exception):
                logger.warning("Search failed for a query: %s", result)
                continue

            documents = result["documents"][0] if result["documents"] else []
            metadatas = result["metadatas"][0] if result["metadatas"] else []

            for i, sentence in enumerate(documents):
                # Skip duplicates
                if sentence in seen_sentences:
                    continue
                seen_sentences.add(sentence)

                # Extract document name from metadata
                document_name = "Unknown Document"
                if i < len(metadatas) and metadatas[i]:
                    metadata = metadatas[i]
                    document_name = metadata.get("title", "Unknown Document")

                all_relevant_sentences.append(
                    {"sentence": sentence, "document_name": document_name}
                )

        return all_relevant_sentences

    except Exception as e:  # pylint: disable = broad-exception-caught
        CHROMADB_EXCEPTIONS.labels(operation="search").inc()
        logger.error("Error in enhanced sentence retrieval: %s", e, exc_info=True)
        return []


def get_relevant_sentences(question: str):
    """
    Retrieve relevant sentences for a given question (fallback method)

    Args:
        question (str): The input question

    Returns:
        list: List of dictionaries containing sentence and document name,
              or empty list if error occurs
              Format: [{"sentence": str, "document_name": str}, ...]
    """
    logger.info("Using fallback method for question: %s", question)
    try:
        relevant_embeddings = search_relevant_embeddings(question, 5)
        relevant_sentences = []
        documents = (
            relevant_embeddings["documents"][0]
            if relevant_embeddings["documents"]
            else []
        )
        metadatas = (
            relevant_embeddings["metadatas"][0]
            if relevant_embeddings["metadatas"]
            else []
        )

        for i, sentence in enumerate(documents):
            # Extract document name from metadata, default to "Unknown Document" if not available
            document_name = "Unknown Document"
            if i < len(metadatas) and metadatas[i]:
                metadata = metadatas[i]
                # Use title field from metadata which contains the document name
                document_name = metadata.get("title", "Unknown Document")

            relevant_sentences.append(
                {"sentence": sentence, "document_name": document_name}
            )
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

    prompt = f"""Bạn là một trợ lý ảo pháp luật chuyên nghiệp. Phân tích kỹ câu hỏi và ngữ liệu pháp luật được cung cấp, sau đó trả lời CHÍNH XÁC theo một trong hai trường hợp:

NGỮ LIỆU PHÁP LUẬT:
{context}
CÂU HỎI: {question}

HƯỚNG DẪN XỬ LÝ:
1. ĐỌC KỸ từng đoạn ngữ liệu pháp luật trên cùng với tên văn bản đi kèm
2. TÌM KIẾM thông tin trực tiếp liên quan đến câu hỏi
3. XÁC ĐỊNH chương, điều, và TÊN VĂN BẢN CHÍNH XÁC từ thông tin được cung cấp

QUY TẮC TRẢ LỜI - TUÂN THỦ NGHIÊM NGẶT:

TRƯỜNG HỢP 1: Tìm thấy thông tin phù hợp trong ngữ liệu
→ Format bắt buộc: "Theo [điểm cụ thể nếu có] [khoản cụ thể nếu có] [điều cụ thể] [chương cụ thể] của [tên văn bản chính xác], [nội dung trả lời]"
→ VÍ DỤ: "Theo điểm 1 khoản 1 Điều 29 chương II của Luật Hàng hải Việt Nam, việc thanh tra kiểm tra về an toàn hàng hải..."
→ LƯU Ý 1: PHẢI sử dụng tên văn bản CHÍNH XÁC từ thông tin được cung cấp trong [Nguồn: ...] , đồng thời diễn tả lại nội dung trả lời cho dễ nghe, không sao chép nguyên văn
→ LƯU Ý 2: Có thể kết hợp nhiều điều luật, chương luật từ các đoạn khác nhau nếu cần thiết để trả lời đầy đủ câu hỏi
→ LƯU Ý 3: Nếu trong Ngữ liệu pháp luật không có thông tin liên quan đến câu hỏi, tự trả lời 'Tôi không có đủ thông tin để trả lời câu hỏi của bạn.'
TRƯỜNG HỢP 2: Câu hỏi không liên quan đến pháp luật hoặc không rõ ràng
→ Trả lời CHÍNH XÁC: "Câu hỏi không liên quan đến pháp luật hoặc không rõ ràng. Vui lòng đặt câu hỏi lại."

CẤM TUYỆT ĐỐI:
- KHÔNG sử dụng "Theo Đoạn 1", "Theo Đoạn 2" trong câu trả lời
- KHÔNG thêm bất kỳ thông tin nào ngoài 2 trường hợp trên
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
                    model=os.getenv("LLM_MODEL", "openai/gpt-oss-20b"),
                    max_tokens=1024,
                    temperature=0.1,
                ),
            ),
            timeout=60,
        )

        return response.choices[0].message.content

    except asyncio.TimeoutError:
        GROQ_LLM_EXCEPTIONS.labels(
            model=os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
        ).inc()
        return "Hệ thống đang bận vui lòng thử lại sau."
    except ConnectionError as e:
        GROQ_LLM_EXCEPTIONS.labels(
            model=os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
        ).inc()
        logger.info("Network error: %s, retrying...", e)
        try:
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model=os.getenv("LLM_MODEL", "openai/gpt-oss-20b"),
                        max_tokens=1024,
                        temperature=0.1,
                    ),
                ),
                timeout=15,
            )
            return response.choices[0].message.content
        except asyncio.TimeoutError:
            GROQ_LLM_EXCEPTIONS.labels(
                model=os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
            ).inc()
            return "Hệ thống đang bận vui lòng thử lại sau."
        except ConnectionError:
            GROQ_LLM_EXCEPTIONS.labels(
                model=os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
            ).inc()
            logger.info("Retry failed: %s", e)
            return "Lỗi mạng"
    except Exception as e:  # pylint: disable = broad-exception-caught
        GROQ_LLM_EXCEPTIONS.labels(
            model=os.getenv("LLM_MODEL", "openai/gpt-oss-20b")
        ).inc()
        logger.info("An error occured: %s", e)
        return "Lỗi hệ thống, vui lòng thử lại sau."


async def process_rag_query(question: str):
    """
    Process a complete RAG query with enhanced retrieval pipeline

    Args:
        question (str): The user's question

    Returns:
        dict: Response containing answer, timing info, and metadata
    """
    total_start_time = time.perf_counter()

    # Step 1 & 2: Extract keywords and enhance question concurrently
    logger.info("Starting keyword extraction and question enhancement")
    step1_start = time.perf_counter()

    try:
        # Run keyword extraction and question enhancement in parallel
        keywords_task = extract_keywords(question)
        enhanced_question_task = enhance_question(question)

        keywords, enhanced_question = await asyncio.gather(
            keywords_task, enhanced_question_task, return_exceptions=True
        )

        # Handle exceptions
        if isinstance(keywords, Exception):
            logger.warning("Keyword extraction failed: %s", keywords)
            keywords = []
        if isinstance(enhanced_question, Exception):
            logger.warning("Question enhancement failed: %s", enhanced_question)
            enhanced_question = question

        step1_end = time.perf_counter()
        enhancement_time = step1_end - step1_start

        logger.info("Enhancement completed in %.4f seconds", enhancement_time)
        logger.info("Keywords: %s", keywords)
        logger.info("Enhanced question: %s", enhanced_question)

        # Step 3: Enhanced retrieval
        start_retrieve_time = time.perf_counter()

        if keywords and enhanced_question != question:
            # Use enhanced retrieval if both steps succeeded
            relevant_sentences = await get_relevant_sentences_enhanced(
                question, keywords, enhanced_question
            )
        else:
            # Fallback to original method
            logger.info("Using fallback retrieval method")
            relevant_sentences = get_relevant_sentences(question)

        end_retrieve_time = time.perf_counter()
        retrieving_time = end_retrieve_time - start_retrieve_time

        # Generate answer
        start_ask_LLM_time = time.perf_counter()
        answer = await ask_LLM(relevant_sentences, question)
        end_ask_LLM_time = time.perf_counter()
        llm_time = end_ask_LLM_time - start_ask_LLM_time - prompting_time

        total_time = time.perf_counter() - total_start_time

        logger.info(
            "Pipeline timing - enhancement: %.4f, retrieving: %.4f, prompting: %.4f, llm: %.4f, total: %.4f",
            enhancement_time,
            retrieving_time,
            prompting_time,
            llm_time,
            total_time,
        )
        logger.info("Enhanced RAG pipeline completed successfully")

        return {
            "answer": answer.strip(),
            "question": question,
            "enhanced_question": enhanced_question,
            "keywords": keywords,
            "context_count": len(relevant_sentences),
            "relevant_chunks": relevant_sentences,
            "timing": {
                "enhancement_time": enhancement_time,
                "retrieving_time": retrieving_time,
                "llm_time": llm_time,
                "total_time": total_time,
            },
        }

    except Exception as e:
        logger.error("Error in enhanced RAG pipeline: %s", e, exc_info=True)
        # Fallback to original simple method
        logger.info("Falling back to simple RAG pipeline")

        start_retrieve_time = time.perf_counter()
        relevant_sentences = get_relevant_sentences(question)
        end_retrieve_time = time.perf_counter()
        retrieving_time = end_retrieve_time - start_retrieve_time

        start_ask_LLM_time = time.perf_counter()
        answer = await ask_LLM(relevant_sentences, question)
        end_ask_LLM_time = time.perf_counter()
        llm_time = end_ask_LLM_time - start_ask_LLM_time - prompting_time

        total_time = time.perf_counter() - total_start_time

        return {
            "answer": answer.strip(),
            "question": question,
            "enhanced_question": question,  # Same as original
            "keywords": [],
            "context_count": len(relevant_sentences),
            "relevant_chunks": relevant_sentences,
            "timing": {
                "enhancement_time": 0,
                "retrieving_time": retrieving_time,
                "llm_time": llm_time,
                "total_time": total_time,
            },
        }
