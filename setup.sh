#!/bin/bash

# Check if Docker is running
echo "Checking Docker status..."
if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    echo "On Linux: sudo systemctl start docker"
    echo "On macOS: Start Docker Desktop application"
    exit 1
fi
echo "Docker is running: OK"

# Clone repository
echo "Cloning repository..."
git clone https://github.com/Hieu1607/AI_legal_assistant.git

# Change to project directory
cd AI_legal_assistant

# Switch to the correct branch
echo "Switching to week_10 branch..."
git checkout week_10

# Build Docker image
echo "Building Docker image..."
docker-compose build

# Start containers
echo "Starting containers..."
docker-compose up -d

echo "Setup complete!"
echo ""
echo "Application is starting up with enhanced cache system..."
echo "You can access the application at:"
echo "- API Documentation: http://localhost:8000/docs"
echo "- Health Check: http://localhost:8000/"
echo "- RAG Endpoint: http://localhost:8000/rag"
echo "- Metrics: http://localhost:8000/metrics"
echo ""
echo "Wait a few moments for the containers to fully start, then check the health endpoint."
echo ""
echo "New in this version:"
echo "- Smart caching system for improved response times"
echo "- Enhanced RAG capabilities with Groq LLM"
echo "- Performance monitoring and metrics"
