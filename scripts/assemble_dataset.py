import json
import os
import sys


# Define get_project_root locally to avoid circular import issues
def get_project_root():
    """Get the root directory of the project."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while True:
        if os.path.isdir(os.path.join(current_dir, "data")) and os.path.isdir(
            os.path.join(current_dir, "src")
        ):
            return current_dir
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            raise FileNotFoundError(
                "Check the project structure. 'data' and 'src' directories not found."
            )
        current_dir = parent_dir


# Set up paths
root = get_project_root()
if root not in sys.path:
    sys.path.insert(0, root)

# Now we can import modules
from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

folder_path = "data/processed/chunks"
all_chunks = []

for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)

    if os.path.isfile(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            chunks_in_file = json.load(f)
            for chunk in chunks_in_file:
                all_chunks.append(chunk)

new_file_path = "data/processed/all_chunks.json"
with open(new_file_path, "w", encoding="utf-8") as f:
    json.dump(all_chunks, f, ensure_ascii=False, indent=4)
print(len(all_chunks))  # 27061
