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


# Singleton handler cho app.log
_APP_LOG_HANDLER = None
_APP_LOG_PATH = None

# Singleton handler cho agent.log
_AGENT_LOG_HANDLER = None
_AGENT_LOG_PATH = None


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
    # First make sure basic logging is set up
    setup_logging()

    # pylint: disable=global-statement
    global _APP_LOG_HANDLER, _APP_LOG_PATH

    # Tạo một singleton app handler cho toàn bộ ứng dụng nếu chưa tồn tại
    if _APP_LOG_HANDLER is None:
        # Tạo logs directory nếu chưa tồn tại
        logs_dir = get_project_root() / "logs"
        logs_dir.mkdir(exist_ok=True)

        # Tạo một formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Tạo một rotating file handler cho app.log
        app_log_path = str(logs_dir / "app.log")
        handler = RotatingFileHandler(
            filename=app_log_path,
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding="utf8",
        )

        # Thiết lập level và formatter
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)

        # Lưu trữ handler như một singleton
        _APP_LOG_HANDLER = handler
        _APP_LOG_PATH = app_log_path

    # Get the logger with the specified name
    logger = logging.getLogger(name)

    # Đặt propagate=False để tránh log bị duplicate khi truyền lên root logger
    logger.propagate = False

    # Đảm bảo logger có ít nhất một level, mặc định là INFO
    if not logger.level:
        logger.setLevel(logging.INFO)

    # Kiểm tra xem logger này đã có app handler chưa
    # bằng cách kiểm tra baseFilename của tất cả các handlers
    app_handler_exists = any(
        isinstance(handler, logging.FileHandler)
        and getattr(handler, "baseFilename", "") == _APP_LOG_PATH
        for handler in logger.handlers
    )

    # Thêm handler nếu chưa có
    if not app_handler_exists:
        logger.addHandler(_APP_LOG_HANDLER)

    return logger


def get_logger_agent(name="agent"):
    """
    Get a logger specifically configured to write to agent.log.

    This function creates a logger with the given name and adds a
    RotatingFileHandler that writes to logs/agent.log. It ensures that
    only one handler is added to prevent duplicate logs.

    Args:
        name: The name of the logger. Defaults to "agent".

    Returns:
        logging.Logger: A configured logger that writes to agent.log
    """
    # First make sure basic logging is set up
    setup_logging()

    # pylint: disable=global-statement
    global _AGENT_LOG_HANDLER, _AGENT_LOG_PATH

    # Tạo một singleton agent handler cho toàn bộ ứng dụng nếu chưa tồn tại
    if _AGENT_LOG_HANDLER is None:
        # Tạo logs directory nếu chưa tồn tại
        logs_dir = get_project_root() / "logs"
        logs_dir.mkdir(exist_ok=True)

        # Tạo một formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Tạo một rotating file handler cho agent.log
        agent_log_path = str(logs_dir / "agent.log")
        handler = RotatingFileHandler(
            filename=agent_log_path,
            maxBytes=10485760,  # 10MB
            backupCount=5,
            encoding="utf8",
        )

        # Thiết lập level và formatter
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)

        # Lưu trữ handler như một singleton
        _AGENT_LOG_HANDLER = handler
        _AGENT_LOG_PATH = agent_log_path

    # Get the logger with the specified name
    logger = logging.getLogger(name)

    # Đặt propagate=False để tránh log bị duplicate khi truyền lên root logger
    logger.propagate = False

    # Đảm bảo logger có ít nhất một level, mặc định là INFO
    if not logger.level:
        logger.setLevel(logging.INFO)

    # Kiểm tra xem logger này đã có agent handler chưa
    # bằng cách kiểm tra baseFilename của tất cả các handlers
    agent_handler_exists = any(
        isinstance(handler, logging.FileHandler)
        and getattr(handler, "baseFilename", "") == _AGENT_LOG_PATH
        for handler in logger.handlers
    )

    # Thêm handler nếu chưa có
    if not agent_handler_exists:
        logger.addHandler(_AGENT_LOG_HANDLER)

    return logger


def reset_logging():
    """Reset the setup flag for testing purposes."""
    return _logger_manager.reset_logging()


# Simple test
if __name__ == "__main__":
    setup_logging()

    # Regular logger (writes to info.log)
    logger = get_logger(__name__)
    logger.info("Logger module working correctly")

    # App logger (writes to app.log)
    app_logger = get_logger_app()
    app_logger.info("App logger working correctly - check logs/app.log")

    # Agent logger (writes to agent.log)
    agent_logger = get_logger_agent()
    agent_logger.info("Agent logger working correctly - check logs/agent.log")

    # Agent logger (writes to agent.log)
    agent_logger = get_logger_agent()
    agent_logger.info("Agent logger working correctly - check logs/agent.log")
