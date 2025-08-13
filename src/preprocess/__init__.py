import os
import sys

# Get the root directory of the project
current_dir = os.path.dirname(os.path.abspath(__file__))
while True:
    # Check if 'data' and 'src' directories exist in current directory
    if os.path.isdir(os.path.join(current_dir, "data")) and os.path.isdir(
        os.path.join(current_dir, "src")
    ):
        root = current_dir
        break

    parent_dir = os.path.dirname(current_dir)
    if parent_dir == current_dir:  # Reached system root directory
        raise FileNotFoundError(
            "Check the project structure. 'data' and 'src' directories not found."
        )
    current_dir = parent_dir

sys.path.insert(0, str(root))

from .chunker import chunk_law_text
from .cleaner import clean_metadata_file_to_text
from .validator import validate_chunk_file
