#!/usr/bin/env python3
"""
Script để test exception handler của FastAPI app
"""

import sys

import requests


def test_validation_error():
    """Test validation error bằng cách gửi request không hợp lệ"""
    url = "http://localhost:8000/retrieve"

    # Test case 1: Thiếu trường question
    print("=== Test 1: Thiếu trường 'question' ===")
    invalid_data_1 = {"top_k": 5}

    try:
        response = requests.post(url, json=invalid_data_1, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("Không thể kết nối tới server. Hãy chắc chắn server đang chạy.")
        return
    except (requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
        print(f"Lỗi khi gửi request: {e}")

    print("\n" + "=" * 50 + "\n")

    # Test case 2: Kiểu dữ liệu sai cho top_k
    print("=== Test 2: Kiểu dữ liệu sai cho 'top_k' ===")
    invalid_data_2 = {"question": "test question", "top_k": "không phải số"}

    try:
        response = requests.post(url, json=invalid_data_2, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
    ) as e:
        print(f"Lỗi khi gửi request: {e}")

    print("\n" + "=" * 50 + "\n")

    # Test case 3: Dữ liệu hoàn toàn không hợp lệ
    print("=== Test 3: Dữ liệu hoàn toàn không hợp lệ ===")
    invalid_data_3 = {"invalid_field": "value"}

    try:
        response = requests.post(url, json=invalid_data_3, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
    ) as e:
        print(f"Lỗi khi gửi request: {e}")


def test_valid_request():
    """Test request hợp lệ để đảm bảo server hoạt động bình thường"""
    url = "http://localhost:8000/retrieve"

    print("=== Test: Request hợp lệ ===")
    valid_data = {"question": "test question", "top_k": 3}

    try:
        response = requests.post(url, json=valid_data, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response type: {type(response.json())}")
        print(
            f"Response length: {len(response.json()) if isinstance(response.json(), list) else 'Not a list'}"
        )
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
    ) as e:
        print(f"Lỗi khi gửi request: {e}")


def check_server_status():
    """Kiểm tra xem server có đang chạy không"""
    try:
        response = requests.get("http://localhost:8000/", timeout=10)
        print(f"Server đang chạy. Response: {response.json()}")
        return True
    except requests.exceptions.ConnectionError:
        print("Server không chạy. Vui lòng khởi động server trước.")
        return False
    except (requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
        print(f"Lỗi khi kiểm tra server: {e}")
        return False


if __name__ == "__main__":
    print("Bắt đầu test Exception Handler...")
    print("=" * 60)

    # Kiểm tra server
    if not check_server_status():
        print("\nHướng dẫn khởi động server:")
        print("1. Mở terminal mới")
        print("2. cd c:\\Users\\HP\\Desktop\\AI_legal_assistant")
        print("3. python -m uvicorn app.retrieve:app --reload")
        sys.exit(1)

    print("\n")

    # Test các trường hợp validation error
    test_validation_error()

    print("\n")

    # Test request hợp lệ
    test_valid_request()

    print("\n=== Kết thúc test ===")
    print(
        "Kiểm tra file logs/errors.log và logs/info.log để xem exception handler có được gọi không."
    )
