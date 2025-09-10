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
git clone https://github.com/Hieu1607/AI_legal_assistant_production.git

# Change to project directory
cd AI_legal_assistant_production

# Build Docker image
echo "Building Docker image..."
docker-compose build

# Start containers
echo "Starting containers..."
docker-compose up -d

echo "Setup complete!"
echo ""
echo "Application is starting up..."
echo "You can access the application at:"
echo "- API Documentation: http://localhost:8000/docs"
echo "- Health Check: http://localhost:8000/"
echo ""
echo "Wait a few moments for the containers to fully start, then check the health endpoint."
