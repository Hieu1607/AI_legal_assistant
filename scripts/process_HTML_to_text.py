import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, str(root))
from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

from src.preprocess.cleaner import clean_metadata_file_to_text

file_path = os.path.join(root, "data", "raw", "new_law_metadata.json")

clean_metadata_file_to_text(file_path)
