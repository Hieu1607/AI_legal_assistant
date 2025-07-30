# Smoke Testing Guide

## Tổng quan

Smoke test là quá trình kiểm tra nhanh các chức năng cơ bản của hệ thống để đảm bảo ứng dụng hoạt động đúng sau khi khởi động.

## Quy trình Smoke Test

### 1. Timeline

```
[0s]     Khởi động warmup ChromaDB
[30s]    Khởi động FastAPI server  
[90s]    Chờ server ổn định (60s timeout)
[90s]    Chạy smoke tests
[120s]   Hoàn thành - Hệ thống sẵn sàng
```

### 2. Tests Được Thực Hiện

#### Test 1: `/retrieve` Endpoint
- **Method**: POST
- **URL**: `http://localhost:8000/retrieve`
- **Payload**: 
  ```json
  {
    "question": "Chương I điều 1 luật dân sự là gì?",
    "top_k": 5
  }
  ```
- **Expected Response**: HTTP 200
- **Purpose**: Kiểm tra tìm kiếm vector database

#### Test 2: `/rag` Endpoint  
- **Method**: POST
- **URL**: `http://localhost:8000/rag`
- **Payload**:
  ```json
  {
    "question": "Chương I điều 1 luật dân sự là gì?"
  }
  ```
- **Expected Response**: HTTP 200
- **Purpose**: Kiểm tra RAG pipeline hoàn chỉnh

### 3. Cách Chạy Smoke Test

#### Option A: Tự động với Docker Compose
```bash
# Windows
.\start_with_tests.ps1

# Linux/macOS  
./start_with_tests.sh
```

#### Option B: Manual Docker Compose
```bash
docker-compose -f docker-compose.smoke-test.yml up
```

#### Option C: Enable trong Docker Compose chính
Uncomment dòng này trong `docker-compose.yml`:
```yaml
# command: ["/app/scripts/start_with_smoke_test.sh"]
```

#### Option D: Chạy riêng biệt
```bash
# Sau khi server đã chạy
bash scripts/smoke_test.sh
```

### 4. Troubleshooting

#### Server không khởi động trong 60s
- **Nguyên nhân**: Máy chậm, model download lâu
- **Giải pháp**: Tăng timeout trong `start_with_smoke_test.sh`

#### Test `/retrieve` fail
- **Nguyên nhân**: ChromaDB chưa có data hoặc embeddings
- **Giải pháp**: Kiểm tra `scripts/download_gdown.py` đã chạy

#### Test `/rag` fail  
- **Nguyên nhân**: AI model không khả dụng hoặc API key
- **Giải pháp**: Kiểm tra environment variables

#### Curl command not found
- **Nguyên nhân**: Curl không được cài trong container
- **Giải pháp**: Dockerfile đã được cập nhật để cài curl

### 5. Script Files

- `scripts/smoke_test.sh` - Smoke test script chính
- `scripts/start_with_smoke_test.sh` - Startup script với smoke test
- `docker-compose.smoke-test.yml` - Docker compose với smoke test
- `start_with_tests.sh` / `start_with_tests.ps1` - Helper scripts

### 6. Monitoring

Theo dõi logs trong quá trình smoke test:
```bash
# Real-time logs
docker-compose -f docker-compose.smoke-test.yml logs -f

# Specific service logs
docker-compose logs -f ai-legal-assistant
```

### 7. Success Indicators

✅ **Thành công khi thấy**:
```
✅ Initial warm up completed successfully!
✅ Server started successfully!  
✅ Post-startup warm up completed successfully!
🧪 Running smoke tests...
API /retrieve thành công!
API /rag thành công!
✅ All smoke tests passed! System is ready.
🎉 AI Legal Assistant is fully operational!
```

❌ **Thất bại khi thấy**:
```
❌ Server failed to start!
❌ Smoke tests failed! Check the logs for issues.
Lỗi API /retrieve, mã phản hồi: 500
Lỗi API /rag, mã phản hồi: 500
```

### 8. Performance Expectations

- **Total startup time**: ~2-3 phút
- **API response time**: < 5 giây
- **Memory usage**: < 2GB
- **CPU usage**: < 80% during startup
