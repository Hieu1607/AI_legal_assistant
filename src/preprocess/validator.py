import os
import sys


root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))
from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def validate_chunk_file(chunks):
    check = 1
    for numth, chunk in enumerate(chunks):
        if chunk["chunk_id"] is None:
            logger.info("Found chunk %d without chunk_id", numth + 1)
            check = 0
        if chunk["text"] is None:
            logger.info("Found chunk %d without text", numth + 1)
            check = 0
    return check


if __name__ == "__main__":
    print("Im too lazy to write the main now")
