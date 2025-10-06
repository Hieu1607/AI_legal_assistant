# Super minimal Dockerfile
# pragma: allowlist nextline critical_high_vulnerabilities
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

WORKDIR /app

# Install system dependencies including curl for smoke tests
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*
    
    # Copy requirements files
COPY requirements.txt ./

# Install Python packages from requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY app/ ./app/
COPY src/ ./src/
COPY configs/ ./configs/
COPY services/ ./services/
COPY scripts/ ./scripts/

# Copy essential data files
COPY titles.txt ./

# Create basic directories
RUN mkdir -p logs

# Fix line endings and make startup scripts executable
RUN chmod +x /app/scripts/start_with_warmup.sh && \
    chmod +x /app/scripts/smoke_test.sh && \
    sed -i 's/\r$//' /app/scripts/start_with_warmup.sh && \
    sed -i 's/\r$//' /app/scripts/smoke_test.sh 

EXPOSE 8000

# For local development with warmup, use: docker run ... /app/scripts/start_with_warmup.sh
CMD ["/app/scripts/start_with_warmup.sh"]


