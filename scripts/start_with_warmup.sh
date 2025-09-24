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
cd /app && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2 &
SERVER_PID=$!

# Wait for server to be ready
echo "⏳ Waiting for server to be ready..."
sleep 15

# Run smoke tests by default
echo "🧪 Running smoke tests..."

# Try health check multiple times with better error handling
MAX_RETRIES=6
RETRY_COUNT=0
SERVER_READY=false
PORT=${PORT:-8000}

echo "🔍 Testing server connectivity on port $PORT..."

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    echo "Health check attempt $((RETRY_COUNT + 1))/$MAX_RETRIES..."
    
    # Try multiple approaches to check server health
    if command -v curl >/dev/null 2>&1; then
        # Use curl if available
        if curl -f -s --connect-timeout 5 --max-time 10 "http://localhost:$PORT/" > /dev/null 2>&1; then
            echo "✅ Server is responsive (curl)"
            SERVER_READY=true
            break
        elif curl -f -s --connect-timeout 5 --max-time 10 "http://127.0.0.1:$PORT/" > /dev/null 2>&1; then
            echo "✅ Server is responsive (curl 127.0.0.1)"
            SERVER_READY=true
            break
        elif curl -f -s --connect-timeout 5 --max-time 10 "http://0.0.0.0:$PORT/" > /dev/null 2>&1; then
            echo "✅ Server is responsive (curl 0.0.0.0)"
            SERVER_READY=true
            break
        fi
    fi
    
    # Fallback: check if process is running and port is listening
    if netstat -tuln 2>/dev/null | grep ":$PORT " > /dev/null 2>&1; then
        echo "✅ Server port is listening"
        SERVER_READY=true
        break
    fi
    
    echo "⏳ Server not ready yet, waiting 8 more seconds..."
    sleep 8
    RETRY_COUNT=$((RETRY_COUNT + 1))
done

if [ "$SERVER_READY" = true ]; then
    # Run the smoke test script
    if [ -f "./scripts/smoke_test.sh" ]; then
        chmod +x "./scripts/smoke_test.sh"
        echo "🚀 Executing smoke tests..."
        if ./scripts/smoke_test.sh; then
            echo "✅ All smoke tests passed!"
        else
            echo "❌ Smoke tests failed!"
            kill $SERVER_PID 2>/dev/null || true
            exit 1
        fi
    elif [ -f "/app/scripts/smoke_test.sh" ]; then
        echo "🚀 Running comprehensive smoke tests..."
        if bash /app/scripts/smoke_test.sh; then
            echo "✅ All smoke tests passed!"
        else
            echo "❌ Smoke tests failed!"
            kill $SERVER_PID 2>/dev/null || true
            exit 1
        fi
    else
        echo "⚠️ Smoke test script not found, skipping comprehensive tests"
    fi
else
    echo "❌ Server health check failed after $MAX_RETRIES attempts!"
    echo "🔍 Debugging info:"
    echo "Port: $PORT"
    if command -v netstat >/dev/null 2>&1; then
        echo "Open ports:"
        netstat -tuln | grep LISTEN
    fi
    if command -v ps >/dev/null 2>&1; then
        echo "Python processes:"
        ps aux | grep python || echo "No Python processes found"
    fi
    kill $SERVER_PID 2>/dev/null || true
    exit 1
fi

echo "Server ready and smoke tests completed!"

# Wait for the server process to finish
wait $SERVER_PID
