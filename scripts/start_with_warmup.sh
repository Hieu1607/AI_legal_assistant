#!/bin/bash
# Start script with ChromaDB warm up for AI Legal Assistant

set -e  # Exit on any error

echo "Starting AI Legal Assistant with warm up..."

# Run warm up script
echo "Running warm up sequence..."
if python /app/scripts/warmup_chromadb.py; then
    echo "Warm up completed successfully!"
else
    echo "Warm up failed! Exiting..."
    exit 1
fi

echo "Starting FastAPI server..."

# Set production environment
export ENVIRONMENT=production

# Start the main application with uvicorn in background for smoke test
cd /app && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 &
SERVER_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for server to be ready..."
sleep 10

# Run smoke tests by default
echo "Running smoke tests..."
if curl -f http://localhost:${PORT:-8000}/ > /dev/null 2>&1; then
    echo "Server is responsive"
    if [ -f "/app/scripts/smoke_test.sh" ]; then
        echo "  Running comprehensive smoke tests..."
        if bash /app/scripts/smoke_test.sh; then
            echo "All smoke tests passed!"
        else
            echo "Smoke tests failed!"
            kill $SERVER_PID 2>/dev/null || true
            exit 1
        fi
    else
        echo "Smoke test script not found, skipping comprehensive tests"
    fi
else
    echo "Server health check failed!"
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

echo "Server ready and smoke tests completed!"

# Wait for the server process to finish
wait $SERVER_PID
