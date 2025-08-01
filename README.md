# AI Legal Assistant

A comprehensive AI-powered legal document processing and retrieval system that leverages natural language processing and vector search capabilities to assist with legal document analysis and information retrieval.

## 🏗️ Project Structure

```
AI_legal_assistant/
├── app/              # FastAPI application
│   └── retrieve.py   # Retrieval service endpoint
├── configs/          # Configuration files and logging setup
├── data/             # Data storage and processing
│   ├── processed/    # Processed data including chunks and embeddings
│   │   ├── chunks/   # Text chunks from legal documents
│   │   ├── rules/    # Categorized legal rules
│   │   └── vector_store/  # Vector index storage
│   └── raw/          # Raw scraped data
├── demo/             # Demonstration scripts and notebooks
├── docs/             # Documentation files
├── scripts/          # Data processing and utility scripts
├── src/              # Main source code
│   ├── embedding/    # Text embedding modules
│   ├── extract_data/ # Data extraction utilities
│   ├── preprocess/   # Text preprocessing and chunking
│   ├── retrieval/    # Web scraping and data fetching
│   └── store_vector/ # Vector storage and search
└── tests/            # Unit tests
```

## 🔧 Features

### Retrieval Service (Week 5)
- **FastAPI REST API**: High-performance `/retrieve` endpoint for document retrieval
- **Vector Search Integration**: Seamless connection with ChromaDB vector store
- **Structured Response**: JSON responses with chunk metadata and similarity scores
- **Error Handling**: Comprehensive error handling with proper HTTP status codes
- **Logging**: Detailed request/response logging for monitoring and debugging

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

### Retrieval Service

Start the FastAPI server:
```bash
uvicorn app.retrieve:app --host localhost --port 8000
```

#### API Endpoints

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

**GET /**
Health check endpoint.

**GET /shutdown**
Gracefully shutdown the server.

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

Using curl:
```bash
curl -X POST "http://localhost:8000/retrieve" \
     -H "Content-Type: application/json" \
     -d '{"question": "contract regulations", "top_k": 3}'
```

Using Python requests:
```python
import requests

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
python -m pytest tests/test_retrieve.py -v
```

Available tests:
- `test_chunker.py`: Text chunking functionality
- `test_cleaner.py`: Text cleaning utilities
- `test_retrieve.py`: API endpoint testing

## 📝 Error Handling

The API handles various error scenarios:

- **422 Validation Error**: Invalid request format or missing required fields
- **500 Internal Server Error**: Vector store errors or processing failures
- **200 Empty Results**: Valid request but no matching documents found

All errors include detailed error messages and proper HTTP status codes.

## 📊 Logging

The application provides comprehensive logging:
- Request/response logging for all API calls
- Error tracking with stack traces
- Performance metrics for retrieval operations
- Configurable log levels (INFO, ERROR, DEBUG)

Logs are written to:
- `logs/app.log`: General application logs
- `logs/errors.log`: Error-specific logs
- `logs/info.log`: Information-level logs

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

This project is actively developed with focus on:
- **Week 5**: Retrieval Service Deployment
- FastAPI REST API implementation
- Comprehensive error handling and logging
- Unit testing and API documentation
- Performance optimization for production deployment

## 🚀 Production Deployment

For production deployment:
1. Configure environment variables for production
2. Set up proper logging levels
3. Use a production WSGI server (Gunicorn)
4. Configure load balancing if needed
5. Set up monitoring and health checks

## 📄 License

[Add your license information here]

## 🤝 Contributing

[Add contribution guidelines here]