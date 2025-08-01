import csv
import html
import json
import os
import sys

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
