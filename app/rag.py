import asyncio
import os
import sys
import time

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("Gemini_API_KEY"))  # type: ignore

# from google.generativeai import generative_models
# import fastapi
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

retrieving_time = 0
prompting_time = 0
llm_time = 0

# Set up logging
root = os.path.dirname(os.getcwd())
sys.path.insert(0, str(root))

from configs.logger import get_logger_app, setup_logging
from src.store_vector.search_embeddings import search_relevant_embeddings

setup_logging()
# Sử dụng get_logger_app để ghi log vào app.log
logger = get_logger_app(__name__)

router = APIRouter()


class QueryQuestion(BaseModel):
    question: str


def get_relevant_sentences(question):
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


async def ask_LLM(relevant_sentences, question):
    start_prompting_time = time.perf_counter()
    if not relevant_sentences:
        return "Không tìm thấy thông tin liên quan để trả lời câu hỏi của bạn."
    # Tạo một chuỗi chứa tất cả các câu từ relevant_sentences
    context = ""
    for i, sentence in enumerate(relevant_sentences, 1):
        context += f"Đoạn {i}: {sentence}\n\n"

    prompt = f"""Với vai trò là 1 trợ lý ảo pháp luật chuyên nghiệp, dựa trên các nội dung sau:
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
    prompting_time = end_propting_time - start_prompting_time
    try:
        # Sử dụng hàm riêng để chạy generate_content trong một executor
        model = genai.GenerativeModel(model_name="gemini-2.5-pro")  # type: ignore

        # Sử dụng loop.run_in_executor để chạy hàm đồng bộ trong một thread riêng
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: model.generate_content(prompt)),
            timeout=60,
        )
        return response.text
    except asyncio.TimeoutError:
        return "Hệ thống đang bận vui lòng thử lại sau."
    except ConnectionError as e:
        logger.info("Network error: %s, retrying...", e)
        try:
            model = genai.GenerativeModel(model_name="gemini-2.5-pro")  # type: ignore
            loop = asyncio.get_event_loop()
            response = await asyncio.wait_for(
                loop.run_in_executor(None, lambda: model.generate_content(prompt)),
                timeout=15,
            )
            return response.text
        except asyncio.TimeoutError:
            return "Hệ thống đang bận vui lòng thử lại sau."
        except ConnectionError:
            logger.info("Retry failed: %s", e)
            return "Lỗi mạng"


@router.post("/rag")
async def ask_model(request: QueryQuestion):
    try:
        start_retrieve_time = time.perf_counter()
        relevant_sentences = get_relevant_sentences(request.question)
        end_retrieve_time = time.perf_counter()
        retrieving_time = end_retrieve_time - start_retrieve_time

        start_ask_LLM_time = time.perf_counter()
        answer = await ask_LLM(relevant_sentences, request.question)
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

        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "data": {
                    "answer": answer.strip(),
                    "question": request.question,
                    "context_count": len(relevant_sentences),
                },
            },
        )
    except (IndexError, KeyError, FileNotFoundError, ImportError, ValueError) as e:
        logger.info("An error occurred during asking model: %s", e)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": {
                    "type": "internal_error",
                    "message": "An error occurred while processing your request",
                },
            },
        )
