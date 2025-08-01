import json
import os
import sys


root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

sys.path.insert(0, str(root))
from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

from src.preprocess.chunker import make_chunks_from_metadata

path = os.path.join(root, "data", "raw", "new_law_metadata.json")
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)
    make_chunks_from_metadata(data)
