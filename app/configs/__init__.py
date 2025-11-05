"""
Configuration package for the all logs.
"""

from .logger import get_logger, setup_logging, _logger_manager

__all__ = ["get_logger", "setup_logging", "_logger_manager"]