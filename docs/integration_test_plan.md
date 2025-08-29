# Integration Test Plan

This document outlines the integration test cases for the AI Legal Assistant API to validate end-to-end functionality across all endpoints.

## Test Environment
- **Base URL**: `http://localhost:8000`
- **Prerequisites**: 
  - Vector database with legal documents
  - Gemini API key configured
  - BGE-M3 model available locally

## Test Cases

### 1. Normal Legal Query with Citations
**Endpoint**: `POST /rag`

**Input**:
```json
{
  "question": "Quy định về hợp đồng lao động là gì?"
}
```

**Expected Output**:
- Status: 200 OK
- Response format:
```json
{
  "status": "success",
  "data": {
    "answer": "Theo chương 3 điều 15 bộ luật lao động 2019, hợp đồng lao động là...",
    "question": "Quy định về hợp đồng lao động là gì?",
    "context_count": 5
  }
}
```

**Test Steps**:
1. Send POST request to `/rag` with legal question
2. Verify response contains proper citations with "Theo chương...điều...bộ luật..." format
3. Verify context_count > 0
4. Verify response time < 10 seconds

---

### 2. LLM Timeout with Fallback Response
**Endpoint**: `POST /rag`

**Input**:
```json
{
  "question": "Quy định về thuế thu nhập cá nhân?"
}
```

**Expected Output** (when timeout occurs):
- Status: 200 OK
- Response format:
```json
{
  "status": "success", 
  "data": {
    "answer": "The system is busy now. Please try again.",
    "question": "Quy định về thuế thu nhập cá nhân?",
    "context_count": 5
  }
}
```

**Test Steps**:
1. Configure shorter timeout (simulate overload)
2. Send request with complex legal question
3. Verify fallback message when timeout occurs
4. Verify status remains 200 with graceful degradation

---

### 3. Agent Processing Error
**Endpoint**: `POST /agent`

**Input**:
```json
{
  "question": "Test invalid processing",
  "top_k": 5,
  "total_steps": 3,
  "timeout_sec": 30
}
```

**Expected Output**:
- Status: 500 Internal Server Error
- Response format:
```json
{
  "success": false,
  "status_code": 500,
  "step_completed": 1,
  "data": null,
  "message": "Internal server error during processing",
  "execution_time": 2.5
}
```

**Test Steps**:
1. Trigger internal error (corrupt database/model failure)
2. Verify proper error status code
3. Verify error logging is captured
4. Verify partial completion information is returned

---

### 4. No Matching Documents Found
**Endpoint**: `POST /retrieve`

**Input**:
```json
{
  "question": "quantum physics regulations in Vietnam",
  "top_k": 5
}
```

**Expected Output**:
- Status: 200 OK
- Response: `[]` (empty array)

**Test Steps**:
1. Send query for topic not in legal database
2. Verify empty array response
3. Verify status code is still 200 (valid request, no results)
4. Verify no error messages in logs

---

### 5. Agent Timeout at Different Steps
**Endpoint**: `POST /agent`

**Input**:
```json
{
  "question": "Chương II điều 29 bộ luật hàng hải nói gì?",
  "top_k": 3,
  "total_steps": 2,
  "timeout_sec": 5
}
```

**Expected Output** (Step 1 timeout):
- Status: 408 Request Timeout
- Response format:
```json
{
  "success": false,
  "status_code": 408,
  "step_completed": 0,
  "data": null,
  "message": "Step 1 (retrieve chunks) timed out after 5s",
  "execution_time": 5.0
}
```

**Test Steps**:
1. Set very short timeout (5 seconds)
2. Send request requiring multiple processing steps
3. Verify timeout handling at each step
4. Verify partial results returned when possible

---

### 6. Input Validation Errors
**Endpoint**: `POST /agent`

**Input**:
```json
{
  "question": "Hi",
  "top_k": 25,
  "total_steps": 5,
  "timeout_sec": 400
}
```

**Expected Output**:
- Status: 422 Unprocessable Entity
- Response format:
```json
{
  "error": {
    "type": "validation_error",
    "message": "Input data is not valid",
    "fields": [
      {"field": "question", "error": "ensure this value has at least 10 characters"},
      {"field": "top_k", "error": "ensure this value is less than or equal to 20"},
      {"field": "total_steps", "error": "ensure this value is less than or equal to 3"},
      {"field": "timeout_sec", "error": "ensure this value is less than or equal to 300"}
    ]
  }
}
```

**Test Steps**:
1. Send request with invalid parameters
2. Verify validation error response format
3. Verify all validation rules are enforced
4. Verify detailed field-level error messages

---

### 7. Health Check System Status
**Endpoint**: `GET /health`

**Expected Output** (Healthy):
- Status: 200 OK
- Response format:
```json
{
  "service": "AI Legal Assistant",
  "status": "healthy",
  "services": {
    "bge_m3_model": {
      "status": "healthy",
      "message": "Model files available locally"
    },
    "chroma_db": {"status": "healthy"},
    "gemini_api": {
      "status": "healthy", 
      "message": "API responding correctly"
    }
  }
}
```

**Expected Output** (Unhealthy):
- Status: 500 Internal Server Error
- Response format:
```json
{
  "service": "AI Legal Assistant",
  "status": "unhealthy",
  "error": "ChromaDB error: Connection failed"
}
```

**Test Steps**:
1. Verify health check when all services are available
2. Test with disabled/unavailable services (ChromaDB, Gemini API)
3. Verify proper error reporting for each service
4. Verify status codes match service health

## Test Execution Guidelines

### Automated Testing
- Run tests in sequence to avoid resource conflicts
- Use test database for consistent results
- Mock external API calls when testing error scenarios

### Performance Validation
- Monitor response times for each endpoint
- Verify timeout handling works as specified
- Check memory usage during concurrent requests

### Error Logging Verification
- Confirm all errors are properly logged
- Verify sensitive information is not exposed
- Check log levels are appropriate for each scenario
