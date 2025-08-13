# configs/logger.py
"""
Simple centralized logging configuration for the AI Legal Assistant project.
"""

import logging
import logging.config
import os

import yaml


class LoggerManager:
    """Manages logging configuration for the application."""

    def __init__(self):
        self._setup_done = False

    def get_project_root(self):
        """Get the project root directory."""
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def _update_handler_paths(self, config, project_root):
        """Update file handler paths to use absolute paths."""
        if "handlers" in config:
            for handler_name, handler_config in config["handlers"].items():
                if "filename" in handler_config:
                    # Convert relative path to absolute path from project root
                    filename = handler_config["filename"]
                    if not os.path.isabs(filename):
                        handler_config["filename"] = os.path.join(
                            project_root, filename
                        )

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
            config_path = os.path.join(project_root, "configs", "logging.yaml")
            logs_dir = os.path.join(project_root, "logs")

            # Create logs directory if it doesn't exist
            os.makedirs(logs_dir, exist_ok=True)

            if os.path.exists(config_path):
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
