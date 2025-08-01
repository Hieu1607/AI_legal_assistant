"""
Module để test FastAPI app với router từ retrieve.py và cấu hình từ main.py
"""

import os
import sys
from unittest.mock import patch

import pytest
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

# Thêm thư mục gốc của dự án vào sys.path để import các module từ app và src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import router từ module app.retrieve và functions cần thiết
from app.retrieve import router


# Fixture để tạo TestClient cho FastAPI app
@pytest.fixture
def client():
    # Tạo app tương tự như trong main.py
    app = FastAPI()
    app.include_router(router)

    # Thêm exception handler như trong main.py
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError):
        errors = [
            {
                "field": ".".join(str(loc) for loc in err["loc"][1:]),  # loại bỏ 'body'
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


# Fixture để mock search_relevant_embeddings để không cần dữ liệu thực
@pytest.fixture
def mock_search():
    with patch("src.store_vector.search_embeddings.search_relevant_embeddings") as mock:
        # Mock dữ liệu trả về từ hàm search_relevant_embeddings
        mock.return_value = {
            "ids": [["id1", "id2", "id3"]],
            "distances": [[0.1, 0.2, 0.3]],
            "metadatas": [[{"source": "doc1"}, {"source": "doc2"}, {"source": "doc3"}]],
            "cosine_similarities": [[0.9, 0.8, 0.7]],
            "documents": [["content1", "content2", "content3"]],
        }
        yield mock


def test_index_endpoint(client):
    """Test endpoint / trả về greeting message"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Hello muhehehehe" in response.json()


def test_validation_error_missing_question(client):
    """Test lỗi thiếu trường bắt buộc 'question'"""
    response = client.post("/retrieve", json={"top_k": 5})
    assert response.status_code == 422
    error_response = response.json()
    assert error_response["error"]["type"] == "validation_error"

    # Kiểm tra xem lỗi có đề cập đến trường 'question' không
    field_errors = [err["field"] for err in error_response["error"]["fields"]]
    assert any("question" in field for field in field_errors)


def test_validation_error_invalid_top_k(client):
    """Test lỗi kiểu dữ liệu không hợp lệ cho 'top_k'"""
    response = client.post(
        "/retrieve", json={"question": "test question", "top_k": "không phải số"}
    )
    assert response.status_code == 422
    error_response = response.json()
    assert error_response["error"]["type"] == "validation_error"

    # Kiểm tra xem lỗi có đề cập đến trường 'top_k' không
    field_errors = [err["field"] for err in error_response["error"]["fields"]]
    assert any("top_k" in field for field in field_errors)


def test_validation_error_invalid_data(client):
    """Test lỗi dữ liệu hoàn toàn không hợp lệ"""
    response = client.post("/retrieve", json={"invalid_field": "value"})
    assert response.status_code == 422
    error_response = response.json()
    assert error_response["error"]["type"] == "validation_error"


def test_valid_request(client, mock_search):
    """Test request hợp lệ với mock data"""
    # Patch the search_relevant_embeddings function in the specific module where it's imported
    with patch("app.retrieve.search_relevant_embeddings", mock_search):
        # Kiểm tra kết quả khi gọi API
        response = client.post(
            "/retrieve", json={"question": "test question", "top_k": 3}
        )

    assert response.status_code == 200
    result = response.json()

    # Kiểm tra kết quả
    assert isinstance(result, list)
    assert len(result) == 3
    assert result[0]["chunk_id"] == "id1"
    assert result[1]["chunk_id"] == "id2"
    assert result[2]["chunk_id"] == "id3"

    # Kiểm tra xem mock_search đã được gọi với đúng tham số chưa
    mock_search.assert_called_once_with("test question", 3)


def test_error_handling(client, mock_search):
    """Test xử lý lỗi khi có exception trong quá trình tìm kiếm"""
    mock_search.side_effect = ValueError("Test error")

    with patch("app.retrieve.search_relevant_embeddings", mock_search):
        response = client.post(
            "/retrieve", json={"question": "test question", "top_k": 3}
        )

    assert response.status_code == 500
    error_response = response.json()
    assert error_response["error"]["type"] == "internal_error"


def test_empty_result(client, mock_search):
    """Test kết quả rỗng từ search_relevant_embeddings"""
    mock_search.return_value = {
        "ids": [[]],
        "distances": [[]],
        "metadatas": [[]],
        "cosine_similarities": [[]],
        "documents": [[]],
    }

    with patch("app.retrieve.search_relevant_embeddings", mock_search):
        response = client.post(
            "/retrieve", json={"question": "test question", "top_k": 3}
        )

    assert response.status_code == 200
    result = response.json()
    assert result == []


def test_shutdown_endpoint(client):
    """Test endpoint /shutdown trả về thông báo shutdown"""
    with patch("os.kill") as mock_kill:
        response = client.get("/shutdown")
        assert response.status_code == 200
        assert mock_kill.called
