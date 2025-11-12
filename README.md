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

## 🛠️ Technologies Used

- **Backend**: FastAPI, Uvicorn
- **Vector Database**: Weaviate
- **Containerization**: Docker
- **Core Libraries**:
  - `pydantic` for data validation.
  - `python-dotenv` for managing environment variables.
  - `prometheus-client` for exposing metrics.
  - `pyyaml` for configuration.

## 🔑 Environment Variables Setup

To run the application, you need to set up the following environment variables in a `.env` file. You can copy the example file:

```bash
cp .env.example .env
```

The `.env` file requires `WEAVIATE_URL` and `WEAVIATE_API_KEY`. Follow these steps to obtain them:

1.  **Login to Weaviate Cloud**: Go to [Weaviate Cloud Console](https://console.weaviate.cloud/) and log in to your account.
2.  **Navigate to Your Cluster**: Select the Weaviate cluster that contains your data.
3.  **Copy Cluster URL**: In the cluster details, find and copy the **Cluster URL**. This will be your `WEAVIATE_URL`.
4.  **Create an API Key**:
    *   Click on the **"API Keys"** tab.
    *   Click the **"Create API Key"** button.
    *   Give the key a descriptive name, grant it **Admin** or **Viewer** permissions as needed, and create it.
    *   Copy the generated key immediately. This will be your `WEAVIATE_API_KEY`.

After setting these variables, your `.env` file should look like this:

```env
WEAVIATE_URL="<YOUR_WEAVIATE_URL>"
WEAVIATE_API_KEY="<YOUR_WEAVIATE_API_KEY>"
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