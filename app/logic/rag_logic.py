"""
Business logic for RAG (Retrieval-Augmented Generation) operations
"""

import asyncio
import os
import re
import sys
import time
from difflib import SequenceMatcher

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Set up logging
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))

from configs.logger import get_logger, setup_logging
from services.metrics import CHROMADB_EXCEPTIONS, OPENAI_LLM_EXCEPTIONS
from src.store_vector.search_embeddings import (
    batch_search_relevant_embeddings,
    search_relevant_embeddings,
)

setup_logging()
logger = get_logger(__name__)

prompting_time = 0


def load_titles_from_file(file_path):
    """Read all law titles from titles.txt file"""
    titles = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line:
                    # Remove line numbers at the beginning (e.g., "1. ")
                    title = re.sub(r"^\d+\.\s*", "", line)
                    titles.append(title)
        return titles
    except FileNotFoundError:
        logger.error("File not found: %s", file_path)
        return []


def similarity(a, b):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def extract_year_from_title(title):
    """Extract year from law title"""
    # Find years in the title (prioritize 4-digit years)
    years = re.findall(r"\b(20\d{2}|19\d{2})\b", title)
    if years:
        return int(max(years))  # Get the largest year
    return 0


def extract_base_law_name(law_name):
    """Extract basic law name (remove year, number)"""
    # Remove year and law number
    base_name = re.sub(r"\b(19|20)\d{2}\b", "", law_name)
    base_name = re.sub(r"số\s+\d+[/\w]*", "", base_name)
    base_name = re.sub(r"sửa đổi|bổ sung", "", base_name)
    return base_name.strip()


def is_same_law_type(base_name, title):
    """Check if two laws are of the same type"""
    title_base = extract_base_law_name(title)

    # Compare similarity of base names
    similarity_score = similarity(base_name.lower(), title_base.lower())
    return similarity_score > 0.7


def extract_keywords_from_title(text):
    """Extract important keywords from law name"""
    # Remove unimportant words
    stop_words = {
        "luật",
        "bộ",
        "của",
        "về",
        "và",
        "các",
        "năm",
        "số",
        "sửa",
        "đổi",
        "bổ",
        "sung",
    }

    # Split words and remove punctuation
    words = re.findall(r"\b\w+\b", text.lower())
    keywords = [word for word in words if word not in stop_words and len(word) > 2]

    return keywords


def calculate_keyword_match(keywords, title):
    """Calculate keyword match score"""
    if not keywords:
        return 0

    title_lower = title.lower()
    matched_keywords = 0

    for keyword in keywords:
        if keyword in title_lower:
            matched_keywords += 1

    return matched_keywords / len(keywords)


def group_similar_laws(candidates, llm_input):
    """Group similar laws together"""
    # Extract base law name from LLM input
    base_name = extract_base_law_name(llm_input)

    # Filter candidates that contain the base name
    filtered_candidates = []
    for candidate in candidates:
        if is_same_law_type(base_name, candidate["title"]):
            filtered_candidates.append(candidate)

    return filtered_candidates if filtered_candidates else candidates


def find_best_matches(llm_results, all_titles, threshold=0.3):
    """
    Find best matching titles from LLM results, prioritize latest version
    Args:
        llm_results: List of law names from LLM
        all_titles: List of all titles from titles.txt
        threshold: Minimum similarity threshold
    """
    matches = []

    for llm_law in llm_results:
        llm_law_clean = llm_law.strip()
        if not llm_law_clean:
            continue

        # Find all matching candidates
        candidates = []

        for title in all_titles:
            # Calculate similarity
            score = similarity(llm_law_clean, title)

            # Check if important keywords appear in title
            keywords = extract_keywords_from_title(llm_law_clean)
            keyword_match_score = calculate_keyword_match(keywords, title)

            # Combined score
            combined_score = score * 0.7 + keyword_match_score * 0.3

            if combined_score >= threshold:
                year = extract_year_from_title(title)
                candidates.append(
                    {"title": title, "score": combined_score, "year": year}
                )

        # Sort candidates by score and year (prioritize high score and recent year)
        if candidates:
            # Group candidates of the same law type
            grouped_candidates = group_similar_laws(candidates, llm_law_clean)

            if grouped_candidates:
                # Select the candidate with highest score and most recent year
                best_candidate = max(
                    grouped_candidates, key=lambda x: (x["score"], x["year"])
                )
                matches.append(
                    {
                        "llm_input": llm_law_clean,
                        "exact_title": best_candidate["title"],
                        "confidence": best_candidate["score"],
                    }
                )
            else:
                matches.append(
                    {"llm_input": llm_law_clean, "exact_title": None, "confidence": 0}
                )
        else:
            matches.append(
                {"llm_input": llm_law_clean, "exact_title": None, "confidence": 0}
            )

    return matches


# ================================
# NEW ENHANCED RAG PIPELINE FUNCTIONS
# ================================


async def step1_find_relevant_laws(question: str):
    """
    Step 1: Find 1-2 relevant law codes related to the question

    Args:
        question (str): User's question

    Returns:
        tuple: (found: bool, law_list: list)
    """
    if not question or not question.strip():
        return False, []

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return False, []

    # Simplified prompt to increase stability
    enhanced_prompt = """Hãy xác định bộ luật Việt Nam liên quan đến câu hỏi sau. 

Nếu câu hỏi liên quan đến pháp luật Việt Nam, trả lời tên bộ luật (từ 1-2 bộ luật, mỗi bộ luật trên 1 dòng). 
Nếu không liên quan đến pháp luật, trả lời "Không tìm thấy".

Ví dụ: 

Câu hỏi: "Nam giới phải đi nghĩa vụ quân sự như nào?"

Câu trả lời:
Luật nghĩa vụ quân sự


Câu hỏi:"""

    try:
        client = OpenAI(api_key=api_key)

        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # Using cost-effective model as recommended
            messages=[
                {"role": "user", "content": f"{enhanced_prompt}\n\n{question.strip()}"},
            ],
            temperature=0.1,
            max_tokens=4096,
        )

        result = completion.choices[0].message.content

        # DEBUG: Log raw response
        logger.info("RAW LLM RESPONSE for '%s': '%s'", question, result)

        if not result or not result.strip():
            logger.info("Empty response from LLM")
            return False, []

        result = result.strip()
        logger.info("CLEANED LLM RESPONSE: '%s'", result)

        # Check if LLM returns "Not found"
        if "không tìm thấy" in result.lower():
            logger.info(
                "LLM không tìm thấy bộ luật liên quan cho câu hỏi: %s", question
            )
            return False, []

        # Process results to extract law code names
        law_names = []
        lines = result.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove line start symbols
            line = re.sub(r"^[-•*]\s*", "", line)
            line = re.sub(r"^\d+\.\s*", "", line)
            line = re.sub(r"^[A-Z]\)\s*", "", line)

            line = line.strip()

            # Skip lines that are too short or contain explanatory keywords
            if len(line) < 10 or any(
                keyword in line.lower()
                for keyword in ["giải thích", "lý do", "vì", "do", "tại sao"]
            ):
                continue

            # Only add if it looks like a law code name
            if any(
                keyword in line.lower()
                for keyword in [
                    "luật",
                    "bộ luật",
                    "nghị định",
                    "thông tư",
                    "quyết định",
                ]
            ):
                law_names.append(line)

                # Limit to maximum 2 law codes
                if len(law_names) >= 2:
                    break

        if law_names:
            logger.info("Tìm thấy %d bộ luật: %s", len(law_names), law_names)
            return True, law_names
        else:
            logger.info("Không tìm thấy bộ luật hợp lệ từ LLM response")
            return False, []

    except Exception as e:
        logger.error(
            "Lỗi khi gọi LLM tìm bộ luật - Question: '%s', Error type: %s, Error: %s",
            question,
            type(e).__name__,
            str(e),
            exc_info=True,
        )
        return False, []


async def step3_find_exact_titles(llm_laws: list):
    """
    Step 3: Find the latest law code titles in titles.txt

    Args:
        llm_laws (list): List of law codes from LLM

    Returns:
        list: List of exact names of law codes from titles.txt
    """
    # Read list of all titles
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))

    # Try multiple possible paths for titles.txt (local dev vs Docker)
    possible_paths = [
        os.path.join(project_root, "titles.txt"),  # Local development
        "/app/titles.txt",  # Docker container
        os.path.join(os.getcwd(), "titles.txt"),  # Current working directory
    ]

    titles_path = None
    for path in possible_paths:
        if os.path.exists(path):
            titles_path = path
            break

    if not titles_path:
        logger.error(
            "titles.txt file not found in any of these locations: %s", possible_paths
        )
        return []

    logger.info("Using titles.txt from: %s", titles_path)
    all_titles = load_titles_from_file(titles_path)
    logger.info("Đã load %d titles từ titles.txt", len(all_titles))

    if not all_titles:
        logger.warning("Không thể load titles từ file")
        return []

    # Find the best matching titles
    matches = find_best_matches(llm_laws, all_titles, threshold=0.3)

    # Get the exact titles found
    found_exact_titles = []
    for match in matches:
        if match["exact_title"]:
            found_exact_titles.append(match["exact_title"])
            logger.info(
                "Tìm thấy exact title: %s (confidence: %.2f)",
                match["exact_title"],
                match["confidence"],
            )
        else:
            logger.warning("Không tìm thấy exact title cho: %s", match["llm_input"])

    return found_exact_titles


async def extract_keywords(question: str):
    """
    Extract 3 most relevant legal keywords from the question using LLM

    Args:
        question (str): The input question

    Returns:
        list: List of 3 keywords related to legal topics
    """
    prompt = f"""Từ câu hỏi pháp luật sau, hãy trích xuất chính xác 3 từ khóa/cụm từ quan trọng nhất liên quan đến pháp luật Việt Nam

Câu hỏi: {question}

Yêu cầu:
- Chỉ trả về 3 từ khóa/cụm từ, mỗi từ khóa trên 1 dòng
- Không giải thích, không đánh số
- Tập trung vào khái niệm pháp luật cốt lõi
- Ưu tiên thuật ngữ pháp lý chính thức
- Không trả về luật số bao nhiêu. 

Ví dụ:
Câu hỏi: "Nam giới phải đi nghĩa vụ quân sự như nào?"
Từ khóa:
Nghĩa vụ quân sự
Độ tuổi nghĩa vụ
Nam giới

Từ khóa cho câu hỏi trên:"""

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="gpt-4o-mini",
                    max_tokens=4096,
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


async def enhance_question(question: str):
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
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="gpt-4o-mini",
                    max_tokens=4096,
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


async def step4_extract_keywords_and_enhance(question: str):
    """
    Step 4: Extract 3 important keywords and enhance question in parallel

    Args:
        question (str): Original question

    Returns:
        tuple: (keywords: list, enhanced_question: str)
    """
    # Run in parallel to speed up
    keywords_task = extract_keywords(question)
    enhanced_question_task = enhance_question(question)

    try:
        results = await asyncio.gather(
            keywords_task, enhanced_question_task, return_exceptions=True
        )

        keywords_result, enhanced_question_result = results

        # Handle exceptions and ensure type safety
        if isinstance(keywords_result, Exception):
            logger.error("Lỗi extract keywords: %s", keywords_result)
            keywords = []
        else:
            keywords = keywords_result if keywords_result else []

        if isinstance(enhanced_question_result, Exception):
            logger.error("Lỗi enhance question: %s", enhanced_question_result)
            enhanced_question = question
        else:
            enhanced_question = (
                enhanced_question_result if enhanced_question_result else question
            )

        return keywords, enhanced_question

    except Exception as e:
        logger.error("Lỗi trong step 4: %s", str(e))
        return [], question


async def step5_search_embeddings(
    question: str, keywords: list, enhanced_question: str, exact_titles: list
):
    """
    Step 5: Embeddings and database query with 3 keywords and enhanced question

    Args:
        question (str): Original question
        keywords (list): List of extracted keywords
        enhanced_question (str): Enhanced question
        exact_titles (list): List of exact titles from titles.txt

    Returns:
        list: List of relevant sentences
    """
    logger.info("Bắt đầu search embeddings với %d titles", len(exact_titles))

    # Prepare search queries: enhanced question + keywords
    search_queries = [enhanced_question] + keywords

    try:

        # Prepare batch search with title filtering
        queries_and_titles = []
        results_per_query = min(
            5, max(3, 15 // (len(exact_titles) * len(search_queries)))
        )

        for title in exact_titles:
            for query in search_queries:
                queries_and_titles.append((query, title))

        logger.info(
            "Thực hiện batch search cho %d query-title combinations",
            len(queries_and_titles),
        )

        # Perform asynchronous batch search with timeout
        try:
            search_results = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: batch_search_relevant_embeddings(
                        queries_and_titles, results_per_query
                    ),
                ),
                timeout=60.0,  # 60 second timeout
            )
        except asyncio.TimeoutError:
            logger.warning("Batch search timeout sau 60 giây, chuyển sang fallback")
            raise Exception("Embedding search timeout")

        # Process results and remove duplicates
        all_relevant_sentences = []
        seen_sentences = set()

        for result in search_results:
            if result and result.get("documents") and result["documents"][0]:
                documents = result["documents"][0]
                metadatas = result.get("metadatas", [[]])[0]
                similarities = result.get("cosine_similarities", [[]])[0]

                for i, sentence in enumerate(documents):
                    if sentence not in seen_sentences:
                        seen_sentences.add(sentence)

                        # Get metadata information
                        metadata = metadatas[i] if i < len(metadatas) else {}
                        document_name = metadata.get("title", "Không xác định")
                        similarity_score = (
                            similarities[i] if i < len(similarities) else 0.0
                        )

                        all_relevant_sentences.append(
                            {
                                "sentence": sentence,
                                "document_name": document_name,
                                "similarity": similarity_score,
                            }
                        )

        # Sort by similarity and get top results
        all_relevant_sentences.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        final_results = all_relevant_sentences[:15]  # Get top 15 results

        logger.info(
            "Tìm thấy %d sentences liên quan từ %d titles",
            len(final_results),
            len(exact_titles),
        )

        return final_results

    except Exception as e:
        logger.error("Error in step 5 search embeddings: %s", str(e))
        CHROMADB_EXCEPTIONS.labels(operation="search").inc()

        # Fallback: search without title filtering
        try:
            logger.info("Fallback: search without title filtering")
            queries_and_titles = [(query, None) for query in search_queries]

            search_results = await asyncio.get_event_loop().run_in_executor(
                None, lambda: batch_search_relevant_embeddings(queries_and_titles, 5)
            )

            fallback_sentences = []
            seen_sentences = set()

            for result in search_results:
                if result and result.get("documents") and result["documents"][0]:
                    documents = result["documents"][0]
                    metadatas = result.get("metadatas", [[]])[0]

                    for i, sentence in enumerate(documents):
                        if sentence not in seen_sentences:
                            seen_sentences.add(sentence)
                            metadata = metadatas[i] if i < len(metadatas) else {}

                            fallback_sentences.append(
                                {
                                    "sentence": sentence,
                                    "document_name": metadata.get(
                                        "title", "Không xác định"
                                    ),
                                }
                            )

            return fallback_sentences[:10]  # Lấy top 10 cho fallback

        except Exception as fallback_error:
            logger.error("Fallback search cũng thất bại: %s", str(fallback_error))
            return []


async def ask_LLM(relevant_sentences: list, question: str):
    """
    Generate answer using OpenAI LLM based on relevant context

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
            document_name = item.get("document_name", "Không xác định")
            context += f"Đoạn {i}: {sentence}\n[Nguồn: {document_name}]\n\n"
        else:
            # Fallback for old format
            context += f"Đoạn {i}: {item}\n[Nguồn: Không xác định]\n\n"

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
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Create chat completion
        response = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="gpt-4o-mini",
                    max_tokens=4096,
                    temperature=0.1,
                ),
            ),
            timeout=60,
        )

        return response.choices[0].message.content

    except asyncio.TimeoutError:
        OPENAI_LLM_EXCEPTIONS.labels(model="gpt-4o-mini").inc()
        return "Hệ thống đang bận vui lòng thử lại sau."
    except ConnectionError as e:
        OPENAI_LLM_EXCEPTIONS.labels(model="gpt-4o-mini").inc()
        logger.info("Network error: %s, retrying...", e)
        try:
            # Retry once
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: client.chat.completions.create(
                        messages=[{"role": "user", "content": prompt}],
                        model="gpt-4o-mini",
                        max_tokens=4096,
                        temperature=0.1,
                    ),
                ),
                timeout=60,
            )
            return response.choices[0].message.content
        except asyncio.TimeoutError:
            return "Hệ thống đang bận vui lòng thử lại sau."
        except ConnectionError:
            return "Lỗi kết nối, vui lòng thử lại sau."
    except Exception as e:  # pylint: disable = broad-exception-caught
        OPENAI_LLM_EXCEPTIONS.labels(model="gpt-4o-mini").inc()
        logger.info("An error occured: %s", e)
        return "Lỗi hệ thống, vui lòng thử lại sau."


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
            document_name = "Không xác định"
            if i < len(metadatas) and metadatas[i]:
                metadata = metadatas[i]
                document_name = metadata.get("title", "Không xác định")

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


async def process_rag_query_new(question: str):
    """
    PIPELINE RAG MỚI - 7 BƯỚC THEO YÊU CẦU

    Args:
        question (str): Câu hỏi từ người dùng

    Returns:
        dict: Response chứa answer, timing info và metadata
    """
    total_start_time = time.perf_counter()

    logger.info("Bắt đầu pipeline RAG mới cho câu hỏi: %s", question)

    try:
        # BƯỚC 1: Tìm kiếm 1-2 bộ luật liên quan
        step1_start = time.perf_counter()
        has_laws, llm_laws = await step1_find_relevant_laws(question)
        step1_time = time.perf_counter() - step1_start

        # BƯỚC 2: Kiểm tra kết quả bước 1
        if not has_laws:
            logger.info("Bước 1: Không tìm thấy bộ luật liên quan")
            return {
                "answer": "Câu hỏi không rõ ràng hoặc không liên quan đến pháp luật. Vui lòng thử lại.",
                "question": question,
                "enhanced_question": question,
                "keywords": [],
                "relevant_titles": [],
                "context_count": 0,
                "relevant_chunks": [],
                "timing": {
                    "step1_time": step1_time,
                    "step2_time": 0,
                    "step3_time": 0,
                    "step4_time": 0,
                    "step5_time": 0,
                    "step6_time": 0,
                    "total_time": time.perf_counter() - total_start_time,
                },
                "pipeline_stopped_at": "step_2",
            }

        logger.info("Bước 1: Tìm thấy %d bộ luật: %s", len(llm_laws), llm_laws)

        # BƯỚC 3: Tìm exact titles trong titles.txt
        step3_start = time.perf_counter()
        exact_titles = await step3_find_exact_titles(llm_laws)
        step3_time = time.perf_counter() - step3_start

        if not exact_titles:
            logger.warning("Bước 3: Không tìm thấy exact titles, dùng fallback")
            exact_titles = []

        logger.info("Bước 3: Tìm thấy %d exact titles", len(exact_titles))

        # BƯỚC 4: Extract keywords và enhance question song song
        step4_start = time.perf_counter()
        try:
            keywords_result, enhanced_question_result = (
                await step4_extract_keywords_and_enhance(question)
            )
            keywords = keywords_result if isinstance(keywords_result, list) else []
            enhanced_question = (
                enhanced_question_result
                if isinstance(enhanced_question_result, str)
                else question
            )
        except Exception as e:
            logger.error("Lỗi trong step 4: %s", str(e))
            keywords = []
            enhanced_question = question

        step4_time = time.perf_counter() - step4_start

        logger.info("Bước 4: Extract %d keywords, enhanced question", len(keywords))

        # BƯỚC 5: Search embeddings với metadata filtering
        step5_start = time.perf_counter()
        if exact_titles:
            relevant_sentences = await step5_search_embeddings(
                question, keywords, enhanced_question, exact_titles
            )
        else:
            # Fallback: search không có title filtering
            search_queries = [enhanced_question] + keywords
            queries_and_titles = [(query, None) for query in search_queries]

            search_results = await asyncio.get_event_loop().run_in_executor(
                None, lambda: batch_search_relevant_embeddings(queries_and_titles, 5)
            )

            relevant_sentences = []
            seen_sentences = set()

            for result in search_results:
                if result and result.get("documents") and result["documents"][0]:
                    documents = result["documents"][0]
                    metadatas = result.get("metadatas", [[]])[0]

                    for i, sentence in enumerate(documents):
                        if sentence not in seen_sentences:
                            seen_sentences.add(sentence)
                            metadata = metadatas[i] if i < len(metadatas) else {}

                            relevant_sentences.append(
                                {
                                    "sentence": sentence,
                                    "document_name": metadata.get(
                                        "title", "Không xác định"
                                    ),
                                }
                            )

            relevant_sentences = relevant_sentences[:10]

        step5_time = time.perf_counter() - step5_start

        logger.info("Bước 5: Tìm thấy %d relevant sentences", len(relevant_sentences))

        # BƯỚC 6: Tạo prompt và hỏi LLM
        step6_start = time.perf_counter()
        answer = await ask_LLM(relevant_sentences, question)
        step6_time = time.perf_counter() - step6_start

        total_time = time.perf_counter() - total_start_time

        logger.info("Pipeline hoàn thành trong %.4f giây", total_time)

        # BƯỚC 7: Return kết quả
        return {
            "answer": answer.strip() if answer else "Không thể tạo câu trả lời.",
            "question": question,
            "enhanced_question": enhanced_question,
            "keywords": keywords,
            "relevant_titles": exact_titles,
            "context_count": len(relevant_sentences),
            "relevant_chunks": relevant_sentences,
            "timing": {
                "step1_time": step1_time,
                "step2_time": 0,  # Logic check, no time consumed
                "step3_time": step3_time,
                "step4_time": step4_time,
                "step5_time": step5_time,
                "step6_time": step6_time,
                "total_time": total_time,
            },
            "pipeline_stopped_at": "completed",
        }

    except Exception as e:
        logger.error("Lỗi trong pipeline RAG mới: %s", str(e), exc_info=True)

        # Fallback về method cũ đơn giản
        logger.info("Fallback về method đơn giản")

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
            "answer": answer.strip() if answer else "Không thể tạo câu trả lời.",
            "question": question,
            "enhanced_question": question,
            "keywords": [],
            "relevant_titles": [],
            "context_count": len(relevant_sentences),
            "relevant_chunks": relevant_sentences,
            "timing": {
                "step1_time": 0,
                "step2_time": 0,
                "step3_time": 0,
                "step4_time": 0,
                "step5_time": retrieving_time,
                "step6_time": llm_time,
                "total_time": total_time,
            },
            "pipeline_stopped_at": "fallback",
        }


# Main function - sử dụng pipeline mới
async def process_rag_query(question: str):
    """
    Entry point cho RAG query - sử dụng pipeline mới 7 bước
    """
    return await process_rag_query_new(question)


async def test_title_based_rag(question: str):
    """
    Test function cho pipeline RAG mới

    Args:
        question (str): Câu hỏi test

    Returns:
        dict: Kết quả RAG response với pipeline mới
    """
    logger.info("Testing new RAG pipeline với câu hỏi: %s", question)
    result = await process_rag_query_new(question)

    logger.info(
        "Test hoàn thành. Tìm thấy %d chunks từ %d titles: %s",
        result["context_count"],
        len(result["relevant_titles"]),
        result["relevant_titles"],
    )

    return result
