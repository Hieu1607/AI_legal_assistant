# Setup logging first
import os
import sys

# Ensure the project root is in the path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
config_path = os.path.join(project_root, "configs")

# Add paths to sys.path if not already present
if project_root not in sys.path:
    sys.path.append(project_root)
if os.path.dirname(config_path) not in sys.path:
    sys.path.append(os.path.dirname(config_path))

# Import after path setup
from configs.logger import get_logger, setup_logging

# Setup logging once
setup_logging()
logger = get_logger(__name__)

# Get the data raw path
data_raw_path = os.path.join(project_root, "data", "raw")
all_html_files = os.listdir(data_raw_path)
files_in_data_raw = [f for f in all_html_files if f.endswith(".html")]

try:
    from src.extract_data.extract_clean_text import process_legal_document

    logger.info("Starting batch processing of %d HTML files", len(files_in_data_raw))

    for file in files_in_data_raw:
        logger.info("Processing file: %s", file)
        process_legal_document(os.path.join(data_raw_path, file))

    logger.info("Batch processing completed successfully")

except ImportError as e:
    logger.error("Error importing process_legal_document: %s", e)
    logger.error(
        "Please ensure your project structure is correct and 'src' is importable."
    )
    print(f"Error importing process_legal_document: {e}")
    print("Please ensure your project structure is correct and 'src' is importable.")
