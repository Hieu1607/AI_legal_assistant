# AI Legal Assistant

A comprehensive AI-powered legal document processing and retrieval system that combines vector search with Large Language Models (LLM) to provide intelligent legal assistance through Retrieval-Augmented Generation (RAG).

## 🏗️ Project Structure

```
AI_legal_assistant/
├── app/                    # FastAPI application with Model-Controller architecture
│   ├── main.py            # FastAPI entry point
│   ├── routers/           # Controllers (API endpoints)
│   │   ├── retrieve.py    # Retrieval endpoint controller
│   │   └── rag.py         # RAG endpoint controller
│   ├── logic/             # Business logic layer
│   │   ├── retrieve_logic.py  # Embedding retrieval logic
│   │   └── rag_logic.py       # RAG processing logic
│   └── models/            # Data models
│       └── base_model.py  # Pydantic request/response models
├── configs/               # Configuration files and logging setup
├── data/                  # Data storage and processing
│   ├── processed/         # Processed data including chunks and embeddings
│   │   ├── chunks/        # Text chunks from legal documents
│   │   ├── rules/         # Categorized legal rules
│   │   └── vector_store/  # Vector index storage
│   └── raw/               # Raw scraped data
├── demo/                  # Demonstration scripts and notebooks
├── docs/                  # Documentation files
│   └── prompt_template.md # RAG prompt templates
├── scripts/               # Data processing and utility scripts
├── src/                   # Main source code
│   ├── embedding/         # Text embedding modules
│   ├── extract_data/      # Data extraction utilities
│   ├── preprocess/        # Text preprocessing and chunking
│   ├── retrieval/         # Web scraping and data fetching
│   └── store_vector/      # Vector storage and search
└── tests/                 # Unit tests
    └── test_rag.py        # RAG module integration tests
```

## 🔧 Features

### 🤖 Week 6: RAG Module - Retrieve + LLM Integration
- **RAG Pipeline**: Complete Retrieval-Augmented Generation workflow
- **Prompt Template System**: Structured prompt templates with fallback logic
- **LLM Integration**: Google Gemini API integration with timeout handling
- **Performance Monitoring**: Detailed latency tracking and logging
- **Error Handling**: Comprehensive fallback mechanisms and retry logic

### Retrieval Service (Week 5)
- **FastAPI REST API**: High-performance `/retrieve` endpoint for document retrieval
- **Vector Search Integration**: Seamless connection with ChromaDB vector store
- **Structured Response**: JSON responses with chunk metadata and similarity scores
- **Model-Controller Architecture**: Clean separation of concerns

### Data Processing Pipeline
- **Web Scraping**: Automated scraping of legal documents from Vietnamese legal websites
- **Text Extraction**: Clean text extraction from HTML documents
- **Chunking**: Intelligent document segmentation for optimal processing
- **Validation**: Data quality assurance and validation

### Embedding & Vector Search
- **Multiple Embedding Options**: Support for both API-based (Google Gemini) and local models
- **Vector Storage**: ChromaDB integration for efficient similarity search
- **Incremental Indexing**: Support for adding new documents without rebuilding entire index
- **Search & Reranking**: Advanced search capabilities with result reranking

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- FastAPI and Uvicorn for the web service
- ChromaDB for vector storage
- Required dependencies (see `pyproject.toml`)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd AI_legal_assistant
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Copy and configure your API keys
cp .env.example .env
```

### Configuration
Configure your embedding preferences and API keys in the environment file. The system supports:
- Google Gemini API for embeddings
- Local sentence-transformers models
- ChromaDB for vector storage

## 📊 Usage

### RAG Service (Week 6)

Start the FastAPI server:
```bash
uvicorn app.main:app --host localhost --port 8000
```

#### API Endpoints

**POST /rag**
Complete RAG query processing with retrieval and LLM generation.

Request:
```json
{
  "question": "Quy định về hợp đồng lao động là gì?"
}
```

Response:
```json
{
  "status": "success",
  "data": {
    "answer": "Theo chương 3 điều 15 bộ luật lao động 2019, hợp đồng lao động là...",
    "question": "Quy định về hợp đồng lao động là gì?",
    "context_count": 5
  }
}
```

**Fallback Responses:**
- Timeout (≥10s): `"Hệ thống đang bận, vui lòng thử lại sau"`
- No relevant info: `"Không tìm thấy thông tin liên quan đến câu hỏi"`
- Non-legal questions: `"Chào bạn, tôi đã sẵn sàng trả lời với vai trò là một trợ lý ảo pháp luật..."`

**POST /retrieve**
Retrieve relevant legal document chunks based on a question.

Request:
```json
{
  "question": "What are the regulations about contracts?",
  "top_k": 5
}
```

Response:
```json
[
  {
    "chunk_id": "contract_law_article_123",
    "distance": 0.234,
    "score": 0.87,
    "content": "Article content about contracts...",
    "metadatas": {
      "law_id": "contract_law_2015",
      "title": "Contract Law 2015"
    }
  }
]
```

### Data Processing
1. **Scrape legal documents**:
```bash
python scripts/scrape_links_from_url.py
python scripts/scrape_HTML_from_url.py
```

2. **Process and chunk documents**:
```bash
python scripts/process_HTML_to_text.py
python scripts/make_chunks.py
```

3. **Build embeddings**:
```bash
python src/embedding/build_embeddings_with_API.py
# or
python src/embedding/build_embeddings_with_local_model.py
```

4. **Initialize and populate vector store**:
```bash
python src/store_vector/init_index.py
python src/store_vector/index_embeddings.py
```

### Testing the API

**RAG Endpoint:**
```bash
curl -X POST "http://localhost:8000/rag" \
     -H "Content-Type: application/json" \
     -d '{"question": "Quy định về hợp đồng lao động là gì?"}'
```

**Retrieve Endpoint:**
```bash
curl -X POST "http://localhost:8000/retrieve" \
     -H "Content-Type: application/json" \
     -d '{"question": "contract regulations", "top_k": 3}'
```

Using Python requests:
```python
import requests

# RAG query
response = requests.post(
    "http://localhost:8000/rag",
    json={"question": "Quy định về hợp đồng lao động là gì?"}
)
print(response.json())

# Retrieve query
response = requests.post(
    "http://localhost:8000/retrieve",
    json={"question": "What are contract regulations?", "top_k": 5}
)
print(response.json())
```

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

Run specific test modules:
```bash
# RAG module tests (Week 6)
python -m pytest tests/test_rag.py -v

# Retrieval tests (Week 5) 
python -m pytest tests/test_retrieve.py -v

# Other tests
python -m pytest tests/test_chunker.py -v
python -m pytest tests/test_cleaner.py -v
```

Available tests:
- `test_rag.py`: RAG module integration tests (≥4 test cases, ≥80% coverage)
- `test_retrieve.py`: API endpoint testing
- `test_chunker.py`: Text chunking functionality
- `test_cleaner.py`: Text cleaning utilities

## 📝 Error Handling

The API handles various error scenarios with proper fallback mechanisms:

### RAG Module Error Handling
- **LLM Timeout (≥10s)**: `"Hệ thống đang bận, vui lòng thử lại sau"`
- **Network Errors**: Automatic retry (2 attempts) with exponential backoff
- **No Relevant Context**: `"Không tìm thấy thông tin liên quan đến câu hỏi"`
- **Non-Legal Questions**: Polite redirection to legal topics
- **500 Internal Error**: Detailed error logging with fallback response

### General API Error Handling
- **422 Validation Error**: Invalid request format or missing required fields
- **500 Internal Server Error**: Vector store errors or processing failures  
- **200 Empty Results**: Valid request but no matching documents found

All errors include detailed error messages and proper HTTP status codes.

## 📊 Performance Monitoring

### RAG Pipeline Latency Tracking
The system provides detailed performance monitoring:

```
INFO:retrieve_time=0.03,prompt_time=0.01,llm_time=1.2,total=1.24
```

**Performance Metrics:**
- **Retrieve Time**: Vector search latency
- **Prompt Time**: Template construction time  
- **LLM Time**: Language model response time
- **Total Time**: End-to-end request processing
- **Target SLA**: < 2 seconds total response time

### Logging
Comprehensive logging across all modules:
- `logs/app.log`: General application logs
- `logs/rag.log`: RAG-specific performance logs  
- `logs/errors.log`: Error tracking with stack traces
- `logs/info.log`: Information-level logs

**Log Structure:**
```
INFO:retrieve_time=0.03,prompt_time=0.01,llm_time=1.2,total=1.24
INFO:RAG answer successfully
ERROR:An error occurred during asking model: ConnectionError
```

## 🔄 Development Workflow

### Adding New Documents
1. Add new documents to the raw data directory
2. Process documents through the chunking pipeline
3. Generate embeddings for new chunks
4. Update the vector index incrementally

### Code Quality
The project uses:
- **Black** for code formatting
- **isort** for import sorting
- **Pylint** for code analysis
- **pytest** for testing

## 🏷️ Current Development

### 🤖 Week 6: RAG Module Implementation
Current focus on Retrieval-Augmented Generation:

1. **✅ Prompt Template & Fallback Logic**
   - Structured prompt templates in `docs/prompt_template.md`
   - LLM timeout handling (≥10s fallback)
   - Context-aware response generation

2. **✅ RAG Endpoint Implementation** 
   - POST `/rag` endpoint with complete workflow
   - Input validation and error handling
   - Retry logic for network failures (2 attempts)
   - Citation-based responses

3. **✅ Performance Monitoring**
   - Detailed latency tracking with `time.perf_counter()`
   - Structured logging for performance metrics
   - Target SLA monitoring (< 2s response time)

4. **✅ Integration Testing**
   - Comprehensive test suite in `tests/test_rag.py`
   - Mock testing for LLM and vector store
   - Coverage ≥80% for RAG module
   - End-to-end workflow validation

5. **🔄 CI/CD & Documentation**
   - Updated GitHub workflows for RAG testing
   - Complete API documentation with examples
   - Performance benchmarking and monitoring

### Previous Milestones
- **Week 5**: Retrieval Service with FastAPI REST API
- **Weeks 1-4**: Data pipeline, embedding, and vector search infrastructure

## 🚀 Production Deployment

For production deployment:

### RAG Service Configuration
1. **Environment Variables**: Configure Gemini API keys and timeout settings
2. **Performance Tuning**: Optimize vector search and LLM call parameters
3. **Rate Limiting**: Implement API rate limiting to prevent abuse
4. **Caching**: Add response caching for frequently asked questions
5. **Monitoring**: Set up performance monitoring and alerting

### Infrastructure Requirements  
1. **WSGI Server**: Use Gunicorn for production deployment
2. **Load Balancing**: Configure nginx for high availability
3. **Logging**: Centralized logging with log rotation
4. **Health Checks**: Implement comprehensive health monitoring
5. **Security**: API authentication and input sanitization

### Performance Targets
- **Response Time**: < 2 seconds for 95% of requests
- **Availability**: 99.9% uptime
- **Throughput**: Support for concurrent requests
- **Resource Usage**: Optimized memory and CPU utilization

## 📄 License

[Add your license information here]

## 🤝 Contributing

[Add contribution guidelines here]