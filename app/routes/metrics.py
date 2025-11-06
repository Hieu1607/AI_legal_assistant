"""
Router for metrics endpoints - Prometheus format only
"""
from functools import lru_cache
from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.configs.logger import get_logger

from app.services.metric_service import MetricsCollector

logger = get_logger(__name__)

router = APIRouter()

# Global metrics collector instance
@lru_cache(maxsize=1)
def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance"""
    metrics_collector = MetricsCollector()
    return metrics_collector

@router.get("/metrics")
def get_metrics():
    """
    Get application metrics in Prometheus format.

    Returns metrics in Prometheus exposition format:
    tên_metric{nhãn="giá_trị"} giá_trị_số thời_gian
    """
    collector = get_metrics_collector()
    prometheus_metrics = collector.get_prometheus_metrics()
    content_type = collector.get_prometheus_content_type()

    logger.info("Metrics endpoint accessed (Prometheus format)")

    return PlainTextResponse(content=prometheus_metrics, media_type=content_type)
