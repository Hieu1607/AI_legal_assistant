import asyncio
import os
import sys

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("Gemini_API_KEY"))  # type: ignore
from pydantic import BaseModel

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(root))
from configs.logger import get_logger_app, setup_logging

setup_logging()
logger = get_logger_app(__name__)
from src.store_vector.weaviate_search import search_relevant_embeddings


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
        # relevant_embeddings["documents"] return nested list, so we need to flat it
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
    context = ""
    for i, sentence in enumerate(relevant_sentences, 1):
        context += f"Đoạn {i}: {sentence}\n"

    prompt = f"""Với vai trò là 1 trợ lý ảo pháp luật, dựa trên các nội dung sau:
        {context}
        Câu hỏi: {data.question}
        Vui lòng trả lời câu hỏi dựa trên thông tin được cung cấp ở trên.

        Trả lời câu hỏi theo 3 trường hợp
        Trường hợp 1: Nếu tìm thấy nội dung thích hợp trong tài liệu, trả lời 'Theo chương ... điều ... bộ luật abc ..., nội dung'
        Trường hợp 2: Nếu không tìm thấy nội dung thích hợp trong tài liệu, trả lời: 'Không tìm thấy thông tin liên quan đến câu hỏi.'
        Trường hợp 3: Nếu câu hỏi linh tinh hoặc không liên quan đến pháp luật, trả lời: "Chào bạn, tôi đã sẵn sàng trả lời với vai trò là một trợ lý ảo pháp luật.Tuy nhiên, có vẻ như bạn chưa cung cấp câu hỏi cụ thể hoặc câu hỏi của bạn không liên quan đến pháp luật. Vui lòng đặt câu hỏi lại để tôi có thể trả lời."
        Trả lời ngắn gọn.
    """
    try:
        model = genai.GenerativeModel(model_name="gemini-2.5-pro")  # type: ignore

        # Use loop.run_in_executor to run a synchronous function in a seperate thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: model.generate_content(prompt)),
            timeout=60,
        )
        logger.info("The answer from LLM is %s", response.text)
        return GenerateOutput(answer=response.text)
    except asyncio.TimeoutError:
        return GenerateOutput(answer="Hệ thống đang bận vui lòng thử lại sau.")
    except ConnectionError as e:
        logger.info("Network error: %s, retrying...", e)
        try:
            model = genai.GenerativeModel(model_name="gemini-2.5-pro")  # type: ignore
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: model.generate_content(prompt)),
                timeout=15,
            )
            return GenerateOutput(answer=response.text)
        except asyncio.TimeoutError:
            return GenerateOutput(answer="Hệ thống đang bận vui lòng thử lại sau.")
        except ConnectionError:
            logger.info("Retry failed: %s", e)
            return GenerateOutput(answer="Lỗi mạng")
    except Exception as e:  # pylint: disable=broad-exception-caught
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
    current_chunks = retrieve_laws(
        RetrieveInput(question="Chương II điều 29 luật hàng hải nói gì?", top_k=5)
    )

    async def main():
        res = await generate_answer(
            GenerateInput(
                question="Chương II điều 29 luật hàng hải nói gì?",
                chunks=current_chunks.chunks,
            )
        )
        answer = format_citation(
            FormatInput(answer=res.answer, chunks=current_chunks.chunks)
        )
        print(answer.formatted_answer)

    asyncio.run(main())
