# Sử dụng Python 3.12 slim image làm base
FROM python:3.12.3-slim

# Thiết lập biến môi trường
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && apt-get upgrade -y \
    && apt-get dist-upgrade -y \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file trước để tận dụng Docker layer caching
COPY requirements.txt* ./

# Nếu có requirements.txt thì cài đặt, nếu không thì cài đặt các package cần thiết
RUN if [ -f requirements.txt ]; then \
        pip install --no-cache-dir -r requirements.txt; \
    else \
        pip install --no-cache-dir \
            fastapi==0.104.1 \
            uvicorn[standard]==0.24.0 \
            sentence-transformers==2.2.2 \
            chromadb==0.4.18 \
            beautifulsoup4==4.12.2 \
            requests==2.31.0 \
            numpy==1.24.3 \
            pydantic==2.5.0 \
            python-multipart==0.0.6 \
            aiofiles==23.2.1; \
    fi

# Copy source code (loại trừ data lớn)
COPY app/ ./app/
COPY src/ ./src/
COPY configs/ ./configs/
COPY services/ ./services/
COPY *.py ./

# Tạo cấu trúc thư mục data trống (sẽ được mount từ host)
RUN mkdir -p data/raw \
    && mkdir -p data/processed/chunks \
    && mkdir -p data/processed/texts \
    && mkdir -p data/processed/new_texts \
    && mkdir -p data/processed/vector_store \
    && mkdir -p logs

# Expose port
EXPOSE ${PORT}

# Command để chạy ứng dụng
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
