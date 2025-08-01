import json
import os
import sys

from playwright.sync_api import sync_playwright

testing_url = "https://luatvietnam.vn/lao-dong/bo-luat-lao-dong-2019-179015-d1.html"


root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))
from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def fetch_detail(file_path):
    final_result = []
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            datas = json.load(f)
            for index, data in enumerate(datas):
                url = data["link"]
                result = {}
                result["links"] = url
                result["date_of_issue"] = data["date_of_issue"]
                result["update_day"] = data["update_day"]
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=False)
                    page = browser.new_page()
                    page.goto(url)
                    page.wait_for_load_state("load")

                    # Get all HTML content
                    result["content"] = page.content()
                    title_element = page.locator("h1.the-document-title").text_content()
                    splitted_title = str(title_element).split(" ")
                    result["law_id"] = splitted_title[len(splitted_title) - 1]
                    browser.close()
                    result["title"] = title_element
                    final_result.append(result)
                logger.info("Successfully get the content of link %d", index + 1)
        logger.info("Successfully get all content")
        return final_result
    except (ValueError, TypeError, OSError) as e:
        logger.info("Error in fetching data : %s", e)
        return 0


if __name__ == "__main__":
    res = fetch_detail("data/raw/law_links.json")
    try:
        raw_path = os.path.join(root, "data", "raw")
        path = os.path.join(raw_path, "law_metadata.json")
        with open(path, "w", encoding="utf-8") as file:
            json.dump(res, file, ensure_ascii=False, indent=4)
    except (ValueError, TypeError, OSError) as e:
        logger.info("Error in saving data : %s", e)
