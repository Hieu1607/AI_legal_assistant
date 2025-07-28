import json
import os
import re
import sys

from bs4 import BeautifulSoup, Tag

root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, str(root))
from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

testing_file_path = "data/raw/law_metadata.json"
testing_file_path = os.path.join(root, testing_file_path)


def merge_isolated_letters(text):
    def replacer(match):
        group = match.group(0)
        return group.replace(" ", "")

    pattern = r"\b(?:[A-ZÀ-Ỹ]{1}\s){1,}[A-ZÀ-Ỹ]{1}\b"

    res = re.sub(pattern, replacer, text)
    return re.sub(r"\n{2,}", "\n", res).strip()


def parse_text_from_HTML(html_content):
    try:
        soup = BeautifulSoup(html_content, "html.parser")
        for div_to_remove in soup.find_all("div", class_="document-tip-r"):
            div_to_remove.decompose()
        target_div = soup.find("div", id="chidanthaydoind")
        if target_div is None:
            target_div = soup.find("div", class_="Section1")
        if target_div is None:
            target_div = soup.find("div", class_="noidungtracuu")
        result = ""
        if isinstance(target_div, Tag):
            for child in target_div.children:
                text = child.get_text(separator=" ", strip=True)
                cleaned_text = " ".join(text.split())
                result += cleaned_text + "\n"
            result = re.sub(r"\n{2,}", "\n", result)
            result = merge_isolated_letters(result)
        return result
    except (FileNotFoundError, KeyError, ValueError, TypeError, OSError) as e:
        logger.info("An error occurred: %s", e)
        return ""


def clean_metadata_file_to_text(file_path):
    try:
        # Tạo thư mục output nếu chưa tồn tại
        output_dir = os.path.join(root, "data", "processed", "new_texts")
        os.makedirs(output_dir, exist_ok=True)
        logger.info("Output directory ensured: %s", output_dir)

        with open(file_path, "r", encoding="utf-8") as f:
            datas = json.load(f)
            processed_count = 0
            skipped_count = 0

            for data in datas:
                text = parse_text_from_HTML(data["content"])
                logger.info("Parsed %s completely", data["title"])

                if text == "":
                    skipped_count += 1
                    logger.warning(
                        "Skipped %s - empty text content", data.get("law_id", "Unknown")
                    )
                    continue

                # Replace invalid filename characters with underscores
                new_file_name = (
                    data["law_id"]
                    .replace(" ", "_")
                    .replace("/", "_")
                    .replace("\\", "_")
                    .replace("-", "_")
                    + ".txt"
                )
                new_file_path = os.path.join(output_dir, new_file_name)

                try:
                    with open(new_file_path, "w", encoding="utf-8") as f:
                        if text is not None:
                            f.write(text)
                            processed_count += 1
                            logger.info("Saved text to: %s", new_file_name)
                except (OSError, IOError) as file_error:
                    logger.error(
                        "Failed to save file %s: %s", new_file_name, file_error
                    )

            logger.info(
                "Processing completed. Processed: %d, Skipped: %d",
                processed_count,
                skipped_count,
            )

    except (ValueError, TypeError, OSError) as e:
        logger.error("Error in cleaning data: %s", e)


if __name__ == "__main__":
    print(root)
