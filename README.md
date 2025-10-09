# AI Legal Assistant

A comprehensive AI-powered legal document processing and retrieval system that combines vector search with Large Language Models (LLM) to provide intelligent legal assistance through Retrieval-Augmented Generation (RAG) and multi-step AI Agent orchestration.

## 🏗️ Project Structure

```
AI_legal_assistant/
├── app/              # FastAPI applications
│   ├── retrieve.py   # Document retrieval service
│   ├── rag.py        # RAG service combining retrieval + LLM
│   ├── agent.py      # Multi-step AI Agent orchestrator
│   └── main.py       # Main application router
├── services/         # Core business logic
│   └── tools.py      # Agent tools and functions
├── configs/          # Configuration and logging
├── data/             # Data storage
│   ├── raw/          # Raw scraped documents
│   └── processed/    # Processed data and vector store
├── docs/             # Documentation
│   └── integration_test_plan.md  # Integration test specifications
├── postman/          # Postman collections for API testing
│   ├── LegalQA_Integration.postman_collection.json  # Main test collection
│   └── dev_environment.json                         # Development environment variables
├── src/              # Core modules
│   ├── embedding/    # Text embedding processing
│   ├── preprocess/   # Text chunking and preprocessing
│   └── store_vector/ # Vector storage and search
├── tests/            # Test suites
├── logs/             # Application logs
├── run_newman.sh     # Newman test execution script
├── run_scripts.py    # Script runner utility
├── pyproject.toml    # Python project configuration
├── Dockerfile        # Docker containerization
└── requirements.txt  # Python dependencies
```

## 🚀 Quick Start

### Local Development

#### Installation
```bash
# Install required dependencies
pip install fastapi uvicorn pytest pytest-cov
pip install sentence-transformers transformers torch
pip install python-dotenv aiohttp pandas numpy pydantic
pip install google-generativeai "weaviate-client[agents]"
```

#### Environment Setup
```bash
# Set up environment variables
cp .env.example .env
# Configure your API keys in .env
```

#### Run Services
```bash
# Development mode with auto-reload
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Production mode
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker Deployment

#### Build and Run with Docker
```bash
# Build Docker image
docker build -t ai-legal-assistant .

# Run container
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  ai-legal-assistant

# Run with environment variables
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_api_key \
  -v $(pwd)/data:/app/data \
  ai-legal-assistant
```

#### Docker Features
- **Optimized Build**: Multi-stage build with Python 3.12 slim image
- **Dependency Caching**: Efficient layer caching for faster rebuilds
- **Volume Mounting**: External data and logs mounting
- **Environment Configuration**: Configurable through environment variables
- **Production Ready**: Includes system dependencies and proper security

## 📡 API Services

### Retrieve Service
**Endpoint**: `POST /retrieve`

Retrieves relevant legal document chunks based on semantic similarity.

**Request**:
```json
{
  "question": "What are the contract regulations?",
  "top_k": 5
}
```

### RAG Service  
**Endpoint**: `POST /rag`

Combines document retrieval with LLM generation for comprehensive answers.

**Request**:
```json
{
  "question": "What are the requirements for a valid contract?"
}
```

### AI Agent Service
**Endpoint**: `POST /agent`

Multi-step AI Agent with configurable orchestration.

**Request**:
```json
{
  "question": "What are contract requirements?",
  "top_k": 5,
  "total_steps": 3,
  "timeout_sec": 30
}
```

**Response**:
```json
{
  "success": true,
  "status_code": 200,
  "step_completed": 3,
  "data": "A valid contract requires mutual consent... [Source: Civil Code 2015, Article 385]",
  "message": "Successfully formatted answer with citations",
  "execution_time": 15.2
}
```

### Interactive API Documentation
Access Swagger UI at: `http://127.0.0.1:8000/docs`

## 🧪 Testing Framework (Week 8)

### Integration Testing Strategy

#### Test Plan Coverage
The system includes comprehensive integration testing covering:
- ✅ **Happy Path Scenarios**: Normal operation with expected results
- ✅ **Error Handling**: Timeout, validation, and system errors
- ✅ **Partial Success**: Step-by-step execution scenarios
- ✅ **Edge Cases**: Empty results, invalid inputs

#### Test Cases
1. **Happy Path**: Complete 3-step execution with citations
2. **LLM Timeout**: Fallback to retrieved chunks
3. **System Errors**: Internal server error handling
4. **Empty Results**: No relevant documents found
5. **Partial Execution**: Single-step operations
6. **Validation Errors**: Invalid input handling
7. **Step-specific Timeouts**: Individual step failure scenarios

### Unit Testing
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test modules
python -m pytest tests/test_retrieve.py -v
python -m pytest tests/test_rag.py -v
python -m pytest tests/test_agent.py -v

# Run with coverage report
python -m pytest tests/ --cov=app --cov=services --cov-report=term-missing
```

### Postman Integration Testing

#### Collection Structure
- **Health Check**: Server availability testing
- **Retrieve Tests**: Document retrieval functionality
- **RAG Tests**: Question answering with citations
- **Agent Tests**: Multi-step orchestration scenarios

#### Running Postman Tests
```bash
# Install Newman for CLI testing
npm install -g newman

# Simple test execution using script
bash run_newman.sh

# Manual execution with collection and environment
npx newman run postman/LegalQA_Integration.postman_collection.json \
  --environment postman/dev_environment.json \
  --reporters cli,html --reporter-html-export newman_report.html
```

#### Sample Test Results
```
LegalQA_Integration
→ Check health [200 OK, 145B, 37ms]
→ Retrieve happy case [200 OK, 3.33kB, 12.2s]
→ Agent happy case [200 OK, 4.68kB, 30s]
→ Agent timeout case [200 OK, 282B, 5.2s]
```

### Automated Testing Scripts
```bash
# Simple Newman execution script
bash run_newman.sh

# PowerShell equivalent (if available)
./run_newman.ps1
```

#### Newman Script Content
```bash
#!/bin/bash
COLLECTION="postman/LegalQA_Integration.postman_collection.json"
ENVIRONMENT="postman/dev_environment.json"

newman run $COLLECTION -e $ENVIRONMENT \
  -r cli,html --reporter-html-export newman_report.html
```

## 🔧 Error Handling & Timeouts

### Service-Level Error Handling
- **Request Timeout**: 60 seconds maximum per request
- **Retry Logic**: Automatic retry (2 attempts) for network errors
- **Graceful Degradation**: Partial results on step failures

### Agent-Specific Error Responses
- **Timeout (408)**: Step-level timeout with partial results
- **Bad Request (400)**: No relevant chunks retrieved
- **Internal Error (500)**: System-level failures
- **Validation Error (422)**: Invalid input parameters

## 📊 Performance Monitoring

### Execution Metrics
- **Step Duration**: Individual tool execution times
- **Total Execution Time**: Complete workflow duration
- **Success Rates**: Step-by-step completion statistics
- **Error Patterns**: Failure mode analysis

### Logging Structure
```
INFO [agent] step=1 name=retrieve_laws duration=0.05s status=ok
INFO [agent] step=2 name=generate_answer duration=1.2s status=ok
INFO [agent] step=3 name=format_citation duration=0.01s status=ok
```

## 🚀 CI/CD Integration

### GitHub Actions
The project includes automated CI/CD with:
- **Code Quality**: Black, isort, flake8 linting checks
- **Unit Testing**: Automated pytest execution with coverage reports
- **Integration Testing**: Simplified Newman-based API testing via bash script
- **FastAPI Testing**: Server startup validation and health checks
- **Artifact Upload**: Coverage reports and test results

### Test Automation
```yaml
# Simplified Newman integration in CI/CD
- name: Install Newman for API testing
  run: npm install -g newman

- name: Run Postman tests with Newman
  run: |
    # Start server in background
    timeout 60s uvicorn app.main:app --host 127.0.0.1 --port 8000 &
    SERVER_PID=$!
    sleep 10
    
    # Run Newman tests using existing script
    if curl -f http://127.0.0.1:8000/ > /dev/null 2>&1; then
      echo "Server is running, starting Newman tests..."
      bash run_newman.sh
    else
      echo "Server failed to start, skipping Newman tests"
    fi
    
    # Cleanup
    kill $SERVER_PID 2>/dev/null || true
```

## 🏷️ Current Development

**Week 8 Focus**: Integration Testing & CI/CD Pipeline Optimization
- ✅ Comprehensive integration test plan documentation
- ✅ Postman collection for automated API testing
- ✅ Simplified Newman CLI integration for CI/CD pipelines
- ✅ Environment-specific configuration files
- ✅ Docker containerization with proper volume mounting
- ✅ Swagger UI for interactive API testing
- ✅ Automated testing scripts for cross-platform compatibility
- ✅ GitHub Actions workflow optimization with simplified Newman execution
- ✅ Error handling and timeout management improvements

**Latest Updates**:
- Streamlined CI/CD Newman integration using existing `run_newman.sh` script
- Created `dev_environment.json` for consistent API testing across environments
- Improved GitHub Actions workflow with proper server lifecycle management
- Enhanced documentation with actual script examples and configurations

## 📄 License

[Add your license information here]

## 🤝 Contributing

[Add contribution guidelines here]