import json
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, str(root))

from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

from src.preprocess.validator import validate_chunk_file

folder_path = "data/processed/chunks"

for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)

    if os.path.isfile(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
            flag = validate_chunk_file(chunks)
            if flag:
                logger.info("%s is clear", file_path)
