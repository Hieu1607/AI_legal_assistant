"""
Router for metrics endpoints - Prometheus format only
"""

import os
import sys

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

# Add project root to path
root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))

from app.services.metric_service import MetricsCollector
from configs.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Global metrics collector instance
metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector instance"""
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
