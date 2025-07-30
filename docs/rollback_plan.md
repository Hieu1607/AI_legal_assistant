# Docker Deployment Rollback Plan - AI Legal Assistant

## Tổng quan
Tài liệu này mô tả các bước rollback cho Docker deployment của hệ thống AI Legal Assistant khi gặp sự cố trong quá trình deploy.

## Các tình huống cần rollback

### 1. Container startup failures
### 2. Docker image build errors
### 3. Service connectivity issues
### 4. Resource allocation problems
### 5. Configuration errors trong Docker Compose

---

## 1. Quick Docker Rollback

### 1.1 Immediate Service Rollback
```bash
# Stop failed deployment
docker-compose down

# Rollback to previous working version
docker-compose up -d

# Or rollback specific service
docker-compose stop ai-legal-assistant
docker-compose up -d ai-legal-assistant
```

### 1.2 Container Health Check
```bash
# Check container status
docker-compose ps

# Check container logs
docker-compose logs ai-legal-assistant

# Check resource usage
docker stats
```

---

## 2. Docker Image Rollback

### 2.1 Rollback to Previous Image Tag
```bash
# List available images
docker images | grep ai-legal-assistant

# Stop current containers
docker-compose down

# Edit docker-compose.yml to use previous tag
# ai-legal-assistant:
#   image: ai-legal-assistant:v1.0.0  # previous stable version

# Restart with previous image
docker-compose up -d

# Verify deployment
docker-compose ps
```

---

## 3. Environment-Specific Rollback

### 3.1 Development Environment
```bash
# Quick rollback cho dev
docker-compose down
git checkout HEAD~1
docker-compose build --no-cache
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

### 3.2 Production Environment
```bash
# Production rollback với zero downtime
# Step 1: Deploy previous version to staging containers
docker-compose up -d --scale ai-legal-assistant=2

# Step 2: Stop new containers
docker-compose stop ai-legal-assistant_1

# Step 3: Update load balancer to point to stable containers
# Step 4: Remove failed containers
docker-compose rm -f ai-legal-assistant_1
```

---

## 4. Emergency Docker Rollback

### Khi containers hoàn toàn không start được:

```bash
#!/bin/bash
# emergency_docker_rollback.sh

echo "=== EMERGENCY DOCKER ROLLBACK STARTED ==="

# 1. Force stop and remove all containers
echo "Stopping all containers..."
docker-compose down --remove-orphans --volumes
docker system prune -f

# 2. Restore docker-compose to last known good
echo "Restoring docker-compose configuration..."
git checkout HEAD~1 -- docker-compose.yml

# 3. Remove current images
echo "Removing current images..."
docker rmi $(docker images ai-legal-assistant -q) 2>/dev/null || true

# 4. Rebuild from previous commit
echo "Rebuilding from previous commit..."
docker-compose build --no-cache

# 5. Start services
echo "Starting services..."
docker-compose up -d

# 6. Wait for services
echo "Waiting for services to start..."
sleep 30

# 7. Health check
echo "Running health check..."
docker-compose ps
curl -f http://localhost:8000/health || echo "API still not ready"

echo "=== EMERGENCY DOCKER ROLLBACK COMPLETED ==="
```

---

## 5. Rollback Verification

### 5.1 Container Health Check
```bash
# Check all containers are running
docker-compose ps

# Check container logs for errors
docker-compose logs --tail=50 ai-legal-assistant

# Check resource usage
docker stats --no-stream
```

### 5.2 Service Connectivity Test
```bash
# Test API endpoint
curl -X GET http://localhost:8000/health

# Test retrieve endpoint
curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"question":"test query","top_k":1}'

# Test container internal health
docker-compose exec ai-legal-assistant curl http://localhost:8000/health
```

### 5.3 Deployment Smoke Test
```bash
# Run smoke test script
bash smoke_test.sh

# Or manual verification
echo "Testing API endpoints..."
curl -s http://localhost:8000/health | grep -q "OK" && echo "✓ Health check passed"
curl -s -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"question":"test","top_k":1}' | grep -q "results" && echo "✓ Retrieve endpoint working"
```

---

## 6. Docker Deployment Best Practices

### 6.1 Pre-Deployment Backup
```bash
# Before any deployment, backup current state
docker-compose ps > deployment_state_$(date +%Y%m%d_%H%M%S).txt
docker images > images_backup_$(date +%Y%m%d_%H%M%S).txt

# Tag current working images
docker tag ai-legal-assistant:latest ai-legal-assistant:stable-$(date +%Y%m%d)
```

### 6.2 Rolling Deployment Strategy
```bash
# Deploy new version alongside old
docker-compose up -d --scale ai-legal-assistant=2

# Test new instance
curl http://localhost:8000/health

# If successful, scale down old version
docker-compose up -d --scale ai-legal-assistant=1

# Remove old containers
docker-compose ps -q ai-legal-assistant | head -1 | xargs docker stop
```

### 6.3 Blue-Green Deployment
```bash
# Prepare green environment (use different ports)
docker-compose up -d

# Test green environment
curl http://localhost:8000/health

# Switch traffic (update nginx/load balancer config)
# If issues, rollback by switching back to blue environment
```

---

## 7. Monitoring và Alerts

### 7.1 Container Monitoring
```bash
# Monitor container health
docker-compose ps
docker stats --no-stream

# Check disk usage
docker system df

# Monitor logs
docker-compose logs -f --tail=100
```

### 7.2 Automated Health Checks
```bash
#!/bin/bash
# health_monitor.sh

while true; do
    if ! curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "$(date): API health check failed - initiating rollback"
        ./emergency_docker_rollback.sh
        break
    fi
    sleep 30
done
```
---

## Kết luận

Docker rollback plan này cung cấp các bước cụ thể để nhanh chóng rollback deployment khi gặp sự cố. Trọng tâm là đảm bảo service availability và khả năng phục hồi nhanh chóng thông qua Docker container orchestration.

**Lưu ý quan trọng**:
- Luôn backup state hiện tại trước khi rollback
- Test rollback procedures thường xuyên
- Monitor containers continuously sau rollback
- Document mọi incident để improve process
