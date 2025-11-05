"""
Metrics collection và monitoring logic với Prometheus
"""

import time

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

from app.configs.logger import get_logger

logger = get_logger(__name__)


class MetricsCollector:
    """Prometheus metrics collector cho ứng dụng AI Legal Assistant"""

    def __init__(self):
        """Initialize Prometheus metrics"""
        self.start_time = time.time()

        # Prometheus metrics
        self.http_requests_total = Counter(
            "http_requests_total",
            "Tổng số HTTP requests",
            ["method", "endpoint", "status_code"],
        )

        self.http_request_duration_seconds = Histogram(
            "http_request_duration_seconds",
            "Thời gian xử lý HTTP requests",
            ["method", "endpoint"],
            buckets=(
                0.005,
                0.01,
                0.025,
                0.05,
                0.075,
                0.1,
                0.25,
                0.5,
                0.75,
                1.0,
                2.5,
                5.0,
                7.5,
                10.0,
            ),
        )

        self.application_uptime_seconds = Gauge(
            "application_uptime_seconds", "Thời gian uptime của ứng dụng tính bằng giây"
        )

        self.http_errors_total = Counter(
            "http_errors_total",
            "Tổng số HTTP errors",
            ["method", "endpoint", "status_code"],
        )

    def record_request(
        self, endpoint: str, status_code: int, latency_ms: float, method: str = "GET"
    ):
        """
        Record a request metric.

        Args:
            endpoint (str): API endpoint path
            status_code (int): HTTP status code
            latency_ms (float): Request latency in milliseconds
            method (str): HTTP method
        """
        # Update Prometheus metrics
        self.http_requests_total.labels(
            method=method, endpoint=endpoint, status_code=str(status_code)
        ).inc()

        self.http_request_duration_seconds.labels(
            method=method, endpoint=endpoint
        ).observe(
            latency_ms / 1000.0
        )  # Convert to seconds

        # Record errors
        if status_code >= 400:
            self.http_errors_total.labels(
                method=method, endpoint=endpoint, status_code=str(status_code)
            ).inc()

        # Update uptime
        self.application_uptime_seconds.set(time.time() - self.start_time)

        logger.debug(
            "Request recorded - Endpoint: %s, Status: %d, Latency: %.2fms",
            endpoint,
            status_code,
            latency_ms,
        )

    def get_prometheus_metrics(self) -> str:
        """
        Get metrics in Prometheus format.

        Returns:
            str: Metrics in Prometheus exposition format
        """
        # Update uptime before generating metrics
        self.application_uptime_seconds.set(time.time() - self.start_time)

        return generate_latest().decode("utf-8")

    def get_prometheus_content_type(self) -> str:
        """
        Get the content type for Prometheus metrics.

        Returns:
            str: Content type for Prometheus format
        """
        return CONTENT_TYPE_LATEST
