"""
Configuration package for the all logs.
"""

from .logger import _logger_manager, get_logger, setup_logging
from .settings import settings

__all__ = ["get_logger", "setup_logging", "_logger_manager", "settings"]
