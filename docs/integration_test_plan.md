# Integration Test Plan

## Mô tả
Tài liệu này mô tả các test case tích hợp để kiểm thử hệ thống AI Legal Assistant thông qua API endpoint `/agent`. Mỗi test case bao gồm input, expected output và các bước thực hiện chi tiết.

## Test Environment
- **API Endpoint**: `POST /agent`
- **Timeout**: 5-300 giây (có thể cấu hình)
- **Steps**: 1-3 bước (Retrieve → Generate → Format)

---

## Test Case 1: Happy Path - Truy vấn thông thường với citations

### Mô tả
Kiểm thử trường hợp lý tưởng khi người dùng hỏi về hợp đồng và hệ thống trả về câu trả lời đầy đủ với citations.

### Input
```json
{
  "question": "Hợp đồng trong luật dân sự là gì?",
  "top_k": 5,
  "total_steps": 3,
  "timeout_sec": 30
}
```

### Expected Output
```json
{
  "success": true,
  "status_code": 200,
  "step_completed": 3,
  "data": "Hợp đồng là thỏa thuận giữa các bên... [Nguồn: Bộ luật Dân sự 2015, Điều 385]",
  "message": "Successfully formatted answer with citations",
  "execution_time": 15.2
}
```

### Bước thực hiện
1. Gửi POST request đến `/agent` với payload trên
2. Kiểm tra response status = 200
3. Kiểm tra `success = true`
4. Kiểm tra `step_completed = 3`
5. Kiểm tra `data` chứa từ khóa "hợp đồng" và citation "Nguồn:"
6. Kiểm tra `execution_time > 0`

---

## Test Case 2: LLM Timeout - Fallback Response

### Mô tả
Kiểm thử khi LLM bị timeout ở step 2 (generate answer), hệ thống trả về chunks từ step 1.

### Input
```json
{
  "question": "Chương II điều 29 bộ luật hàng hải nói gì?",
  "top_k": 5,
  "total_steps": 3,
  "timeout_sec": 5
}
```

### Expected Output
```json
{
  "success": false,
  "status_code": 408,
  "step_completed": 1,
  "data": ["CHƯƠNG II TÀU BIỂN...", "Điều 29..."],
  "message": "Step 2 (generate answer) timed out after 5s. Returning chunks from step 1.",
  "execution_time": 5.1
}
```

### Bước thực hiện
1. Gửi request với timeout ngắn (5s)
2. Kiểm tra response status = 200 (API vẫn trả về thành công)
3. Kiểm tra `success = false`
4. Kiểm tra `status_code = 408` (Request Timeout)
5. Kiểm tra `step_completed = 1`
6. Kiểm tra `data` chứa array của chunks
7. Kiểm tra message chứa "timed out"

---

## Test Case 3: Agent Error - Internal Server Error

### Mô tả
Kiểm thử khi có lỗi hệ thống (OSError, ValueError, RuntimeError), trả về status 500.

### Input
```json
{
  "question": "Luật giao thông đường bộ quy định gì?",
  "top_k": 5,
  "total_steps": 3,
  "timeout_sec": 20
}
```

### Expected Output
```json
{
  "success": false,
  "status_code": 500,
  "step_completed": 0,
  "data": null,
  "message": "Error occurred: Database connection failed. Returning partial results.",
  "execution_time": 2.3
}
```

### Bước thực hiện
1. Simulate lỗi hệ thống (database down, file system error)
2. Gửi request bình thường
3. Kiểm tra response status = 200
4. Kiểm tra `success = false`
5. Kiểm tra `status_code = 500`
6. Kiểm tra `step_completed = 0`
7. Kiểm tra `data = null`
8. Kiểm tra message chứa "Error occurred"

---

## Test Case 4: Empty Chunks - No Relevant Documents

### Mô tả
Kiểm thử khi query không tìm ra chunk nào phù hợp, hệ thống trả về lỗi 400.

### Input
```json
{
  "question": "Luật về du lịch vũ trụ Việt Nam quy định gì?",
  "top_k": 5,
  "total_steps": 2,
  "timeout_sec": 20
}
```

### Expected Output
```json
{
  "success": false,
  "status_code": 400,
  "step_completed": 1,
  "data": null,
  "message": "Cannot generate answer: no chunks retrieved from step 1",
  "execution_time": 3.5
}
```

### Bước thực hiện
1. Gửi query với chủ đề không có trong database
2. Kiểm tra response status = 200
3. Kiểm tra `success = false`
4. Kiểm tra `status_code = 400` (Bad Request)
5. Kiểm tra `step_completed = 1`
6. Kiểm tra `data = null`
7. Kiểm tra message chứa "no chunks retrieved"

---

## Test Case 5: Partial Success - Step 1 Only

### Mô tả
Kiểm thử khi chỉ yêu cầu thực hiện step 1 (retrieve chunks), trả về danh sách chunks.

### Input
```json
{
  "question": "Bộ luật hình sự điều 100 quy định gì?",
  "top_k": 3,
  "total_steps": 1,
  "timeout_sec": 15
}
```

### Expected Output
```json
{
  "success": true,
  "status_code": 200,
  "step_completed": 1,
  "data": ["Điều 100. Tội giết người...", "CHƯƠNG VII TỘI PHẠM..."],
  "message": "Successfully retrieved law chunks",
  "execution_time": 2.1
}
```

### Bước thực hiện
1. Gửi request với `total_steps = 1`
2. Kiểm tra response status = 200
3. Kiểm tra `success = true`
4. Kiểm tra `step_completed = 1`
5. Kiểm tra `data` là array với length = top_k
6. Kiểm tra message = "Successfully retrieved law chunks"

---

## Test Case 6: Validation Error - Invalid Input

### Mô tả
Kiểm thử khi input không hợp lệ (question quá ngắn, top_k ngoài phạm vi), trả về validation error.

### Input
```json
{
  "question": "ABC",
  "top_k": 25,
  "total_steps": 4,
  "timeout_sec": 3
}
```

### Expected Output
```json
{
  "error": {
    "type": "validation_error",
    "message": "Input data is not valid",
    "fields": [
      {"field": "question", "error": "ensure this value has at least 10 characters"},
      {"field": "top_k", "error": "ensure this value is less than or equal to 20"},
      {"field": "total_steps", "error": "ensure this value is less than or equal to 3"},
      {"field": "timeout_sec", "error": "ensure this value is greater than or equal to 5"}
    ]
  }
}
```

### Bước thực hiện
1. Gửi request với các giá trị invalid
2. Kiểm tra response status = 422 (Unprocessable Entity)
3. Kiểm tra response chứa `error.type = "validation_error"`
4. Kiểm tra `error.fields` chứa các field bị lỗi
5. Kiểm tra message chi tiết cho từng field

---

## Test Case 7: Step 3 Timeout - Format Citation Failure

### Mô tả
Kiểm thử khi step 3 (format citation) bị timeout, trả về answer từ step 2.

### Input
```json
{
  "question": "Luật lao động về thời giờ làm việc quy định gì?",
  "top_k": 5,
  "total_steps": 3,
  "timeout_sec": 8
}
```

### Expected Output
```json
{
  "success": false,
  "status_code": 408,
  "step_completed": 2,
  "data": "Theo luật lao động, thời giờ làm việc bình thường không quá 8 giờ/ngày...",
  "message": "Step 3 (format citation) timed out after 8s. Returning answer from step 2.",
  "execution_time": 8.2
}
```

### Bước thực hiện
1. Simulate timeout ở step 3
2. Gửi request với timeout ngắn
3. Kiểm tra response status = 200
4. Kiểm tra `success = false`
5. Kiểm tra `status_code = 408`
6. Kiểm tra `step_completed = 2`
7. Kiểm tra `data` chứa answer (string) chưa format
8. Kiểm tra message chứa "Step 3" và "timed out"

---

## Test Execution Commands

### Chạy toàn bộ test suite
```bash
pytest tests/test_agent.py -v
```

### Chạy test với coverage report
```bash
pytest --cov=app.agent --cov-report=term tests/test_agent.py
```

### Chạy test case cụ thể
```bash
pytest tests/test_agent.py::test_happy_case_3_steps -v
```

## Notes
- Tất cả các test case đều trả về HTTP status 200, trừ validation errors (422)
- `success` field trong response body cho biết kết quả thực tế
- `status_code` trong response body tương ứng với HTTP status codes
- `execution_time` luôn >= 0 và phản ánh thời gian thực tế
