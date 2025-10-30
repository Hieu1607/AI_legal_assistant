# AI Legal Assistant

A comprehensive AI-powered legal document processing and retrieval system that combines vector search with Large Language Models (LLM) to provide intelligent legal assistance through Retrieval-Augmented Generation (RAG).

## 🏗️ Project Structure

```
C:\Users\HP\Desktop\AI_legal_assistant\
├───.dockerignore
├───.env .example
├───.gitignore
├───.pre-commit-config.yaml
├───docker-compose.yml
├───Dockerfile
├───pyproject.toml
├───README.md
├───requirements.txt
├───.git\
└───app\
    ├───main.py
    ├───configs\
    │   ├───__init__.py
    │   ├───logger.py
    │   └───logging.yaml
    ├───models\
    │   └───__init__.py
    ├───routes\
    │   ├───__init__.py
    │   ├───health.py
    │   ├───metrics.py
    │   └───rag.py
    ├───services\
    │   ├───health_service.py
    │   ├───metric_service.py
    │   └───rag_service.py
    └───tools\
        ├───cache_manager.py
        └───weaviate_search.py
```

## 🚀 Quick Start

### Local Development

#### Installation
```bash
# Install required dependencies
pip install -r requirements.txt
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
# Build and Run Docker image
docker-compose up -d --build
```

## 📡 API Services

### RAG Service
**Endpoint**: `POST /rag`

Combines document retrieval with LLM generation for comprehensive answers.

**Request**:
```json
{
  "question": "What are the requirements for a valid contract?"
}
```

### Interactive API Documentation
Access Swagger UI at: `http://127.0.0.1:8000/docs`