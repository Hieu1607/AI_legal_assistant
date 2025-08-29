"""
Module test agent.py from configs of main.py
"""

import asyncio
import os
import re
import sys
from unittest.mock import patch

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

from app.routers.agent import router
from services.tools import GenerateOutput, RetrieveOutput

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
    with patch("app.logic.agent_logic.retrieve_laws") as mock:
        mock.return_value = RetrieveOutput(
            chunks=[
                "CHƯƠNG II TÀU BIỂN; Điều 29. Thanh tra, kiểm tra về an toàn hàng hải, an ninh hàng hải và phòng ngừa ô nhiễm môi trường",
                "CHƯƠNG II TÀU BIỂN; Mục 3. ĐĂNG KIỂM TÀU BIỂN VIỆT NAM; Điều 29. Nguyên tắc đăng kiểm tàu biển Việt Nam; 4. Tàu biển Việt Nam hoạt động tuyến quốc tế được kiểm định, phân cấp, đánh giá và cấp giấy chứng nhận theo quy định của pháp luật và điều ước quốc tế mà Cộng hòa xã hội chủ nghĩa Việt Nam là thành viên.",
                "CHƯƠNG II TÀU BIỂN; Mục 5. CHUYỂN QUYỀN SỞ HỮU VÀ THẾ CHẤP TÀU BIỂN; Điều 37. Thế chấp tàu biển Việt Nam; 3. Hợp đồng thế chấp tàu biển Việt Nam phải được giao kết bằng văn bản. Việc thế chấp tàu biển Việt Nam được thực hiện theo pháp luật Việt Nam.",
                "CHƯƠNG II NHỮNG NGUYÊN TẮC CƠ BẢN; Điều 9. Bảo đảm quyền bảo vệ của đương sự Đương sự có quyền tự bảo vệ hoặc nhờ luật sư hay người khác có đủ điều kiện theo quy định của Bộ luật này bảo vệ quyền và lợi ích hợp pháp của mình. Toà án có trách nhiệm bảo đảm cho đương sự thực hiện quyền bảo vệ của họ.",
                "CHƯƠNG IV CẢNG BIỂN; Mục 2. QUẢN LÝ CẢNG BIỂN; Điều 90. Phí, lệ phí hàng hải và giá dịch vụ tại cảng biển; 5. Doanh nghiệp thực hiện việc kê khai giá dịch vụ tại cảng biển với cơ quan có thẩm quyền và niêm yết theo quy định của pháp luật về giá.",
            ]
        )
        yield mock


@pytest.fixture
def mock_ask():
    with patch("app.logic.agent_logic.generate_answer") as mock:
        mock.return_value = GenerateOutput(
            answer="Theo chương II điều 29 bộ luật hàng hải thì nội dung là blabla"
        )
        yield mock


def test_happy_case_1_step(client, mock_search):  # pylint: disable=redefined-outer-name
    with mock_search:
        response = client.post(
            "/agent",
            json={
                "question": test_question,
                "top_k": 5,
                "total_steps": 1,
                "timeout_sec": 20,
            },
        )

        data = response.json()
        assert response.status_code == 200
        assert data["success"] is True
        assert data["status_code"] == 200
        assert data["step_completed"] == 1
        assert len(data["data"]) == 5
        assert data["message"] == "Successfully retrieved law chunks"
        assert data["execution_time"] >= 0


def test_happy_case_2_steps(
    client, mock_search, mock_ask
):  # pylint: disable=redefined-outer-name
    with mock_search:
        with mock_ask:
            response = client.post(
                "/agent",
                json={
                    "question": test_question,
                    "top_k": 5,
                    "total_steps": 2,
                    "timeout_sec": 20,
                },
            )

            data = response.json()
            print(data)
            assert response.status_code == 200
            assert data["success"] is True
            assert data["status_code"] == 200
            assert data["step_completed"] == 2
            # Check if answer contains chapter and article information
            match = re.search(r".*chương (.+).*điều (.+)", data["data"].lower())
            assert match is not None
            assert data["message"] == "Successfully generated answer"
            assert data["execution_time"] >= 0


def test_happy_case_3_steps(
    client, mock_search, mock_ask
):  # pylint: disable=redefined-outer-name
    with mock_search & mock_ask:
        response = client.post(
            "/agent",
            json={
                "question": test_question,
                "top_k": 5,
                "total_steps": 3,
                "timeout_sec": 20,
            },
        )

        data = response.json()
        assert response.status_code == 200
        assert data["success"] is True
        assert data["status_code"] == 200
        assert data["step_completed"] == 3
        # Check if formatted answer contains chapter and article information
        match_1 = re.search(r".*chương (.+).*điều (.+)", data["data"].lower())
        assert match_1 is not None
        # Check if citation is included
        match_2 = re.search(r".*nguồn.*", data["data"].lower())
        assert match_2 is not None
        assert data["message"] == "Successfully formatted answer with citations"
        assert data["execution_time"] >= 0


def test_timeout_in_step_1(client, mock_ask):  # pylint: disable=redefined-outer-name
    with patch("services.tools.retrieve_laws") as mock:
        with mock_ask:
            mock.side_effect = asyncio.TimeoutError("Simulated timeout")
            response = client.post(
                "/agent",
                json={
                    "question": test_question,
                    "top_k": 5,
                    "total_steps": 3,
                    "timeout_sec": 5,
                },
            )
            data = response.json()
            assert response.status_code == 200
            assert data["success"] is False
            assert data["status_code"] == 408
            assert data["step_completed"] == 0
            assert "Step 1 (retrieve chunks) timed out after 5s" in data["message"]
            assert (
                data["execution_time"] >= 0
            )  # Should be small since mock fails immediately


def test_timeout_in_step_2(client, mock_search):  # pylint: disable=redefined-outer-name
    with mock_search:
        with patch("services.tools.generate_answer") as mock:
            mock.side_effect = asyncio.TimeoutError("Example error")
            response = client.post(
                "/agent",
                json={
                    "question": test_question,
                    "top_k": 5,
                    "total_steps": 3,
                    "timeout_sec": 5,
                },
            )
            data = response.json()
            assert response.status_code == 200
            assert data["success"] is False
            assert data["status_code"] == 408
            assert data["step_completed"] == 1
            assert "Step 2 (generate answer) timed out after 5s" in data["message"]
            assert data["execution_time"] >= 0


def test_timeout_in_step_3(
    client, mock_search, mock_ask
):  # pylint: disable=redefined-outer-name
    with mock_search & mock_ask:
        with patch("app.logic.agent_logic.format_citation") as mock:
            mock.side_effect = asyncio.TimeoutError("Example error")
            response = client.post(
                "/agent",
                json={
                    "question": test_question,
                    "top_k": 5,
                    "total_steps": 3,
                    "timeout_sec": 5,
                },
            )
            data = response.json()
            print(data)
            assert response.status_code == 200
            assert data["success"] is False
            assert data["status_code"] == 408
            assert data["step_completed"] == 2
            assert "Step 3 (format citation) timed out after 5s" in data["message"]
            assert data["execution_time"] >= 0


def test_empty_chunks_in_step_2(
    client, mock_search, mock_ask
):  # pylint: disable=redefined-outer-name
    with mock_search & mock_ask:
        mock_search.return_value = RetrieveOutput(chunks=[])

        response = client.post(
            "/agent",
            json={
                "question": test_question,
                "top_k": 5,
                "total_steps": 2,
                "timeout_sec": 20,
            },
        )

        data = response.json()
        print(data)
        assert response.status_code == 200
        assert data["success"] is False
        assert data["status_code"] == 400
        assert data["step_completed"] == 1
        assert (
            "Cannot generate answer: no chunks retrieved from step 1" in data["message"]
        )


def test_not_answer_in_step_3(
    client, mock_search, mock_ask
):  # pylint: disable=redefined-outer-name
    with mock_search, mock_ask:
        mock_ask.return_value = GenerateOutput(answer="")
        response = client.post(
            "/agent",
            json={
                "question": test_question,
                "top_k": 5,
                "total_steps": 3,
                "timeout_sec": 20,
            },
        )

        data = response.json()
        assert response.status_code == 200
        assert data["success"] is False
        assert data["status_code"] == 400
        assert data["step_completed"] == 2
        assert (
            "Cannot format citation: missing data from previous steps"
            in data["message"]
        )


def test_other_errors(client, mock_search):  # pylint: disable=redefined-outer-name
    with mock_search:
        mock_search.side_effect = OSError("Example error")
        response = client.post(
            "/agent",
            json={
                "question": test_question,
                "top_k": 5,
                "total_steps": 3,
                "timeout_sec": 20,
            },
        )

        data = response.json()
        assert response.status_code == 200
        assert data["success"] is False
        assert data["status_code"] == 500
        assert data["step_completed"] == 0
        assert "Error occurred" in data["message"]
        assert data["data"] is None


# pytest --cov=app.agent --cov-report=term tests/test_agent.py
