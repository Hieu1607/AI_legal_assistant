import json
import os
import sys


def get_project_root():
    """Get the root directory of the project."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while True:
        # Kiểm tra xem 'data' và 'src' có tồn tại trong thư mục hiện tại không
        if os.path.isdir(os.path.join(current_dir, "data")) and os.path.isdir(
            os.path.join(current_dir, "src")
        ):
            return current_dir

        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Đã đến thư mục gốc của hệ thống
            raise FileNotFoundError(
                "Check the project structure. 'data' and 'src' directories not found."
            )
        current_dir = parent_dir


root = get_project_root()
sys.path.insert(0, str(root))
from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

from src.retrieval.fetch_details import fetch_detail

file_path = "data/raw/law_links.json"
# file_path = "data/raw/law_links_from_head_page.json"
try:
    res = fetch_detail(file_path)
    raw_path = os.path.join(root, "data", "raw")
    path = os.path.join(raw_path, "law_metadata.json")
    # path = os.path.join(raw_path, "law_metadata_from_head_page.json")
    with open(path, "w", encoding="utf-8") as file:
        json.dump(res, file, ensure_ascii=False, indent=4)
except (ValueError, TypeError, OSError) as e:
    logger.info("Error in saving data : %s", e)
