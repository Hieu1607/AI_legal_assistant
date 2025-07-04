# Web Crawling Guide for AI Legal Assistant

This guide provides comprehensive documentation for the web crawling system used to extract legal documents from Vietnamese law websites.

## Overview

The crawling system is designed to collect legal documents from `luatvietnam.vn`, consisting of two main phases:
1. **Link Extraction**: Scraping links to legal documents from listing pages
2. **Content Extraction**: Fetching full HTML content and metadata from individual legal document pages
These function can work well with 2 url, based on what you want
`https://luatvietnam.vn/van-ban-luat-viet-nam.html?page=1` or
`https://luatvietnam.vn/van-ban-luat-viet-nam.html?OrderBy=0&keywords=&lFieldId=&EffectStatusId=0&DocTypeId=58&OrganId=0&page=1&pSize=20&ShowSapo=0https://luatvietnam.vn/van-ban-luat-viet-nam.html?OrderBy=0&keywords=&lFieldId=&EffectStatusId=0&DocTypeId=58&OrganId=0&page=1&pSize=20&ShowSapo=0`

## Architecture

The crawling system consists of the following key components:

### Core Modules

#### 1. `src/retrieval/links_scraper.py`
- **Purpose**: Extracts links and basic metadata from legal document listing pages
- **Target**: `luatvietnam.vn` document listing pages
- **Output**: JSON file containing links, issue dates, and update dates

#### 2. `src/retrieval/fetch_details.py`
- **Purpose**: Fetches complete HTML content and detailed metadata from individual legal document pages
- **Technology**: Uses Playwright for JavaScript-heavy pages
- **Output**: JSON file with full content, titles, and law IDs

#### 3. `scripts/scrape_links_from_url.py`
- **Purpose**: Script wrapper for link extraction
- **Function**: Calls the links_scraper module with predefined URLs

#### 4. `scripts/scrape_HTML_from_url.py`
- **Purpose**: Script wrapper for content extraction
- **Function**: Calls the fetch_details module to get full HTML content

#### 5. `run_scripts.py`
- **Purpose**: Command-line interface for running crawling operations
- **Commands**: Supports `list`, `detail`, and `all` operations

## Installation & Setup

### Prerequisites

```bash
# Install required Python packages
pip install requests beautifulsoup4 playwright

# Install Playwright browsers
playwright install chromium
```

### Project Structure

Ensure your project has the following structure:
```
AI_legal_assistant/
├── data/
│   └── raw/
├── src/
│   └── retrieval/
├── scripts/
├── configs/
└── docs/
```

## Usage

### Method 1: Using run_scripts.py (Recommended)

```bash
# Extract links only
python run_scripts.py list

# Extract full content only (requires existing links file)
python run_scripts.py detail

# Run complete crawling process (links + content)
python run_scripts.py all
```

### Method 2: Running Individual Scripts

```bash
# Step 1: Extract links
python scripts/scrape_links_from_url.py

# Step 2: Extract content
python scripts/scrape_HTML_from_url.py
```

### Method 3: Direct Module Usage

```python
from src.retrieval.links_scraper import crawl_links
from src.retrieval.fetch_details import fetch_detail

# Extract links
url = "https://luatvietnam.vn/van-ban-luat-viet-nam.html?page=1"
crawl_links(url, "law_links.json")

# Extract content
result = fetch_detail("data/raw/law_links.json")
```

## Detailed Functionality

### Link Extraction Process

**Function**: `crawl_links()` in `links_scraper.py`

1. **HTTP Request**: Sends GET request with browser-like headers to avoid blocking
2. **HTML Parsing**: Uses BeautifulSoup to parse the HTML response
3. **Link Extraction**: Finds links using CSS selectors:
   - `h2.doc-title a` - Main document titles
   - `h3.doc-title a` - Sub-document titles
4. **Metadata Extraction**: Extracts issue dates and update dates from `div.doc-dmy` elements
5. **Data Processing**: Combines links with metadata into structured format
6. **Output**: Saves to `data/raw/law_links.json`

**Sample Output**:
```json
[
    {
        "link": "https://luatvietnam.vn/lao-dong/bo-luat-lao-dong-2019-179015-d1.html",
        "date_of_issue": "01/01/2021",
        "update_day": "15/06/2023"
    }
]
```

### Content Extraction Process

**Function**: `fetch_detail()` in `fetch_details.py`

1. **Input Processing**: Reads the links JSON file from previous step
2. **Browser Automation**: Uses Playwright to:
   - Launch headless Chromium browser
   - Navigate to each legal document URL
   - Wait for page to fully load
3. **Data Extraction**:
   - Full HTML content via `page.content()`
   - Document title from `h1.the-document-title`
   - Law ID extraction from title text
4. **Output**: Saves comprehensive metadata to `data/raw/law_metadata.json`

**Sample Output**:
```json
[
    {
        "links": "https://luatvietnam.vn/lao-dong/bo-luat-lao-dong-2019-179015-d1.html",
        "date_of_issue": "01/01/2021",
        "update_day": "15/06/2023",
        "content": "<html>...</html>",
        "law_id": "179015-d1",
        "title": "Bộ luật Lao động 2019"
    }
]
```

## Configuration

### Request Headers
The system uses realistic browser headers to avoid blocking:
```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8",
    # ... additional headers
}
```

### Rate Limiting
- Random delays between requests: 1-3 seconds
- Timeout setting: 20 seconds per request

### Target URLs
Default target URL pattern:
```
https://luatvietnam.vn/van-ban-luat-viet-nam.html?OrderBy=0&keywords=&lFieldId=&EffectStatusId=0&DocTypeId=58&OrganId=0&page=1&pSize=20&ShowSapo=0
```

## Error Handling

The system includes comprehensive error handling:

### Network Errors
- Request timeouts
- Connection failures
- HTTP error status codes

### Parsing Errors
- Invalid HTML structure
- Missing elements
- Encoding issues

### File System Errors
- Directory creation
- File writing permissions
- JSON serialization errors

### Logging
All operations are logged using the project's logging system:
- Info level: Successful operations and progress
- Error level: Failures and exceptions
- Log files: Stored in `logs/` directory

## Data Flow

```
1. URL Input → links_scraper.py
2. Extract Links → data/raw/law_links.json
3. Links File → fetch_details.py
4. Extract Content → data/raw/law_metadata.json
5. Further Processing → data/processed/
```

## Output Files

### Primary Output Files
- `data/raw/law_links.json`: Links and basic metadata
- `data/raw/law_metadata.json`: Complete content and metadata

### Log Files
- `logs/app.log`: General application logs
- `logs/errors.log`: Error-specific logs
- `logs/info.log`: Information logs

## Troubleshooting

### Common Issues

1. **Request Blocked/403 Error**
   - Solution: Adjust headers, add delays, or use proxy

2. **Playwright Browser Not Found**
   - Solution: Run `playwright install chromium`

3. **File Permission Errors**
   - Solution: Check write permissions for `data/raw/` directory

4. **Memory Issues with Large Content**
   - Solution: Process in smaller batches or increase system memory

### Performance Optimization

1. **Parallel Processing**: Consider using concurrent requests for link extraction
2. **Batch Processing**: Process content extraction in smaller batches
3. **Caching**: Implement caching for already processed URLs
4. **Resume Capability**: Add functionality to resume interrupted crawling

## Best Practices

1. **Respect robots.txt**: Check website's robots.txt file
2. **Rate Limiting**: Don't overwhelm the server with too many requests
3. **Error Recovery**: Implement retry logic for failed requests
4. **Data Validation**: Validate extracted data before saving
5. **Monitoring**: Monitor crawling progress and success rates

## Legal and Ethical Considerations

1. **Terms of Service**: Ensure compliance with website's terms of service
2. **Copyright**: Respect copyright laws when using scraped content
3. **Data Privacy**: Handle any personal data according to privacy regulations
4. **Server Load**: Avoid causing excessive load on target servers

## Future Enhancements

1. **Incremental Updates**: Only crawl new or updated documents
2. **Multi-source Support**: Add support for additional legal websites
3. **Content Filtering**: Add filtering for specific document types
4. **Database Integration**: Direct database storage instead of JSON files
5. **API Integration**: Provide REST API for crawling operations
