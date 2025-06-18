# configs/logger.py
"""
Simple centralized logging configuration for the AI Legal Assistant project.
"""

import logging
import logging.config
from pathlib import Path

import yaml


class LoggerManager:
    """Manages logging configuration for the application."""

    def __init__(self):
        self._setup_done = False

    def get_project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent

    def setup_logging(self, force_setup=False):
        """
        Setup logging configuration from YAML file.

        Args:
            force_setup: If True, force setup even if already done

        Returns:
            bool: True if successful, False otherwise
        """
        if self._setup_done and not force_setup:
            return True

        try:
            project_root = self.get_project_root()
            config_path = project_root / "configs" / "logging.yaml"
            logs_dir = project_root / "logs"

            # Create logs directory if it doesn't exist
            logs_dir.mkdir(exist_ok=True)

            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                logging.config.dictConfig(config)
            else:
                # Fallback to basic config
                logging.basicConfig(
                    level=logging.INFO,
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                )
                logging.warning("Logging config not found, using basic configuration")

            self._setup_done = True
            return True

        except (FileNotFoundError, yaml.YAMLError, KeyError) as e:
            logging.basicConfig(level=logging.ERROR)
            logging.error("Failed to setup logging: %s", e)
            return False

    def reset_logging(self):
        """Reset the setup flag for testing purposes."""
        self._setup_done = False


# Create a singleton instance
_logger_manager = LoggerManager()


def get_project_root():
    """Get the project root directory."""
    return _logger_manager.get_project_root()


def setup_logging(force_setup=False):
    """
    Setup logging configuration from YAML file.

    Args:
        force_setup: If True, force setup even if already done

    Returns:
        bool: True if successful, False otherwise
    """
    return _logger_manager.setup_logging(force_setup)


def get_logger(name):
    """Get a logger with the specified name."""
    return logging.getLogger(name)


def reset_logging():
    """Reset the setup flag for testing purposes."""
    return _logger_manager.reset_logging()


# Simple test
if __name__ == "__main__":
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Logger module working correctly")
