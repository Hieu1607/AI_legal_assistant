import os
import sys


root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if root not in sys.path:
    sys.path.insert(0, root)

# Now we can import modules
from configs.logger import get_logger, setup_logging
from src.retrieval.links_scraper import crawl_links

setup_logging()
logger = get_logger(__name__)


# URL for scraping law links - breaking into multiple lines to satisfy linting
base_url = "https://luatvietnam.vn/van-ban-luat-viet-nam.html"
params = "?OrderBy=0&keywords=&lFieldId=&EffectStatusId=0&DocTypeId=58&OrganId=0&page=1&pSize=20&ShowSapo=0"
real_url = base_url + params
# url = "https://luatvietnam.vn/van-ban-luat-viet-nam.html?page=1"
crawl_links(real_url, "law_links.json")
# crawl_links(url, "law_links_from_head_page.json")
