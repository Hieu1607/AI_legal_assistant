import os
import sys


def run_scrape_list():
    os.system("python scripts/scrape_links_from_url.py")


def run_scrape_detail():
    os.system("python scripts/scrape_HTML_from_url.py")


def run_all():
    run_scrape_list()
    run_scrape_detail()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_crawl.py [list|detail|all]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "list":
        run_scrape_list()
    elif command == "detail":
        run_scrape_detail()
    elif command == "all":
        run_all()
    else:
        print(f"Unknown command: {command}")
        print("Usage: python run_crawl.py [list|detail|all]")
