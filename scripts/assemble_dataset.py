import json
import os
import sys


root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
