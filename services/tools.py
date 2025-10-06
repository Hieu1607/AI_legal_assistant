import asyncio
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
from pydantic import BaseModel

root = os.getcwd()
sys.path.insert(0, str(root))
from configs.logger import get_logger_app, setup_logging

setup_logging()
logger = get_logger_app(__name__)
from services.metrics import (
    CHROMADB_EXCEPTIONS,
    HF_EMBEDDINGS_EXCEPTIONS,
    OPENAI_LLM_EXCEPTIONS,
)
from src.store_vector.search_embeddings import search_relevant_embeddings

# Import metrics functions
try:
    from app.logic.metrics_logic import increment_openai_tokens
except ImportError:
    # Fallback if import fails
    def increment_openai_tokens(token_type: str, count: int = 1):
        pass


class RetrieveInput(BaseModel):
    question: str
    top_k: int


class RetrieveOutput(BaseModel):
    chunks: list[str]


class GenerateInput(BaseModel):
    question: str
    chunks: list[str]


class GenerateOutput(BaseModel):
    answer: str


class FormatInput(BaseModel):
    answer: str
    chunks: list[str]


class FormatOutput(BaseModel):
    formatted_answer: str


def retrieve_laws(data: RetrieveInput) -> RetrieveOutput:
    try:
        logger.info("Question: %s, number of chunks: %d", data.question, data.top_k)
        relevant_embeddings = search_relevant_embeddings(data.question, data.top_k)
        # relevant_embeddings["documents"] returns nested list, need to flatten it
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

        # Combine documents with metadata for document names
        chunks = []
        for i, sentence in enumerate(documents):
            # Extract document name from metadata
            document_name = "Unknown Document"
            if i < len(metadatas) and metadatas[i]:
                metadata = metadatas[i]
                # Use title field which contains the legal document name
                document_name = metadata.get("title", "Unknown Document")

            # Format: "sentence [Document: document_name]"
            formatted_chunk = f"{sentence} [Nguồn: {document_name}]"
            chunks.append(formatted_chunk)

        return RetrieveOutput(chunks=chunks)
    except (ValueError, KeyError, ImportError, OSError) as e:
        CHROMADB_EXCEPTIONS.labels(operation="retrieve").inc()
        logger.error("An error occurred: %s", e)
        return RetrieveOutput(chunks=[])


async def generate_answer(data: GenerateInput) -> GenerateOutput:
    relevant_sentences = data.chunks
    logger.info("Question: %s, chunks: %s", data.question, data.chunks)
    if not relevant_sentences:
        return GenerateOutput(
            answer="Không tìm thấy thông tin liên quan để trả lời câu hỏi của bạn."
        )
    # Create a string containing all sentences from relevant_sentences
    context = ""
    for i, sentence in enumerate(relevant_sentences, 1):
        context += f"Đoạn {i}: {sentence}\n"

    prompt = f"""Bạn là một trợ lý ảo pháp luật chuyên nghiệp. Phân tích kỹ câu hỏi và ngữ liệu pháp luật được cung cấp, sau đó trả lời CHÍNH XÁC theo một trong hai trường hợp:
NGỮ LIỆU PHÁP LUẬT:
{context}
CÂU HỎI: {data.question}

HƯỚNG DẪN XỬ LÝ:
1. ĐỌC KỸ từng đoạn ngữ liệu pháp luật trên cùng với nguồn văn bản đi kèm
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
- KHÔNG sử dụng "[Nguồn: ...]" trong câu trả lời, chỉ sử dụng để xác định tên văn bản
- KHÔNG thêm bất kỳ thông tin nào ngoài 2 trường hợp trên
- KHÔNG giải thích lý do chọn trường hợp nào


BẮT ĐẦU TRẢ LỜI:"""
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Use loop.run_in_executor to run sync function in a separate thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
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
        answer = response.choices[0].message.content

        # Track token usage if available
        if hasattr(response, "usage") and response.usage:
            if hasattr(response.usage, "prompt_tokens"):
                increment_openai_tokens("input", response.usage.prompt_tokens)
            if hasattr(response.usage, "completion_tokens"):
                increment_openai_tokens("output", response.usage.completion_tokens)
            if hasattr(response.usage, "total_tokens"):
                increment_openai_tokens("total", response.usage.total_tokens)

        logger.info("The answer from LLM is %s", answer)
        return GenerateOutput(answer=answer)
    except asyncio.TimeoutError:
        OPENAI_LLM_EXCEPTIONS.labels(model="gpt-4o-mini").inc()
        return GenerateOutput(answer="Hệ thống đang bận vui lòng thử lại sau.")
    except ConnectionError as e:
        OPENAI_LLM_EXCEPTIONS.labels(model="gpt-4o-mini").inc()
        logger.info("Network error: %s, retrying...", e)
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
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

            # Track token usage if available
            if hasattr(response, "usage") and response.usage:
                if hasattr(response.usage, "prompt_tokens"):
                    increment_openai_tokens("input", response.usage.prompt_tokens)
                if hasattr(response.usage, "completion_tokens"):
                    increment_openai_tokens("output", response.usage.completion_tokens)
                if hasattr(response.usage, "total_tokens"):
                    increment_openai_tokens("total", response.usage.total_tokens)

            return GenerateOutput(answer=response.choices[0].message.content)
        except asyncio.TimeoutError:
            OPENAI_LLM_EXCEPTIONS.labels(model="gpt-4o-mini").inc()
            return GenerateOutput(answer="Hệ thống đang bận vui lòng thử lại sau.")
        except ConnectionError:
            OPENAI_LLM_EXCEPTIONS.labels(model="gpt-4o-mini").inc()
            logger.info("Retry failed: %s", e)
            return GenerateOutput(answer="Lỗi mạng")
    except Exception as e:  # pylint: disable = broad-exception-caught
        OPENAI_LLM_EXCEPTIONS.labels(model="gpt-4o-mini").inc()
        logger.info("An error occured: %s", e)
        return GenerateOutput(answer="Lỗi hệ thống, vui lòng thử lại sau.")


def format_citation(data: FormatInput) -> FormatOutput:
    try:
        answer = data.answer
        chunks = data.chunks
        context = ""
        for i, sentence in enumerate(chunks, 1):
            context += f"Đoạn {i}: {sentence}\n"
        new_answer = f"{answer}\nNguồn:\n{context}"
        logger.info("The formatted answer is \n%s", new_answer)
        return FormatOutput(formatted_answer=new_answer)
    except (ValueError, OSError, ImportError, KeyError) as e:
        logger.error("An error occurred: %s", e)
        return FormatOutput(formatted_answer="Cannot format the answer")


if __name__ == "__main__":
    chunks = retrieve_laws(
        RetrieveInput(question="Chương II điều 29 luật hàng hải nói gì?", top_k=5)
    )

    async def main():
        res = await generate_answer(
            GenerateInput(
                question="Chương II điều 29 luật hàng hải nói gì?", chunks=chunks.chunks
            )
        )
        answer = format_citation(FormatInput(answer=res.answer, chunks=chunks.chunks))
        print(answer.formatted_answer)

    asyncio.run(main())
