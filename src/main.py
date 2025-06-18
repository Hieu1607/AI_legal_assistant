# src/main.py

import logging.config
import os

import yaml

# Đảm bảo thư mục 'logs' tồn tại
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)


def setup_logging(config_path="configs/logging.yaml"):
    """
    Tải cấu hình logging từ file YAML.
    """
    try:
        with open(config_path, "rt", encoding="utf8") as f:
            config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
        # Test với root logger thay vì __name__
        test_logger = logging.getLogger("src")
        test_logger.info("Cấu hình logging đã được tải thành công.")
        print("DEBUG: Logging setup completed")  # Debug print
    except Exception as e:
        # Fallback to basic logging if configuration fails
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        logging.error("Không thể tải cấu hình logging từ '%s': %s", config_path, e)
        print(f"DEBUG: Logging setup failed: {e}")  # Debug print
        # Re-raise the exception if it's critical
        raise


if __name__ == "__main__":
    print("DEBUG: Starting main.py")  # Debug print
    setup_logging()

    # Sử dụng logger "src" thay vì __name__
    main_logger = logging.getLogger("src")
    main_logger.info("Ứng dụng đã khởi động thành công!")
    main_logger.warning("Đây là test warning message")
    main_logger.error("Đây là test error message")

    # Test với root logger
    root_logger = logging.getLogger()
    root_logger.info("Root logger test message")

    print("DEBUG: Main.py completed")  # Debug print
