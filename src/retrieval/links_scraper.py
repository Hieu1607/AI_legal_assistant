import json
import os
import random
import sys
import time

import requests
from bs4 import BeautifulSoup

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))

from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def get_the_HTML_page(url):
    """
    Get the HTML source code
    params :
        - url : The url to the web page
    """

    # Configure session with headers to mimic a real browser
    session = requests.Session()
    soup = ""
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0",
        }
    )

    try:
        time.sleep(random.uniform(1, 3))
        response = session.get(url, timeout=20)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            logger.info("Successfully scraped the page!")
        else:
            logger.info("Request failed with status code: %s", response.status_code)
    except requests.exceptions.RequestException as e:
        logger.info("Request error: %s", e)
    except (ValueError, TypeError, OSError) as e:
        logger.info("Other error: %s", e)
    if soup:
        return soup
    logger.info("Can't find anything")
    return None


def find_all_links(soup):
    """
    Find all links in the soup page
    """
    all_links_in_h2 = soup.select("h2.doc-title a")
    # Uncommend this for the main link (14 links)
    # all_links_in_h3 = soup.select("h3.doc-title a")
    result = []
    for a in all_links_in_h2:
        link = a.get("href")
        link = "https://luatvietnam.vn" + link
        if a:
            result.append(link)
        else:
            logger.info("Can't find the link in current container")
    # for a in all_links_in_h3:
    #     link = a.get("href")
    #     link = "https://luatvietnam.vn" + link
    #     if a:
    #         result.append(link)
    #     else:
    #         logger.info("Can't find the link in current container")
    logger.info("Total links : %d", len(result))
    # print("Result: ", result)
    return result


def find_all_metadata(soup):
    all_divs = soup.select("div.doc-dmy")
    issue_days_list = []
    update_days_list = []
    for i in range(0, len(all_divs), 4):
        span = all_divs[i].find_all()[1].get_text()
        issue_days_list.append(span)
    for i in range(3, len(all_divs), 4):
        span = all_divs[i].find_all()[1].get_text()
        update_days_list.append(span)
    return issue_days_list, update_days_list


def concatenate_2_type_of_data(links, issue_days_list, update_day_list):
    result = []
    logger.info(
        "Number of links is %d",
        len(links),
    )
    logger.info(
        "Number of issue_days_list is %d",
        len(issue_days_list),
    )
    logger.info(
        "Number of update_day_list is %d",
        len(update_day_list),
    )

    for i, link in enumerate(links):
        current_result = {}
        current_result["link"] = link
        current_result["date_of_issue"] = issue_days_list[i]
        current_result["update_day"] = update_day_list[i]
        result.append(current_result)
    return result


def save_to_data(result, file_name):
    """
    Save the data just crawl to json file (append if file exists)
    params:
        - result: All links
        - file_name: Name of the file (json)
    """
    try:
        # file_name = "law_links.json"
        raw_path = os.path.join(root, "data", "raw")
        file_path = os.path.join(raw_path, file_name)

        # Tạo thư mục nếu chưa tồn tại
        os.makedirs(raw_path, exist_ok=True)

        existing_data = []

        # Đọc data cũ nếu file đã tồn tại
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                logger.info(
                    "Loaded %d existing records from %s", len(existing_data), file_name
                )
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(
                    "Failed to read existing file %s: %s. Starting with empty data.",
                    file_name,
                    e,
                )
                existing_data = []

        # Lọc bỏ các link trùng lặp (nếu có)
        existing_links = {
            item.get("link")
            for item in existing_data
            if isinstance(item, dict) and "link" in item
        }
        new_data = [
            item
            for item in result
            if isinstance(item, dict) and item.get("link") not in existing_links
        ]

        if new_data:
            # Kết hợp data cũ và mới
            combined_data = existing_data + new_data

            # Ghi lại vào file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(combined_data, f, indent=4, ensure_ascii=False)

            logger.info(
                "Added %d new records. Total records: %d",
                len(new_data),
                len(combined_data),
            )
        else:
            logger.info(
                "No new data to add. All %d records already exist.", len(result)
            )

        return 1
    except (ValueError, TypeError, OSError) as e:
        logger.error("Error in saving data: %s", e)
        return 0


def crawl_links(url, name):
    """
    Controller function to scrape all links from the url.
    params:
        - url: url of the web page
        - name: name of the file
    """
    HTML_page = get_the_HTML_page(url)
    links = find_all_links(HTML_page)
    issue_days, update_days = find_all_metadata(HTML_page)
    result = concatenate_2_type_of_data(links, issue_days, update_days)
    flag = save_to_data(result, name)
    if flag:
        logger.info("Successfully scrape all links from the url")
    else:
        logger.info("Failed to scrape all links")


if __name__ == "__main__":
    testing_url = "https://luatvietnam.vn/van-ban-luat-viet-nam.html?OrderBy=0&keywords=&lFieldId=&EffectStatusId=0&DocTypeId=58&OrganId=0&page=1&pSize=20&ShowSapo=0https://luatvietnam.vn/van-ban-luat-viet-nam.html?OrderBy=0&keywords=&lFieldId=&EffectStatusId=0&DocTypeId=58&OrganId=0&page=1&pSize=20&ShowSapo=0"
    crawl_links(testing_url, "law_links.json")
