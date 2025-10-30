# configs/logger.py
"""
Simple centralized logging configuration for the AI Legal Assistant project.
"""

import logging
import logging.config
from logging.handlers import RotatingFileHandler
from pathlib import Path

import yaml


class LoggerManager:
    """Manages logging configuration for the application."""

    def __init__(self):
        self._setup_done = False

    def get_project_root(self):
        """Get the project root directory."""
        return Path(__file__).parent.parent

    def _update_handler_paths(self, config, project_root):
        """Update file handler paths to use absolute paths."""
        if "handlers" in config:
            for handler_name, handler_config in config["handlers"].items():
                if "filename" in handler_config:
                    # Convert relative path to absolute path from project root
                    filename = handler_config["filename"]
                    if not Path(filename).is_absolute():
                        handler_config["filename"] = str(project_root / filename)

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

                # Update file handler paths to use absolute paths
                self._update_handler_paths(config, project_root)
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


_APP_LOG_HANDLER = None
_APP_LOG_PATH = None


def get_logger_app(name="app"):
    """
    Get a logger specifically configured to write to app.log.

    This function creates a logger with the given name and adds a
    RotatingFileHandler that writes to logs/app.log. It ensures that
    only one handler is added to prevent duplicate logs.

    Args:
        name: The name of the logger. Defaults to "app".

    Returns:
        logging.Logger: A configured logger that writes to app.log
    """
    setup_logging()

    # pylint: disable=global-statement
    global _APP_LOG_HANDLER, _APP_LOG_PATH

    if _APP_LOG_HANDLER is None:
        logs_dir = get_project_root() / "logs"
        logs_dir.mkdir(exist_ok=True)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        app_log_path = str(logs_dir / "app.log")
        handler = RotatingFileHandler(
            filename=app_log_path,
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding="utf8",
        )

        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)

        _APP_LOG_HANDLER = handler
        _APP_LOG_PATH = app_log_path

    # Get the logger with the specified name
    logger = logging.getLogger(name)

    logger.propagate = False

    if not logger.level:
        logger.setLevel(logging.INFO)

    app_handler_exists = any(
        isinstance(handler, logging.FileHandler)
        and getattr(handler, "baseFilename", "") == _APP_LOG_PATH
        for handler in logger.handlers
    )

    if not app_handler_exists:
        logger.addHandler(_APP_LOG_HANDLER)

    return logger


def reset_logging():
    """Reset the setup flag for testing purposes."""
    return _logger_manager.reset_logging()


# Simple test
if __name__ == "__main__":
    setup_logging()

    # Regular logger (writes to info.log)
    current_logger = get_logger(__name__)
    current_logger.info("Logger module working correctly")

    # App logger (writes to app.log)
    app_logger = get_logger_app()
    app_logger.info("App logger working correctly - check logs/app.log")
