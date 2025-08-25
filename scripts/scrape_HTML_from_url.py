import json
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
