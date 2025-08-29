"""
Module test rag.py from configs of main.py
"""

import asyncio
import os
import re
import sys
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

from app.logic.rag_logic import ask_LLM, get_relevant_sentences
from app.routers.rag import router

test_question = "Chương II điều 29 bộ luật hàng hải là gì?"


# Fixture to create TestClient for FastAPI app
@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        errors = [
            {
                "field": ".".join(str(loc) for loc in err["loc"][1:]),
                "error": err["msg"],
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "validation_error",
                    "message": "Input data is not valid",
                    "fields": errors,
                }
            },
        )

    return TestClient(app)


@pytest.fixture
def mock_search():
    with patch("src.store_vector.search_embeddings.search_relevant_embeddings") as mock:
        mock.return_value = {
            "ids": [["id1", "id2", "id3", "id4", "id5"]],
            "distances": [[0.1, 0.2, 0.3, 0.4, 0.5]],
            "metadatas": [
                [
                    {"source": "doc1"},
                    {"source": "doc2"},
                    {"source": "doc3"},
                    {"source": "doc4"},
                    {"source": "doc5"},
                ]
            ],
            "cosine_similarities": [[0.9, 0.8, 0.7, 0.6, 0.5]],
            "documents": [
                [
                    "CHƯƠNG II TÀU BIỂN; Điều 29. Thanh tra, kiểm tra về an toàn hàng hải, an ninh hàng hải và phòng ngừa ô nhiễm môi trường",
                    "CHƯƠNG II TÀU BIỂN; Mục 3. ĐĂNG KIỂM TÀU BIỂN VIỆT NAM; Điều 29. Nguyên tắc đăng kiểm tàu biển Việt Nam; 4. Tàu biển Việt Nam hoạt động tuyến quốc tế được kiểm định, phân cấp, đánh giá và cấp giấy chứng nhận theo quy định của pháp luật và điều ước quốc tế mà Cộng hòa xã hội chủ nghĩa Việt Nam là thành viên.",
                    "CHƯƠNG II TÀU BIỂN; Mục 5. CHUYỂN QUYỀN SỞ HỮU VÀ THẾ CHẤP TÀU BIỂN; Điều 37. Thế chấp tàu biển Việt Nam; 3. Hợp đồng thế chấp tàu biển Việt Nam phải được giao kết bằng văn bản. Việc thế chấp tàu biển Việt Nam được thực hiện theo pháp luật Việt Nam.",
                    "CHƯƠNG II NHỮNG NGUYÊN TẮC CƠ BẢN; Điều 9. Bảo đảm quyền bảo vệ của đương sự Đương sự có quyền tự bảo vệ hoặc nhờ luật sư hay người khác có đủ điều kiện theo quy định của Bộ luật này bảo vệ quyền và lợi ích hợp pháp của mình. Toà án có trách nhiệm bảo đảm cho đương sự thực hiện quyền bảo vệ của họ.",
                    "CHƯƠNG IV CẢNG BIỂN; Mục 2. QUẢN LÝ CẢNG BIỂN; Điều 90. Phí, lệ phí hàng hải và giá dịch vụ tại cảng biển; 5. Doanh nghiệp thực hiện việc kê khai giá dịch vụ tại cảng biển với cơ quan có thẩm quyền và niêm yết theo quy định của pháp luật về giá.",
                ]
            ],
        }
        yield mock


def test_get_relevant_sentences(mock_search):  # pylint: disable=redefined-outer-name
    with patch(
        "src.store_vector.search_embeddings.search_relevant_embeddings", mock_search
    ):
        response = get_relevant_sentences(test_question)
        assert "chương ii" in response[0].lower()
        assert len(response) == 5
        assert (
            response[0]
            == "CHƯƠNG II TÀU BIỂN; Điều 29. Thanh tra, kiểm tra về an toàn hàng hải, an ninh hàng hải và phòng ngừa ô nhiễm môi trường"
        )


def test_ask_LLM_good_case(mock_search):  # pylint: disable=redefined-outer-name
    with patch(
        "src.store_vector.search_embeddings.search_relevant_embeddings", mock_search
    ):
        relevant_sentences = get_relevant_sentences(test_question)
    answer = asyncio.run(ask_LLM(relevant_sentences, test_question))
    logger.info(answer)
    match = re.search(r".*chương (.+).*điều (.+)", answer.lower())
    assert match is not None


def test_ask_LLM_no_relevant_sentences():
    relevant_sentences = []
    answer = asyncio.run(ask_LLM(relevant_sentences, test_question))
    assert "không" in answer.lower() and "thông tin" in answer.lower()


@pytest.mark.asyncio
async def test_ask_LLM_timeout_error(
    mock_search,
):  # pylint: disable=redefined-outer-name
    with patch(
        "src.store_vector.search_embeddings.search_relevant_embeddings", mock_search
    ):
        relevant_sentences = get_relevant_sentences(test_question)
    with patch("google.generativeai.GenerativeModel") as mock_model_cls:
        # Create mock for GenerativeModel
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = asyncio.TimeoutError
        # When GenerativeModel mock was created, it return mock_model
        mock_model_cls.return_value = mock_model

        answer = await ask_LLM(relevant_sentences, test_question)
        assert answer == "The system is busy now. Please try again."


@pytest.mark.asyncio
async def test_ask_LLM_connection_error_2_times(
    mock_search,
):  # pylint: disable=redefined-outer-name
    with patch(
        "src.store_vector.search_embeddings.search_relevant_embeddings", mock_search
    ):
        relevant_sentences = get_relevant_sentences(test_question)
    with patch("google.generativeai.GenerativeModel") as mock_model_cls:
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = ConnectionError
        mock_model_cls.return_value = mock_model

        result = await ask_LLM(relevant_sentences, test_question)
        assert result == "Network errored"


@pytest.mark.asyncio
async def test_ask_LLM_connection_error_1_time(
    mock_search,
):  # pylint: disable=redefined-outer-name
    with patch(
        "src.store_vector.search_embeddings.search_relevant_embeddings", mock_search
    ):
        relevant_sentences = get_relevant_sentences(test_question)
    with patch("google.generativeai.GenerativeModel") as mock_model_cls:
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = [
            ConnectionError("Network errored"),
            MagicMock(text="This is the answer"),
        ]
        mock_model_cls.return_value = mock_model

        result = await ask_LLM(relevant_sentences, test_question)
        assert result == "This is the answer"


@pytest.mark.asyncio
async def test_ask_model_good_case(
    client, mock_search
):  # pylint: disable=redefined-outer-name
    with (
        patch(
            "src.store_vector.search_embeddings.search_relevant_embeddings", mock_search
        ),
        patch("google.generativeai.GenerativeModel") as mock_model_cls,
    ):
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = (
            "Theo Chương II Điều 29 Bộ luật Hàng hải, tàu biển Việt Nam..."
        )
        mock_model.generate_content.return_value = mock_response
        mock_model_cls.return_value = mock_model

        res = client.post("/rag", json={"question": test_question})

        assert res.status_code == 200
        response = res.json()
        assert response["status"] == "success"
        assert response["data"]["question"] == test_question
        assert "Theo" in response["data"]["answer"]
        assert response["data"]["context_count"] == 5


@pytest.mark.asyncio
async def test_ask_model_bad_case(client):  # pylint: disable=redefined-outer-name
    with patch(
        "app.rag.get_relevant_sentences"
    ) as mock_search:  # pylint: disable=redefined-outer-name
        mock_search.side_effect = ValueError("Simulated error")

        response = client.post("/rag/", json={"question": test_question})

        assert response.status_code == 500
        error_message = response.json()
        assert error_message["status"] == "error"
        assert error_message["error"]["type"] == "internal_error"
        assert (
            error_message["error"]["message"]
            == "An error occurred while processing your request"
        )


# pytest --cov=app.rag --cov-report=term tests/test_rag.py
