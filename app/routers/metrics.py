"""
Router/Controller for metrics endpoint
"""

import os
import sys
from fastapi import APIRouter
from fastapi.responses import Response
from prometheus_client import generate_latest

# Set up logging
project_root = os.path.dirname(os.getcwd())
sys.path.insert(0, str(project_root))
from app.constants.http_status import HTTP_STATUS_OK
from app.logic.metrics_logic import get_metrics_data
from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

router = APIRouter()


@router.get("/metrics")
def get_metrics():
    """
    Endpoint to expose Prometheus metrics
    """
    try:
        logger.info("Metrics endpoint accessed")
        
        # Get metrics data
        metrics_data = get_metrics_data()
        
        # Generate Prometheus format
        metrics_output = generate_latest()
        
        return Response(
            content=metrics_output,
            media_type="text/plain; charset=utf-8",
            status_code=HTTP_STATUS_OK
        )
    except Exception as e:
        logger.error(f"Error retrieving metrics: {str(e)}")
        return Response(
            content=f"Error retrieving metrics: {str(e)}",
            media_type="text/plain; charset=utf-8",
            status_code=500
        )