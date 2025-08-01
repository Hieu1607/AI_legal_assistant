# AI Legal Assistant

A comprehensive AI-powered legal document processing and retrieval system with containerized deployment and staging environment support. The system features document retrieval, RAG (Retrieval-Augmented Generation), and multi-step AI Agent capabilities.

## 🏗️ Project Structure

```
AI_legal_assistant/
├── app/                    # FastAPI applications
│   ├── main.py            # Main application router
│   ├── retrieve.py        # Document retrieval service
│   ├── rag.py            # RAG service
│   └── agent.py          # Multi-step AI Agent
├── services/              # Core business logic
├── configs/               # Configuration and logging
├── data/                  # Data storage (mounted in containers)
├── docs/                  # Documentation
├── postman/               # API testing collections
├── tests/                 # Test suites
├── Dockerfile             # Container definition
├── docker-compose.yml     # Multi-container orchestration
├── smoke_test.sh         # Deployment verification
├── DEPLOYMENT.md         # Deployment documentation
└── requirements.txt      # Python dependencies
```

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker Deployment (Week 9)

#### Single Container
```bash
# Build Docker image
docker build -t ai-legal-assistant .

# Run container
docker run -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  ai-legal-assistant
```

#### Docker Compose Orchestration
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Container Features
- **Optimized Build**: Python 3.12 slim base image
- **Volume Mounting**: Persistent data and logs storage
- **Health Checks**: Built-in service monitoring
- **Environment Configuration**: Flexible API key management
- **Auto-restart**: Automatic service recovery

## 📡 API Services

### Main Application (`/`)
- **Health Check**: Service status and availability
- **Interactive Docs**: Swagger UI at `/docs`

### Document Retrieval (`/retrieve`)
**Endpoint**: `POST /retrieve`

Semantic search for relevant legal document chunks.

```json
{
  "question": "What are contract regulations?",
  "top_k": 5
}
```

### RAG Service (`/rag`)
**Endpoint**: `POST /rag`

Retrieval-Augmented Generation for comprehensive legal answers.

```json
{
  "question": "What are the requirements for a valid contract?"
}
```

### AI Agent (`/agent`)
**Endpoint**: `POST /agent`

Multi-step orchestrated legal query processing.

```json
{
  "question": "Contract law requirements",
  "top_k": 5,
  "total_steps": 3,
  "timeout_sec": 30
}
```

## 🚀 Staging Deployment

### Deployment Platforms
The system supports deployment on multiple platforms:
- **Heroku Container Registry**
- **Railway**
- **VPS with Docker**
- **Local Docker Compose**

### Environment Configuration
```bash
# Required environment variables
export GEMINI_API_KEY=your_api_key
export PORT=8000
export PYTHONPATH=/app

# Optional configuration
export RETRIEVAL_TIMEOUT=30
export RAG_TIMEOUT=60
```

### Container Health Monitoring
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## 🧪 Testing & Verification

### Smoke Testing
Automated deployment verification:

```bash
# Run smoke tests
./smoke_test.sh

# Expected output
Testing API
API /retrieve thành công!
API /rag thành công!
API /agent thành công!
All tests passed!
```

### Smoke Test Coverage
- ✅ **Service Availability**: Health check endpoint
- ✅ **Retrieve Functionality**: Document search verification
- ✅ **RAG Integration**: Answer generation testing
- ✅ **Agent Orchestration**: Multi-step workflow validation
- ✅ **Error Handling**: Graceful failure responses

### Integration Testing
```bash
# Postman collection testing
npm install -g newman
npx newman run postman/LegalQA_Integration.postman_collection.json

# Unit testing
python -m pytest tests/ -v --cov=app
```

## 🔧 Development & Operations

### Container Management
```bash
# View running containers
docker-compose ps

# Scale services (if needed)
docker-compose up -d --scale ai-legal-assistant=2

# Update service
docker-compose pull
docker-compose up -d

# Clean up
docker-compose down --volumes --remove-orphans
```

### Log Monitoring
```bash
# Real-time logs
docker-compose logs -f ai-legal-assistant

# Service-specific logs
docker logs <container_id>

# Log files (mounted volumes)
tail -f logs/app.log
tail -f logs/errors.log
```

### Performance Monitoring
- **Resource Usage**: Container memory and CPU monitoring
- **Response Times**: API endpoint performance tracking
- **Health Status**: Automated health check reporting
- **Error Rates**: Service reliability metrics

## 🔄 Rollback Strategy

### Rollback Plan
In case of deployment issues:

1. **Immediate Rollback**:
   ```bash
   docker-compose down
   git checkout previous-stable-tag
   docker-compose up -d
   ```

2. **Version-specific Rollback**:
   ```bash
   docker-compose down
   docker pull ai-legal-assistant:v1.0.0
   docker-compose up -d
   ```

3. **Data Recovery**:
   ```bash
   # Restore data from backup
   docker-compose down
   cp -r backup/data ./data
   docker-compose up -d
   ```

### Deployment Verification
- **Pre-deployment**: Smoke test execution
- **Post-deployment**: Health check validation
- **Monitoring**: Continuous service monitoring
- **Alerts**: Automated failure notifications

## 📊 Container Specifications

### Resource Requirements
- **CPU**: 1-2 cores
- **Memory**: 2-4 GB RAM
- **Storage**: 10-20 GB (including data volumes)
- **Network**: Port 8000 exposed

### Volume Mounts
- `./data:/app/data` - Document and vector storage
- `./logs:/app/logs` - Application logs
- `./configs:/app/configs` - Configuration files

## 🏷️ Current Development

**Week 9 Focus**: Packaging & Staging Deployment
- ✅ Docker containerization with optimized builds
- ✅ Docker Compose orchestration for service management
- ✅ Staging deployment with health monitoring
- ✅ Automated smoke testing for deployment verification
- ✅ Comprehensive rollback planning and procedures
- ✅ Production-ready container configuration

## 📄 License

[Add your license information here]

## 🤝 Contributing

[Add contribution guidelines here]

## 📞 Support

For deployment issues or questions:
1. Check the logs: `docker-compose logs -f`
2. Run smoke tests: `./smoke_test.sh`
3. Verify health: `curl http://localhost:8000/`
4. Consult DEPLOYMENT.md for detailed instructions
