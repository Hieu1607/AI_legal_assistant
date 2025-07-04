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
