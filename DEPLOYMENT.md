# AI Legal Assistant - Deployment Guide

## 🚀 Fresh Deployment (Máy mới hoàn toàn)

### Linux/macOS

```bash
# Download và chạy deployment script
curl -fsSL https://raw.githubusercontent.com/Hieu1607/AI_legal_assistant/week_6_and_week_7/deploy-fresh.sh | bash
```

Hoặc manual:

```bash
# 1. Clone repository
git clone -b week_6_and_week_7 https://github.com/Hieu1607/AI_legal_assistant.git
cd AI_legal_assistant

# 2. Run deployment script
chmod +x deploy-fresh.sh
./deploy-fresh.sh
```

### Windows PowerShell

```powershell
# Download và chạy script
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Hieu1607/AI_legal_assistant/week_6_and_week_7/deploy-fresh.ps1" -OutFile "deploy-fresh.ps1"
.\deploy-fresh.ps1
```

Hoặc manual:

```powershell
# 1. Clone repository
git clone -b week_6_and_week_7 https://github.com/Hieu1607/AI_legal_assistant.git
cd AI_legal_assistant

# 2. Run deployment script
.\deploy-fresh.ps1
```

## 📋 Prerequisites

### Tự động cài đặt (Linux)
Script sẽ tự động cài:
- Docker & Docker Compose
- Git
- Curl, wget, unzip

### Manual installation cần thiết

#### Windows:
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- [Git for Windows](https://git-scm.com/download/win)

#### macOS:
- [Docker Desktop](https://www.docker.com/products/docker-desktop)
- Git (via Xcode Command Line Tools)

## 🏭 Production Deployment

### Option 1: Development mode (data trên host)
```bash
docker-compose up -d
```

### Option 2: Production mode (isolated data)
```bash
# Tạo data directories cho production
sudo mkdir -p /opt/ai-legal-assistant/{data,logs}
sudo chown $USER:$USER /opt/ai-legal-assistant/{data,logs}

# Deploy với production config
docker-compose -f docker-compose.prod.yml up -d
```

## 📁 Data Management cho deployment mới

### 1. Cấu trúc thư mục tự động tạo:
```
AI_legal_assistant/
├── data/
│   ├── raw/                    # Raw scraped data
│   └── processed/
│       ├── chunks/             # Chunked documents
│       ├── texts/              # Processed text files
│       ├── new_texts/          # Latest text processing
│       └── vector_store/       # ChromaDB embeddings
└── logs/                       # Application logs
```

### 2. Import data existing (nếu có):

#### Từ backup file:
```bash
# Download data backup
wget https://your-backup-url/data-backup.zip
unzip data-backup.zip -d ./

# Hoặc copy từ máy khác
rsync -av user@old-server:/path/to/AI_legal_assistant/data/ ./data/
```

#### Từ Google Drive/Cloud Storage:
```bash
# Google Drive (với gdown)
pip install gdown
gdown "https://drive.google.com/uc?id=YOUR_FILE_ID" -O data-backup.zip
unzip data-backup.zip -d ./
```

### 3. Khởi tạo data từ đầu:
```bash
# Chạy data scraping pipeline
docker-compose exec ai-legal-assistant python scripts/scrape_HTML_from_url.py
docker-compose exec ai-legal-assistant python scripts/process_HTML_to_text.py
docker-compose exec ai-legal-assistant python scripts/make_chunks.py
```

## 🔧 Management Commands

### Service management:
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# View logs
docker-compose logs -f

# Update application
git pull
docker-compose up --build -d
```

### Data operations:
```bash
# Backup data
tar -czf data-backup-$(date +%Y%m%d).tar.gz data/ logs/

# Restore data
tar -xzf data-backup.tar.gz

# Reset data (⚠️ WARNING: Deletes all data)
docker-compose down
rm -rf data/ logs/
mkdir -p data/{raw,processed/{chunks,texts,new_texts,vector_store}} logs/
docker-compose up -d
```

## 🌐 Access Points

After successful deployment:

- **API**: http://localhost:8000
- **Interactive API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔒 Security Notes cho Production

1. **Change default ports**: Sửa port mapping trong docker-compose.yml
2. **Add reverse proxy**: Nginx/Traefik cho HTTPS
3. **Environment variables**: Sử dụng .env file cho secrets
4. **Resource limits**: Set trong docker-compose.prod.yml
5. **Regular backups**: Schedule data backups

## 📞 Troubleshooting

### Common issues:

1. **Port 8000 already in use**:
   ```bash
   # Find process using port
   lsof -i :8000  # Linux/macOS
   netstat -ano | findstr :8000  # Windows

   # Change port in docker-compose.yml
   ports:
     - "8080:8000"  # Use port 8080 instead
   ```

2. **Docker not running**:
   ```bash
   # Linux
   sudo systemctl start docker

   # Windows/macOS: Start Docker Desktop
   ```

3. **Permission denied**:
   ```bash
   # Add user to docker group (Linux)
   sudo usermod -aG docker $USER
   # Logout and login again
   ```

4. **Memory issues**:
   ```bash
   # Increase Docker memory limit
   # Docker Desktop -> Settings -> Resources -> Memory
   ```

## 📊 Monitoring

### Health monitoring:
```bash
# Check service health
curl http://localhost:8000/health

# Check container stats
docker stats

# Check logs
docker-compose logs --tail=50 -f ai-legal-assistant
```
