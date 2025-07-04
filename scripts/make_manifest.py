import csv
import html
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
dir_path = "data/raw"
file_name = "test.json"
file_path = os.path.join(dir_path, file_name)
new_file_name = file_name.replace(".json", ".csv")
new_file_path = os.path.join(dir_path, new_file_name)
data = {}
with open(file_path, "r", encoding="utf-8") as file:
    data = json.load(file)

for law in data:
    for k, v in law.items():
        if isinstance(v, str):
            law[k] = html.unescape(v)

csv_headers = list(data[0].keys())

with open(new_file_path, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=csv_headers, quoting=csv.QUOTE_MINIMAL)

    writer.writeheader()  # Ghi tiêu đề cột

    for row in data:
        writer.writerow(row)
print(f"Đã ghi thành công vào '{new_file_path}'.")
