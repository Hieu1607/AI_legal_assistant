"""
Script to test exception handler of FastAPI app
"""

import sys

import requests


def test_validation_error():
    """Test validation error by sending invalid request"""
    url = "http://localhost:8000/retrieve"

    # Test case 1: Missing question field
    print("=== Test 1: Missing 'question' field ===")
    invalid_data_1 = {"top_k": 5}

    try:
        response = requests.post(url, json=invalid_data_1, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("Cannot connect to server. Make sure the server is running.")
        return
    except (requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
        print(f"Error sending request: {e}")

    print("\n" + "=" * 50 + "\n")

    # Test case 2: Wrong data type for top_k
    print("=== Test 2: Wrong data type for 'top_k' ===")
    invalid_data_2 = {"question": "test question", "top_k": "not a number"}

    try:
        response = requests.post(url, json=invalid_data_2, timeout=10)
        print(f"Status code: {response.status_code}")
        print(f"Response: {response.json()}")
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.HTTPError,
    ) as e:
        print(f"Error sending request: {e}")

    print("\n" + "=" * 50 + "\n")

    # Test case 3: Completely invalid data
    print("=== Test 3: Completely invalid data ===")
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
        print(f"Error sending request: {e}")


def test_valid_request():
    """Test valid request to ensure server operates normally"""
    url = "http://localhost:8000/retrieve"

    print("=== Test: Valid request ===")
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
        print(f"Error sending request: {e}")


def check_server_status():
    """Check if the server is running"""
    try:
        response = requests.get("http://localhost:8000/", timeout=10)
        print(f"Server is running. Response: {response.json()}")
        return True
    except requests.exceptions.ConnectionError:
        print("Server is not running. Please start the server first.")
        return False
    except (requests.exceptions.Timeout, requests.exceptions.HTTPError) as e:
        print(f"Error checking server: {e}")
        return False


if __name__ == "__main__":
    print("Starting Exception Handler test...")
    print("=" * 60)

    # Check server
    if not check_server_status():
        print("\nServer startup instructions:")
        print("1. Open new terminal")
        print("2. cd c:\\Users\\HP\\Desktop\\AI_legal_assistant")
        print("3. python -m uvicorn app.retrieve:app --reload")
        sys.exit(1)

    print("\n")

    # Test various validation error cases
    test_validation_error()

    print("\n")

    # Test valid request
    test_valid_request()

    print("\n=== Test completed ===")
    print(
        "Check files logs/errors.log and logs/info.log to see if exception handler was called."
    )
