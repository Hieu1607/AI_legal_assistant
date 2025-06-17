import os
import sys

# Get the data raw path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
data_raw_path = os.path.join(project_root, "data", "raw")
all_html_files = os.listdir(data_raw_path)
files_in_data_raw = [f for f in all_html_files if f.endswith(".html")]

if project_root not in sys.path:
    sys.path.append(project_root)
try:
    from src.extract_data.extract_clean_text import process_legal_document

    for file in files_in_data_raw:
        print(f"Processing file: {file}")
        process_legal_document(os.path.join(data_raw_path, file))
    # process_legal_document(
    #     os.path.join(data_raw_path, "995b0a50-c2a1-45d8-baf6-a0b02c7821cf.html")
    # )
except ImportError as e:
    print(f"Error importing process_legal_document: {e}")
    print("Please ensure your project structure is correct and 'src' is importable.")
