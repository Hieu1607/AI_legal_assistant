import asyncio
import os
import sys

from dotenv import load_dotenv
from groq import Groq

load_dotenv()
from pydantic import BaseModel

root = os.getcwd()
sys.path.insert(0, str(root))
from configs.logger import get_logger_app, setup_logging

setup_logging()
logger = get_logger_app(__name__)
from src.store_vector.search_embeddings import search_relevant_embeddings

# Import metrics functions
try:
    from app.logic.metrics_logic import increment_groq_tokens
except ImportError:
    # Fallback if import fails
    def increment_groq_tokens(token_type: str, count: int = 1):
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
        chunks = (
            relevant_embeddings["documents"][0]
            if relevant_embeddings["documents"]
            else []
        )
        return RetrieveOutput(chunks=chunks)
    except (ValueError, KeyError, ImportError, OSError) as e:
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

    prompt = f"""Bạn là một trợ lý ảo pháp luật chuyên nghiệp. Phân tích kỹ câu hỏi và ngữ liệu pháp luật được cung cấp, sau đó trả lời CHÍNH XÁC theo một trong ba trường hợp:
NGỮ LIỆU PHÁP LUẬT:
{context}
CÂU HỎI: {data.question}

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
    try:
        # Initialize Groq client
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))

        # Use loop.run_in_executor to run sync function in a separate thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
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
        answer = response.choices[0].message.content

        # Track token usage if available
        if hasattr(response, "usage") and response.usage:
            if hasattr(response.usage, "prompt_tokens"):
                increment_groq_tokens("input", response.usage.prompt_tokens)
            if hasattr(response.usage, "completion_tokens"):
                increment_groq_tokens("output", response.usage.completion_tokens)
            if hasattr(response.usage, "total_tokens"):
                increment_groq_tokens("total", response.usage.total_tokens)

        logger.info("The answer from LLM is %s", answer)
        return GenerateOutput(answer=answer)
    except asyncio.TimeoutError:
        return GenerateOutput(answer="Hệ thống đang bận vui lòng thử lại sau.")
    except ConnectionError as e:
        logger.info("Network error: %s, retrying...", e)
        try:
            client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(
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

            # Track token usage if available
            if hasattr(response, "usage") and response.usage:
                if hasattr(response.usage, "prompt_tokens"):
                    increment_groq_tokens("input", response.usage.prompt_tokens)
                if hasattr(response.usage, "completion_tokens"):
                    increment_groq_tokens("output", response.usage.completion_tokens)
                if hasattr(response.usage, "total_tokens"):
                    increment_groq_tokens("total", response.usage.total_tokens)

            return GenerateOutput(answer=response.choices[0].message.content)
        except asyncio.TimeoutError:
            return GenerateOutput(answer="Hệ thống đang bận vui lòng thử lại sau.")
        except ConnectionError:
            logger.info("Retry failed: %s", e)
            return GenerateOutput(answer="Lỗi mạng")


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
