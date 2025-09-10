#!/bin/bash

# AI Legal Assistant Quick Installer
# Run this script on any Linux/macOS machine to setup the project

echo "AI Legal Assistant - Quick Setup"
echo "================================="

# Check prerequisites
echo "Checking prerequisites..."

# Check Git
if command -v git >/dev/null 2>&1; then
    echo "Git: OK"
else
    echo "❌ Error: Git is not installed. Please install Git first."
    echo "Ubuntu/Debian: sudo apt-get install git"
    echo "CentOS/RHEL: sudo yum install git"
    echo "macOS: brew install git"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check Docker
if command -v docker >/dev/null 2>&1; then
    echo "Docker: OK"
else
    echo "❌ Error: Docker is not installed. Please install Docker first."
    echo "Ubuntu/Debian: sudo apt-get install docker.io"
    echo "CentOS/RHEL: sudo yum install docker"
    echo "macOS: brew install --cask docker"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if Docker is running
echo "Checking if Docker is running..."
dockerRunning=false
dockerOutput=""

dockerOutput=$(docker info 2>&1)
dockerExitCode=$?

if [ $dockerExitCode -eq 0 ]; then
    dockerRunning=true
    echo "Docker daemon: Running"
else
    echo "Docker command exit code: $dockerExitCode"
    echo "Docker output: $dockerOutput"
fi

if [ "$dockerRunning" = false ]; then
    echo ""
    echo "❌ Docker Desktop is not running!"
    echo ""
    echo "Please start Docker first:"
    echo "Linux: sudo systemctl start docker"
    echo "       sudo systemctl enable docker"
    echo "macOS: Start Docker Desktop application"
    echo ""
    echo "After starting Docker, please run this script again."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "✅ All prerequisites met!"
echo ""

# Move to parent directory to avoid conflicts with project cloning
originalLocation=$(pwd)

# Download and run setup script
echo "Downloading setup script..."
if wget -q "https://raw.githubusercontent.com/Hieu1607/AI_legal_assistant_production/main/setup.sh" -O "ai_legal_setup.sh" 2>/dev/null; then
    echo "Running setup..."
    chmod +x ai_legal_setup.sh
    ./ai_legal_setup.sh
    cd "$originalLocation"
    rm -f ai_legal_setup.sh
elif curl -s "https://raw.githubusercontent.com/Hieu1607/AI_legal_assistant_production/main/setup.sh" -o "ai_legal_setup.sh" 2>/dev/null; then
    echo "Running setup..."
    chmod +x ai_legal_setup.sh
    ./ai_legal_setup.sh
    cd "$originalLocation"
    rm -f ai_legal_setup.sh
else
    echo "❌ Error downloading setup script"
    cd "$originalLocation"
    read -p "Press Enter to exit..."
    exit 1
fi

# Return to original location
cd "$originalLocation"

read -p "✅ Press Enter to finish"
