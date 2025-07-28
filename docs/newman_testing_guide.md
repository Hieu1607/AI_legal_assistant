# Newman API Testing Scripts

Scripts để chạy Newman API tests cho AI Legal Assistant project.

## Files

- `run_newman.sh` - Bash script cho Linux/macOS
- `run_newman.ps1` - PowerShell script cho Windows
- `postman/` - Thư mục chứa Postman collections và environments

## Cài đặt

### 1. Cài đặt Newman
```bash
npm install -g newman
```

### 2. Cài đặt dependencies
```bash
pip install uvicorn fastapi
```

## Sử dụng

### Windows (PowerShell)
```powershell
# Chạy với cấu hình mặc định
.\run_newman.ps1

# Chạy với custom collection
.\run_newman.ps1 -Collection "my-tests.json" -Port 8080

# Xem help
.\run_newman.ps1 -Help
```

### Linux/macOS (Bash)
```bash
# Chạy với cấu hình mặc định
./run_newman.sh

# Chạy với custom collection
./run_newman.sh --collection "my-tests.json" --port 8080

# Xem help
./run_newman.sh --help
```

## Tính năng

### Auto-Setup
- Tự động tạo sample collection nếu chưa có
- Tự động tạo environment file
- Tự động khởi động FastAPI server
- Tự động dọn dẹp processes khi kết thúc

### Test Reports
- HTML report cho UI
- JSON report cho CI/CD
- Console output với colors

### Error Handling
- Kiểm tra dependencies
- Timeout handling
- Graceful cleanup
- Exit codes cho CI/CD

## Sample Tests

Script tự động tạo sample collection với:

1. **Health Check** - Test endpoint `/`
2. **Agent Query** - Test endpoint `/agent` với payload mẫu

## Customization

### Collection Structure
```json
{
    "info": {
        "name": "AI Legal Assistant API Tests"
    },
    "item": [
        {
            "name": "Test Name",
            "request": {
                "method": "POST",
                "url": "{{base_url}}/endpoint",
                "body": {"raw": "..."}
            },
            "event": [
                {
                    "listen": "test",
                    "script": {
                        "exec": ["pm.test('...', function() { ... });"]
                    }
                }
            ]
        }
    ]
}
```

### Environment Variables
```json
{
    "values": [
        {
            "key": "base_url",
            "value": "http://localhost:8000",
            "enabled": true
        }
    ]
}
```

## CI/CD Integration

Script có thể được tích hợp vào GitHub Actions:

```yaml
- name: Run Newman Tests
  run: |
    npm install -g newman
    ./run_newman.sh --timeout 60
```

## Output

### Success
```
[INFO] Starting Newman API tests...
[SUCCESS] All tests passed!
[INFO] HTML report: newman-results/newman-report-20250117_143022.html
```

### Failure
```
[ERROR] Some tests failed (exit code: 1)
[INFO] Check reports for details:
[INFO] HTML report: newman-results/newman-report-20250117_143022.html
```

## Troubleshooting

### Newman not found
```bash
npm install -g newman
# hoặc sử dụng npx
npx newman --version
```

### Server không start
- Kiểm tra port có bị sử dụng không
- Kiểm tra uvicorn đã cài đặt chưa
- Kiểm tra app module path

### Tests fail
- Kiểm tra server có chạy không
- Xem HTML report để debug
- Kiểm tra API endpoints có hoạt động không

## Advanced Usage

### Custom timeout
```bash
./run_newman.sh --timeout 60
```

### Multiple environments
```bash
./run_newman.sh --environment "staging.json"
```

### Custom output directory
```bash
./run_newman.sh --output "test-results"
```
