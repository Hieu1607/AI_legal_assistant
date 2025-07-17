# AI_legal_assistant

## Retrieve Service

### Cài đặt
```bash
# Cài đặt các gói cần thiết
pip install fastapi uvicorn pytest pytest-cov
pip install sentence-transformers transformers torch
pip install python-dotenv aiohttp pandas numpy pydantic
pip install google-generativeai chromadb
```

### Cấu trúc thư mục
```
app/
  retrieve.py           # FastAPI service cho việc truy vấn dữ liệu
tests/
  test_retrieve.py      # Test cho retrieve service
data/
  processed/
    vector_store/       # Dữ liệu vector embeddings
```

### Chạy service
```bash
# Chạy server ở chế độ development
python -m uvicorn app.retrieve:app --reload --host 127.0.0.1 --port 8000

# Hoặc ở chế độ production
python -m uvicorn app.retrieve:app --host 0.0.0.0 --port 8000
```

### API Endpoints
- `GET /`: Endpoint kiểm tra hoạt động của server
- `POST /retrieve`: Endpoint tìm kiếm các đoạn văn bản liên quan
  - Body: `{"question": "Câu hỏi của bạn", "top_k": 5}`
  - Response: Danh sách các đoạn văn bản liên quan

### Test
```bash
# Chạy unit tests
python -m pytest tests/test_retrieve.py -v

# Chạy tests với coverage
python -m pytest tests/test_retrieve.py --cov=app.retrieve --cov-report=term-missing

# Tạo HTML report cho coverage
python -m pytest tests/test_retrieve.py --cov=app.retrieve --cov-report=html
```

## RAG Service

### Cài đặt
```bash
# Cài đặt các gói cần thiết (ngoài các gói đã cài cho Retrieve Service)
pip install google-generativeai
```

### Cấu trúc thư mục
```
app/
  rag.py              # FastAPI service cho RAG (Retrieval-Augmented Generation)
  main.py             # Main FastAPI application kết hợp các modules
tests/
  test_rag.py         # Test cho RAG service
```

### Chạy service
```bash
# Chạy full service bao gồm cả RAG và Retrieve
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Hoặc ở chế độ production
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### API Endpoints
- `POST /rag/`: Endpoint trả lời câu hỏi dựa trên văn bản pháp luật
  - Body: `{"question": "Câu hỏi của bạn"}`
  - Response: Câu trả lời được tạo bởi LLM dựa trên nội dung pháp luật có liên quan

### Giới hạn và Xử lý Lỗi
- **Timeout**: 60 giây cho mỗi request tới LLM, sau đó trả về thông báo lỗi "Hệ thống đang bận vui lòng thử lại sau"
- **Retry**: Tự động thử lại 1 lần khi có lỗi kết nối, với timeout 15 giây cho lần thử lại
- **Xử lý lỗi**:
  - Lỗi kết nối: Trả về "Lỗi mạng"
  - Không tìm thấy thông tin liên quan: Trả về thông báo phù hợp
  - Lỗi hệ thống: Trả về JSON với status_code 500 và thông báo lỗi

### Test
```bash
# Chạy unit tests cho RAG
python -m pytest tests/test_rag.py -v

# Chạy tests với coverage
python -m pytest tests/test_rag.py --cov=app.rag --cov-report=term-missing

# Tạo HTML report cho coverage
python -m pytest tests/test_rag.py --cov=app.rag --cov-report=html

```
