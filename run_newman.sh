#!/bin/bash

# Script to run Newman API tests for AI Legal Assistant
# Usage: ./run_newman.sh [collection_file] [environment_file]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
COLLECTION_FILE="postman/ai-legal-assistant.json"
ENVIRONMENT_FILE="postman/environment.json"
OUTPUT_DIR="newman-results"
HOST="localhost"
PORT="8000"
APP_MODULE="app.main:app"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to cleanup background processes
cleanup() {
    print_info "Cleaning up background processes..."
    pkill -f "uvicorn.*$APP_MODULE" || true
    sleep 2
}

# Set trap to cleanup on script exit
trap cleanup EXIT

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--collection)
            COLLECTION_FILE="$2"
            shift 2
            ;;
        -e|--environment)
            ENVIRONMENT_FILE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -h|--host)
            HOST="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -c, --collection FILE    Postman collection file (default: $COLLECTION_FILE)"
            echo "  -e, --environment FILE   Environment file (default: $ENVIRONMENT_FILE)"
            echo "  -o, --output DIR         Output directory (default: $OUTPUT_DIR)"
            echo "  -h, --host HOST          API host (default: $HOST)"
            echo "  -p, --port PORT          API port (default: $PORT)"
            echo "  --help                   Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

print_info "Starting Newman API tests for AI Legal Assistant"
print_info "Collection: $COLLECTION_FILE"
print_info "Environment: $ENVIRONMENT_FILE"
print_info "Output directory: $OUTPUT_DIR"
print_info "API URL: http://$HOST:$PORT"

# Check dependencies
print_info "Checking dependencies..."

if ! command_exists newman; then
    if command_exists npx; then
        print_warning "Newman not found globally, will use npx"
        NEWMAN_CMD="npx newman"
    else
        print_error "Newman not found. Please install with: npm install -g newman"
        exit 1
    fi
else
    NEWMAN_CMD="newman"
fi

if ! command_exists python; then
    print_error "Python not found. Please install Python"
    exit 1
fi

if ! command_exists uvicorn; then
    print_error "Uvicorn not found. Please install with: pip install uvicorn"
    exit 1
fi

# Check if collection file exists
if [[ ! -f "$COLLECTION_FILE" ]]; then
    print_warning "Collection file not found: $COLLECTION_FILE"
    print_info "Creating sample collection file..."

    mkdir -p "$(dirname "$COLLECTION_FILE")"
    cat > "$COLLECTION_FILE" << 'EOF'
{
    "info": {
        "name": "AI Legal Assistant API Tests",
        "description": "Sample collection for AI Legal Assistant API",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [
        {
            "name": "Health Check",
            "request": {
                "method": "GET",
                "header": [],
                "url": {
                    "raw": "{{base_url}}/",
                    "host": ["{{base_url}}"],
                    "path": [""]
                }
            },
            "event": [
                {
                    "listen": "test",
                    "script": {
                        "exec": [
                            "pm.test('Status code is 200', function () {",
                            "    pm.response.to.have.status(200);",
                            "});"
                        ],
                        "type": "text/javascript"
                    }
                }
            ]
        },
        {
            "name": "Agent Query",
            "request": {
                "method": "POST",
                "header": [
                    {
                        "key": "Content-Type",
                        "value": "application/json"
                    }
                ],
                "body": {
                    "mode": "raw",
                    "raw": "{\n    \"question\": \"Chương II điều 29 bộ luật hàng hải nói gì?\",\n    \"top_k\": 5,\n    \"total_steps\": 1,\n    \"timeout_sec\": 20\n}"
                },
                "url": {
                    "raw": "{{base_url}}/agent",
                    "host": ["{{base_url}}"],
                    "path": ["agent"]
                }
            },
            "event": [
                {
                    "listen": "test",
                    "script": {
                        "exec": [
                            "pm.test('Status code is 200', function () {",
                            "    pm.response.to.have.status(200);",
                            "});",
                            "",
                            "pm.test('Response has required fields', function () {",
                            "    const responseJson = pm.response.json();",
                            "    pm.expect(responseJson).to.have.property('success');",
                            "    pm.expect(responseJson).to.have.property('status_code');",
                            "    pm.expect(responseJson).to.have.property('step_completed');",
                            "    pm.expect(responseJson).to.have.property('data');",
                            "    pm.expect(responseJson).to.have.property('message');",
                            "    pm.expect(responseJson).to.have.property('execution_time');",
                            "});"
                        ],
                        "type": "text/javascript"
                    }
                }
            ]
        }
    ]
}
EOF
    print_success "Sample collection created at: $COLLECTION_FILE"
fi

# Check if environment file exists, create if not
if [[ ! -f "$ENVIRONMENT_FILE" ]]; then
    print_info "Creating environment file..."
    mkdir -p "$(dirname "$ENVIRONMENT_FILE")"
    cat > "$ENVIRONMENT_FILE" << EOF
{
    "id": "$(uuidgen 2>/dev/null || echo 'environment-id')",
    "name": "AI Legal Assistant Environment",
    "values": [
        {
            "key": "base_url",
            "value": "http://$HOST:$PORT",
            "enabled": true
        }
    ]
}
EOF
    print_success "Environment file created at: $ENVIRONMENT_FILE"
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Start FastAPI server
print_info "Starting FastAPI server..."
uvicorn "$APP_MODULE" --host "$HOST" --port "$PORT" --reload &
SERVER_PID=$!

# Wait for server to start
print_info "Waiting for server to start..."
sleep 5

# Check if server is running
if ! curl -s "http://$HOST:$PORT/" > /dev/null; then
    print_error "Server failed to start or is not responding"
    exit 1
fi

print_success "Server is running at http://$HOST:$PORT"

# Run Newman tests
print_info "Running Newman tests..."

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
HTML_REPORT="$OUTPUT_DIR/newman-report-$TIMESTAMP.html"
JSON_REPORT="$OUTPUT_DIR/newman-report-$TIMESTAMP.json"

$NEWMAN_CMD run "$COLLECTION_FILE" \
    --environment "$ENVIRONMENT_FILE" \
    --reporters html,json,cli \
    --reporter-html-export "$HTML_REPORT" \
    --reporter-json-export "$JSON_REPORT" \
    --timeout-request 30000 \
    --bail \
    --color on

NEWMAN_EXIT_CODE=$?

if [[ $NEWMAN_EXIT_CODE -eq 0 ]]; then
    print_success "All tests passed!"
    print_info "HTML report: $HTML_REPORT"
    print_info "JSON report: $JSON_REPORT"
else
    print_error "Some tests failed (exit code: $NEWMAN_EXIT_CODE)"
    print_info "Check reports for details:"
    print_info "HTML report: $HTML_REPORT"
    print_info "JSON report: $JSON_REPORT"
fi

print_info "Newman tests completed"
exit $NEWMAN_EXIT_CODE
