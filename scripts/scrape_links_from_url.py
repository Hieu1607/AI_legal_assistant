import sys
import os
# Define get_project_root locally to avoid circular import issues
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Set up paths
if root not in sys.path:
    sys.path.insert(0, root)

# Now we can import modules
from configs.logger import get_logger, setup_logging
from src.retrieval.links_scraper import crawl_links

setup_logging()
logger = get_logger(__name__)

# URL for scraping law links - breaking into multiple lines to satisfy linting
# base_url = "https://luatvietnam.vn/van-ban-luat-viet-nam.html"
# params = "?OrderBy=0&keywords=&lFieldId=&EffectStatusId=0&DocTypeId=58&OrganId=0&page=1&pSize=20&ShowSapo=0"
for i in range(1, 40, 1):
    print(i)
    base_url = " https://luatvietnam.vn/van-ban/ajax/searchajax"
    params = f"?Keywords=&DateFromString=&DateToString=&IsSearchExact=0&SearchByDate=issueDate&DocGroupId=0&DocTypeId=&EffectStatusId=&LanguageId=1&FieldId=&OrganId=&SearchOptions=1&DocTypeIds=10&RowAmount=20&PageIndex={i}"
    real_url = base_url + params
    # url = "https://luatvietnam.vn/van-ban-luat-viet-nam.html?page=1"
    crawl_links(real_url, "new_law_links.json")
    # crawl_links(url, "law_links_from_head_page.json")
