# Prometheus Setup for AI Legal Assistant

This directory contains the configuration files needed to run Prometheus for monitoring the AI Legal Assistant application.

## Files

- `Dockerfile`: Docker configuration for Prometheus
- `prometheus.yml`: Prometheus configuration file
- `docker-compose.yml`: Docker Compose file for easy deployment
- `README.md`: This documentation file

## Quick Start

### Option 1: Using Docker Compose (Recommended)

```bash
cd prometheus
docker-compose up -d
```

### Option 2: Using Docker directly

```bash
cd prometheus
docker build -t ai-legal-prometheus .
docker run -d -p 9090:9090 --name prometheus ai-legal-prometheus
```

## Configuration

### Targets

The Prometheus configuration is set to scrape metrics from:

1. **Prometheus itself**: `localhost:9090`
2. **AI Legal Assistant**: `host.docker.internal:8000/metrics`

### Scrape Intervals

- Default: 15 seconds
- AI Legal Assistant: 30 seconds

## Accessing Prometheus

Once running, you can access:

- **Prometheus Web UI**: http://localhost:9090
- **AI Legal Assistant Metrics**: http://localhost:8000/metrics

## Available Metrics

The AI Legal Assistant exposes the following metrics:

- `http_requests_total`: Total HTTP requests with labels for method, endpoint, and status code
- `request_latency_seconds`: Request latency histogram with method and endpoint labels  
- `gemini_tokens_total`: Total tokens used in Gemini API with type labels

## CORS Configuration

The AI Legal Assistant has been configured to allow CORS requests from:

- Prometheus server (localhost:9090)
- Any origin for the `/metrics` endpoint specifically

## Troubleshooting

### Connection Issues

If Prometheus can't reach the AI Legal Assistant:

1. Make sure the AI Legal Assistant is running on port 8000
2. Check if `host.docker.internal` resolves correctly
3. For Linux, you might need to use `172.17.0.1:8000` instead

### Docker Network Issues

If using a custom Docker network, update the target in `prometheus.yml` accordingly.

## Customization

To modify the scraping configuration:

1. Edit `prometheus.yml`
2. Rebuild the Docker image or restart the container
3. Or use the reload API: `curl -X POST http://localhost:9090/-/reload`