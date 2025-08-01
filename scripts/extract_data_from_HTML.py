# Setup logging first
import os
import sys


root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if root not in sys.path:
    sys.path.insert(0, root)

# Now we can import modules
from configs.logger import get_logger, setup_logging
from src.extract_data.extract_clean_text import process_legal_document

# Setup logging once
setup_logging()
logger = get_logger(__name__)

# Get the data raw path
data_raw_path = os.path.join(root, "data", "raw", "bophapdien")
all_html_files = os.listdir(data_raw_path)
files_in_data_raw = [f for f in all_html_files if f.endswith(".html")]

try:

    logger.info("Starting batch processing of %d HTML files", len(files_in_data_raw))

    for file in files_in_data_raw:
        logger.info("Processing file: %s", file)
        process_legal_document(os.path.join(data_raw_path, file))

    logger.info("Batch processing completed successfully")

except ImportError as e:
    logger.error("Error importing process_legal_document: %s", e)
    print(f"Error importing process_legal_document: {e}")
