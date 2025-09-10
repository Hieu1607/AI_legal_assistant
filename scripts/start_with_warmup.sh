#!/bin/bash
# Start script with ChromaDB warm up for AI Legal Assistant

set -e  # Exit on any error

echo "🚀 Starting AI Legal Assistant with warm up..."

# Run warm up script
echo "🔥 Running warm up sequence..."
if python /app/scripts/warmup_chromadb.py; then
    echo "✅ Warm up completed successfully!"
else
    echo "❌ Warm up failed! Exiting..."
    exit 1
fi

echo "🌟 Starting FastAPI server..."

# Set production environment
export ENVIRONMENT=production

# Start the main application with uvicorn (production mode)
cd /app && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
