# Check if Docker is running
Write-Host "Checking Docker status..."
try {
    docker info | Out-Null
    Write-Host "Docker is running: OK"
} catch {
    Write-Host "Error: Docker is not running. Please start Docker Desktop first."
    exit 1
}

# Clone repository
Write-Host "Cloning repository..."
git clone https://github.com/Hieu1607/AI_legal_assistant_production.git

# Change to project directory
Set-Location AI_legal_assistant_production

# Build Docker image
Write-Host "Building Docker image..."
docker-compose build

# Start containers
Write-Host "Starting containers..."
docker-compose up -d

Write-Host "Setup complete!"
Write-Host ""
Write-Host "Application is starting up..."
Write-Host "You can access the application at:"
Write-Host "- API Documentation: http://localhost:8000/docs"
Write-Host "- Health Check: http://localhost:8000/"
Write-Host ""
Write-Host "Wait a few moments for the containers to fully start, then check the health endpoint."
