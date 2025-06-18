import os
import re
import sys

# src/extract_data/extract_clean_text.py
from bs4 import BeautifulSoup, Tag

# from pathlib import Path


def get_project_root():
    """Get the root directory of the project."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    while True:
        # Kiểm tra xem 'data' và 'src' có tồn tại trong thư mục hiện tại không
        if os.path.isdir(os.path.join(current_dir, "data")) and os.path.isdir(
            os.path.join(current_dir, "src")
        ):
            return current_dir

        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # Đã đến thư mục gốc của hệ thống
            raise FileNotFoundError(
                "Check the project structure. 'data' and 'src' directories not found."
            )
        current_dir = parent_dir
    return current_dir


# Set up logging
root = get_project_root()
sys.path.insert(0, str(root))

from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def clean_text(text):
    """Clean text by removing extra whitespace and unwanted characters."""
    text = re.sub(
        r"\s+", " ", text.strip()
    )  # strip() method removes leading and trailing whitespace
    return text


def extract_text_from_html(html_file_path):
    """Extract text from HTML file and preserve structure for markdown."""
    try:
        with open(html_file_path, "r", encoding="utf-8") as file:
            soup = BeautifulSoup(file, "html.parser")
    except (FileNotFoundError, UnicodeDecodeError) as e:
        logger.error("Error reading HTML file %s: %s", html_file_path, e)
        return ""

    output = []

    # Get the main title
    title = soup.find("h3")
    if title:
        title_text = clean_text(title.get_text())
        output.append(f"# {title_text}")

    # Find content div
    content_div = soup.find("div", class_="_content")
    if not content_div or not isinstance(content_div, Tag):
        logger.warning("No content div found in %s", html_file_path)
        return ""

    # Process elements
    elements = content_div.find_all(["p", "a"], recursive=True)
    for element in elements:
        if not isinstance(element, Tag):
            continue

        element_class = element.get("class")
        if not element_class:
            continue

        processed_text = _process_element_by_class(element, element_class)
        if processed_text:
            output.append(processed_text)

    return "\n".join(output)


def _process_element_by_class(element, element_class):
    """Process element based on its CSS class."""
    class_name = element_class[0] if element_class else ""

    # Class handlers mapping
    handlers = {
        "pChuong": _handle_chapter_element,
        "pDieu": _handle_article_element,
        "pGhiChu": _handle_note_element,
        "pNoiDung": _handle_content_element,
        "pChiDan": _handle_reference_element,
    }

    handler = handlers.get(class_name)
    if handler:
        return handler(element)

    return None


def _handle_chapter_element(element):
    """Handle Chapter (Chương) elements."""
    chapter_text = clean_text(element.get_text())

    if chapter_text.startswith("Chương"):
        return f"\n### {chapter_text}"
    if "Mục" in chapter_text:
        return f"\n#### {chapter_text}"
    return f"\n#### {chapter_text}"


def _handle_article_element(element):
    """Handle Article (Điều) elements."""
    article_text = clean_text(element.get_text())
    return f"\n##### {article_text}"


def _handle_note_element(element):
    """Handle Notes (GhiChu) elements."""
    note_link = element.find("a")
    if note_link and isinstance(note_link, Tag):
        note_text = clean_text(note_link.get_text())
        return f"*{note_text}*"
    return None


def _handle_content_element(element):
    """Handle Content (NoiDung) elements."""
    content_parts = []
    paragraphs = element.find_all("p")

    for paragraph in paragraphs:
        if isinstance(paragraph, Tag):
            content_text = clean_text(paragraph.get_text())
            if content_text:  # Only add non-empty content
                content_parts.append(content_text)

    return "\n".join(content_parts) if content_parts else None


def _handle_reference_element(element):
    """Handle References (ChiDan) elements."""
    reference_text = clean_text(element.get_text())
    return f"({reference_text})" if reference_text else None


def save_to_markdown(content, output_dir, filename):
    """Save extracted content to a markdown file in the specified directory."""
    if len(content) < 100:  # Skip files with too little content
        print(f"Skipping {filename} due to insufficient content length.")
        return

    project_root = get_project_root()
    output_dir_path = os.path.join(
        project_root, "data", "processed", "rules", output_dir
    )  # Create the directory first
    os.makedirs(output_dir_path, exist_ok=True)

    # Create the full file path with .md extension
    output_file_path = os.path.join(output_dir_path, f"{filename}.md")

    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved to {output_file_path}")


def process_legal_document(html_file_path):
    """Process the HTML file and save extracted content to appropriate folder."""
    # Extract filename without extension
    logger.info("Processing file: %s", html_file_path)
    filename = os.path.basename(html_file_path)
    output_filename = ""
    if not filename.endswith(".html"):
        print(f"File must be an HTML file: {filename}")
        return

    # Try to extract topic number from the file content or use filename
    with open(html_file_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")
    big_subject = 0
    small_subject = 0
    description = ""

    # Get the main title
    title = soup.find("h3")
    h3_text = ""
    if title is not None:
        h3_text = " ".join(title.get_text().split())
    # print(f"title: {title}")
    if title:
        title_text = clean_text(title.get_text())
        text = re.match(r"Đề mục \d+\.\d+\s*(.*)", h3_text)
        if text:
            description = text.group(1).strip()
        match = re.search(r"Đề mục (\d+)\.(\d+)", title_text)
        if match:
            big_subject = match.group(1)  # Số nguyên
            small_subject = match.group(2)  # Số thập phân
        else:
            raise ValueError(f"Title does not match expected format: {title_text}")
        folder_name = os.path.join(f"chu_de_{big_subject}", f"de_muc_{small_subject}")
    else:
        # Use the base filename if no topic found
        folder_name = "data_error"
    description = description.replace(" ", "_")
    description = description.replace(",", "_")
    description = description.replace(".", "_")
    # Cut off the description if it's too long
    if len(description) > 50:
        description = description[:50]
    output_filename = f"{big_subject}_{small_subject}_{description}".strip()
    print("Output filename is : ", output_filename)
    # Extract text
    content = extract_text_from_html(html_file_path)  # Save to markdown
    save_to_markdown(content, folder_name, output_filename)
    logger.info(
        "Processed %s into %s/%s.md", html_file_path, folder_name, output_filename
    )


# Example usage
if __name__ == "__main__":
    testing_html = "input.html"
    process_legal_document(testing_html)
