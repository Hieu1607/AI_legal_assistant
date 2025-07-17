"""
Module test services/tools.py
"""

import asyncio
import os
import re
import sys
from unittest.mock import MagicMock, patch

# Add the project root to the Python path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)

import pytest

from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

from services.tools import (
    FormatInput,
    GenerateInput,
    RetrieveInput,
    format_citation,
    generate_answer,
    retrieve_laws,
)

test_question = "Chương II điều 29 bộ luật hàng hải là gì?"


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


def test_retrieve_laws_good_case(mock_search):
    with patch(
        "src.store_vector.search_embeddings.search_relevant_embeddings", mock_search
    ):
        response = retrieve_laws(RetrieveInput(question=test_question, top_k=5))
        assert "CHƯƠNG II" in response.chunks[0]
        assert len(response.chunks) == 5
        assert (
            response.chunks[0]
            == "CHƯƠNG II TÀU BIỂN; Điều 29. Thanh tra, kiểm tra về an toàn hàng hải, an ninh hàng hải và phòng ngừa ô nhiễm môi trường"
        )


def test_retrieve_laws_bad_case():
    # Tạo mock riêng cho test case này
    with patch("services.tools.search_relevant_embeddings") as mock:
        mock.side_effect = ImportError("Example error")
        response = retrieve_laws(RetrieveInput(question=test_question, top_k=5))
        assert response.chunks == []


def test_generate_answer_good_case(mock_search):
    with patch("services.tools.search_relevant_embeddings", mock_search):
        relevant_sentences = retrieve_laws(
            RetrieveInput(question=test_question, top_k=5)
        )
    answer = asyncio.run(
        generate_answer(
            GenerateInput(chunks=relevant_sentences.chunks, question=test_question)
        )
    )
    logger.info(answer)
    match = re.search(r".*chương (.+).*điều (.+)", answer.answer.lower())
    assert match is not None


def test_generate_answer_no_relevant_sentences():
    relevant_sentences = []
    answer = asyncio.run(
        generate_answer(
            GenerateInput(chunks=relevant_sentences, question=test_question)
        )
    )
    assert "không" in answer.answer.lower() and "thông tin" in answer.answer.lower()


@pytest.mark.asyncio
async def test_generate_answer_timeout_error(mock_search):
    with patch("services.tools.search_relevant_embeddings", mock_search):
        relevant_sentences = retrieve_laws(
            RetrieveInput(question=test_question, top_k=5)
        )
    with patch("google.generativeai.GenerativeModel") as mock_model_cls:
        # Tạo mock cho class GenerativeModel
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = asyncio.TimeoutError
        # Khi GenerativeModel được khởi tạo, nó sẽ trả về mock_model
        mock_model_cls.return_value = mock_model

        answer = await generate_answer(
            GenerateInput(chunks=relevant_sentences.chunks, question=test_question)
        )
        assert answer.answer == "Hệ thống đang bận vui lòng thử lại sau."


@pytest.mark.asyncio
async def test_generate_answer_connection_error_2_times(mock_search):
    with patch("services.tools.search_relevant_embeddings", mock_search):
        relevant_sentences = retrieve_laws(
            RetrieveInput(question=test_question, top_k=5)
        )
    with patch("google.generativeai.GenerativeModel") as mock_model_cls:
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = ConnectionError
        mock_model_cls.return_value = mock_model

        result = await generate_answer(
            GenerateInput(chunks=relevant_sentences.chunks, question=test_question)
        )
        assert result.answer == "Lỗi mạng"


@pytest.mark.asyncio
async def test_generate_answer_connection_error_1_time(mock_search):
    with patch("services.tools.search_relevant_embeddings", mock_search):
        relevant_sentences = retrieve_laws(
            RetrieveInput(question=test_question, top_k=5)
        )
    with patch("google.generativeai.GenerativeModel") as mock_model_cls:
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = [
            ConnectionError("Lỗi mạng"),
            MagicMock(text="Đây là câu trả lời"),
        ]
        mock_model_cls.return_value = mock_model

        result = await generate_answer(
            GenerateInput(chunks=relevant_sentences.chunks, question=test_question)
        )
        assert result.answer == "Đây là câu trả lời"


def test_format_citation_good_case(mock_search):
    with patch("services.tools.search_relevant_embeddings", mock_search):
        relevant_sentences = retrieve_laws(
            RetrieveInput(question=test_question, top_k=5)
        )
    result = format_citation(
        FormatInput(answer="Some answer", chunks=relevant_sentences.chunks)
    )
    match = re.search(r"Some answer\nNguồn:\n.*", result.formatted_answer)
    assert match is not None


def test_format_citation_bad_cases():
    result = format_citation(FormatInput(answer="", chunks=["chunk1", "chunk2"]))
    assert "Nguồn:" in result.formatted_answer

    result = format_citation(FormatInput(answer="Some answer", chunks=[]))
    assert result.formatted_answer == "Some answer\nNguồn:\n"

    result = format_citation(FormatInput(answer="", chunks=[]))
    assert result.formatted_answer == "\nNguồn:\n"

    # Test error case by mocking the enumerate function to raise an exception
    with patch("builtins.enumerate") as mock_enumerate:
        mock_enumerate.side_effect = ValueError("Example error")
        result = format_citation(FormatInput(answer="", chunks=[]))
        assert result.formatted_answer == "Cannot format the answer"


# pytest --cov=services.tools --cov-report=term tests/test_tools.py
