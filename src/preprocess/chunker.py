import json
import os
import re
import sys

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, str(root))
from configs.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def chunk_law_text(text):
    chunks = []
    current_chunk = {
        "chapter": None,
        "section": None,
        "subsection": None,
        "article": None,
        "content": [],
    }
    lines = text.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Chapter
        if re.match(r"^CHƯƠNG\s+[IVXLCDM]+", line, re.IGNORECASE):
            if current_chunk["content"] or any(current_chunk.values()):
                chunks.append(current_chunk.copy())
            current_chunk["chapter"] = line
            current_chunk["section"] = None
            current_chunk["subsection"] = None
            current_chunk["article"] = None
            current_chunk["content"] = []
            continue

        # Section
        if re.match(r"^Mục\s+\d+", line):
            if current_chunk["content"] or any(current_chunk.values()):
                chunks.append(current_chunk.copy())
            current_chunk["section"] = line
            current_chunk["subsection"] = None
            current_chunk["article"] = None
            current_chunk["content"] = []
            continue

        # Subsection
        if re.match(r"^Tiểu mục\s+\d+\.", line):
            if current_chunk["content"] or any(current_chunk.values()):
                chunks.append(current_chunk.copy())
            current_chunk["subsection"] = line
            current_chunk["article"] = None
            current_chunk["content"] = []
            continue

        # Article - Stop here and collect all content until next article
        if re.match(r"^Điều\s+\d+", line):
            if current_chunk["content"] or any(current_chunk.values()):
                chunks.append(current_chunk.copy())
            # Keep same chapter, section and subsection
            current_chunk["article"] = line
            current_chunk["content"] = []
            continue

        # All other content goes into the current chunk
        current_chunk["content"].append(line)

    # Add last chunk if there's content
    if current_chunk["content"] or current_chunk["chapter"] or current_chunk["article"]:
        chunks.append(current_chunk)

    return chunks


def make_chunk_id(chunk):
    parts = []

    # Create rule sets for each level - only up to article
    rules = [
        ("chapter", r"CHƯƠNG\s+([IVXLCDM]+)", "CHUONG_{}"),
        ("section", r"Mục\s+(\d+)", "Muc_{}"),
        ("subsection", r"Tiểu mục\s+(\d+)", "Tieu_muc_{}"),
        ("article", r"Điều\s+(\d+)", "Dieu_{}"),
    ]

    for field, pattern, template in rules:
        value = chunk.get(field)
        if value:
            match = re.search(pattern, value, re.IGNORECASE)
            if match:
                parts.append(template.format(match.group(1)))

    return "_".join(parts)


def chunks_to_right_schema(chunks):
    chunk_id_container = []
    content_container = []
    for chunk in chunks:
        if chunk["article"]:  # Only take the chunk with article
            chunk_id = make_chunk_id(chunk)
            content_parts = []
            # Only include structural elements and content
            for field in [
                "chapter",
                "section", 
                "subsection",
                "article",
            ]:
                if chunk[field] is not None:
                    content_parts.append(chunk[field])
            
            # Add the actual content
            if chunk["content"]:
                content_parts.extend(chunk["content"])
            
            content = "\n".join(content_parts)
            chunk_id_container.append(chunk_id)
            content_container.append(content)
    return chunk_id_container, content_container


def add_metadata(chunk_id_container, content_container, metadata):
    res = []
    title = metadata.get("title", "")
    update_day = metadata.get("update_day", "")
    date_of_issue = metadata.get("date_of_issue", "")
    law_id = metadata.get("law_id", "")

    if len(chunk_id_container) == len(content_container):
        for numth, chunk_id in enumerate(chunk_id_container):
            current_chunk = {
                "title": title,
                "update_day": update_day,
                "date_of_issue": date_of_issue,
                "chunk_id": law_id.replace(" ", "_")
                .replace("/", "_")
                .replace("\\", "_")
                .replace("-", "_")
                + "_"
                + chunk_id,
                "text": content_container[numth],
            }
            res.append(current_chunk)
    else:
        logger.error(
            "The length of chunk_id_container and content_container are not the same"
        )
    return res


def make_chunks_from_metadata(metadata_file):
    try:
        for metadata in metadata_file:
            text_file_name = (
                metadata["law_id"]
                .replace(" ", "_")
                .replace("/", "_")
                .replace("\\", "_")
                .replace("-", "_")
                + ".txt"
            )
            text_file_path = os.path.join(
                root, "data", "processed", "texts", text_file_name
            )
            save_file_path = os.path.join(root, "data", "processed", "chunks")
            with open(text_file_path, "r", encoding="utf-8") as f:
                text_file = f.read()
                chunks = chunk_law_text(text_file)
                chunk_id_container, content_container = chunks_to_right_schema(chunks)
                res = add_metadata(chunk_id_container, content_container, metadata)
                new_chunks_file_name = (
                    (
                        metadata["law_id"]
                        .replace(" ", "_")
                        .replace("/", "_")
                        .replace("\\", "_")
                        .replace("-", "_")
                        + ".txt"
                    )
                    + "_chunks"
                    + ".json"
                )
                new_chunks_file_path = os.path.join(
                    save_file_path, new_chunks_file_name
                )
                with open(new_chunks_file_path, "w", encoding="utf-8") as f:
                    json.dump(res, f, ensure_ascii=False, indent=4)
            logger.info("Done processing %s", metadata["title"])
        logger.info("Done processing all files")
    except (ValueError, OSError, KeyError) as e:
        logger.error("An error happenned : %s", e)


def process_all_text_files():
    """Process all text files from both 'texts' and 'new_texts' directories and consolidate into one file"""
    all_chunks = []
    
    # Process files from both directories
    text_dirs = ["texts", "new_texts"]
    
    for text_dir in text_dirs:
        text_dir_path = os.path.join(root, "data", "processed", text_dir)
        
        if not os.path.exists(text_dir_path):
            logger.warning(f"Directory {text_dir_path} does not exist, skipping...")
            continue
            
        logger.info(f"Processing files from {text_dir}...")
        
        # Get all .txt files in the directory
        for filename in os.listdir(text_dir_path):
            if filename.endswith(".txt"):
                file_path = os.path.join(text_dir_path, filename)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        text_content = f.read()
                    
                    # Extract law_id from filename (remove .txt extension)
                    law_id = filename[:-4]
                    
                    # Create basic metadata from filename
                    metadata = {
                        "law_id": law_id,
                        "title": law_id.replace("_", " "),
                        "update_day": "",
                        "date_of_issue": "",
                        "source_directory": text_dir
                    }
                    
                    # Process the text
                    chunks = chunk_law_text(text_content)
                    chunk_id_container, content_container = chunks_to_right_schema(chunks)
                    file_chunks = add_metadata(chunk_id_container, content_container, metadata)
                    
                    all_chunks.extend(file_chunks)
                    logger.info(f"Processed {filename}: {len(file_chunks)} chunks")
                    
                except Exception as e:
                    logger.error(f"Error processing {filename}: {e}")
    
    # Save consolidated chunks to file
    output_file = os.path.join(root, "data", "processed", "all_consolidated_chunks.json")
    
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully saved {len(all_chunks)} total chunks to {output_file}")
        
        # Print summary
        print(f"\n=== CONSOLIDATION SUMMARY ===")
        print(f"Total chunks processed: {len(all_chunks)}")
        print(f"Output file: {output_file}")
        
        # Group by source directory for summary
        texts_count = sum(1 for chunk in all_chunks if chunk.get("title", "").find("texts") != -1 or "source_directory" not in chunk or chunk["source_directory"] == "texts")
        new_texts_count = len(all_chunks) - texts_count
        
        print(f"Chunks from 'texts' directory: {texts_count}")  
        print(f"Chunks from 'new_texts' directory: {new_texts_count}")
        print("================================\n")
        
    except Exception as e:
        logger.error(f"Error saving consolidated file: {e}")
    
    return all_chunks


if __name__ == "__main__":
    print("Starting to process all text files from 'texts' and 'new_texts' directories...")
    print("Chunking will be done only up to Điều (Article) level.")
    
    try:
        all_chunks = process_all_text_files()
        print(f"Processing completed successfully! Total chunks: {len(all_chunks)}")
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        logger.error(f"Error during processing: {e}")
