# Agent example

## Important note: go to terminal and enter: "uvicorn app.main:app" firstly.

## Examples

### Happy case
Request:

curl -X POST \
  http://127.0.0.1:8000//agent \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "Các quy định pháp luật về bảo vệ môi trường ở Việt Nam là gì?",
    "top_k": 5,
    "max_steps": 1,
    "timeout_sec": 20
  }'

Response:

{
  "success": true,
  "status_code": 200,
  "step_completed": 1,
  "data": [
    "Chương I ĐIỀU KHOẢN CƠ BẢN; Điều 2. Cơ sở của trách nhiệm hình sự",
    "CHƯƠNG I. CÁC TỘI XÂM PHẠM AN NINH QUỐC GIA; Điều 100. Hình phạt bổ sung.",
    "CHƯƠNG I. ĐIỀU KHOẢN CƠ BẢN Điều 1. Nhiệm vụ của Bộ luật Hình sự; Điều 3.Nguyên tắc xử lý.",
    "Chương I ĐIỀU KHOẢN CƠ BẢN; Điều 4. Trách nhiệm phòng ngừa và đấu tranh chống tội phạm",
    "CHƯƠNG I. ĐIỀU KHOẢN CƠ BẢN Điều 1. Nhiệm vụ của Bộ luật Hình sự; Điều 2. Cơ sở của trách nhiệm hình sự."
  ],
  "message": "Successfully retrieved law chunks",
  "execution_time": 13.083717823028564
}

### Timeout case:
Request:

curl -X POST \
  http://127.0.0.1:8000//agent \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "Các quy định pháp luật về bảo vệ môi trường ở Việt Nam là gì?",
    "top_k": 5,
    "max_steps": 1,
    "timeout_sec": 1
  }'

Response:

{
  "success": false,
  "status_code": 408,
  "step_completed": 0,
  "data": null,
  "message": "Step 1 (retrieve chunks) timed out after 1s",
  "execution_time": 1.0080208778381348
}
