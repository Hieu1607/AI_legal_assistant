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
        "clause": None,
        "point": None,
        "content": [],
    }
    lines = text.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Chương
        if re.match(r"^CHƯƠNG\s+[IVXLCDM]+", line, re.IGNORECASE):
            if current_chunk["content"] or any(current_chunk.values()):
                chunks.append(current_chunk.copy())
            current_chunk["chapter"] = line
            current_chunk["section"] = None
            current_chunk["subsection"] = None
            current_chunk["article"] = None
            current_chunk["clause"] = None
            current_chunk["point"] = None
            current_chunk["content"] = []
            continue

        # Mục
        if re.match(r"^Mục\s+\d+", line):
            if current_chunk["content"] or any(current_chunk.values()):
                chunks.append(current_chunk.copy())
            current_chunk["section"] = line
            current_chunk["subsection"] = None
            current_chunk["clause"] = None
            current_chunk["point"] = None
            current_chunk["content"] = []
            continue

        # Tiểu mục
        if re.match(r"^Tiểu mục\s+\d+\.", line):
            if current_chunk["content"] or any(current_chunk.values()):
                chunks.append(current_chunk.copy())
            current_chunk["subsection"] = line
            current_chunk["article"] = None
            current_chunk["clause"] = None
            current_chunk["point"] = None
            current_chunk["content"] = []
            continue

        # Điều
        if re.match(r"^Điều\s+\d+", line):
            if current_chunk["content"] or any(current_chunk.values()):
                chunks.append(current_chunk.copy())
            # Giữ nguyên chapter, section và subsection
            current_chunk["article"] = line
            current_chunk["clause"] = None
            current_chunk["point"] = None
            current_chunk["content"] = []
            continue

        # Khoản
        if re.match(r"^\d+\.", line):  # Sửa regex để khớp với định dạng "1.", "2.", ...
            if current_chunk["content"] or any(current_chunk.values()):
                chunks.append(current_chunk.copy())
            current_chunk["clause"] = line
            current_chunk["point"] = None
            current_chunk["content"] = []
            continue

        # Điểm
        if re.match(r"^[a-zA-Z]\)", line) or re.match(r"^[aAÀÁẢẠÃăâđêôơư]{1}\)", line):
            if current_chunk["content"] or any(current_chunk.values()):
                chunks.append(current_chunk.copy())
            current_chunk["point"] = line
            current_chunk["content"] = []
            continue

        # Nội dung bình thường - thêm vào cấp hiện tại thay vì content riêng biệt
        # Tìm cấp cao nhất hiện tại để nối text vào
        if current_chunk["point"]:
            current_chunk["point"] += " " + line
        elif current_chunk["clause"]:
            current_chunk["clause"] += " " + line
        elif current_chunk["article"]:
            current_chunk["article"] += " " + line
        elif current_chunk["subsection"]:
            current_chunk["subsection"] += " " + line
        elif current_chunk["section"]:
            current_chunk["section"] += " " + line
        elif current_chunk["chapter"]:
            current_chunk["chapter"] += " " + line
        else:
            # Nếu chưa có cấp nào, thêm vào content
            current_chunk["content"].append(line)

    # Thêm chunk cuối cùng nếu có nội dung
    if current_chunk["content"] or current_chunk["chapter"] or current_chunk["article"]:
        chunks.append(current_chunk)

    return chunks


def make_chunk_id(chunk):
    parts = []

    # Tạo các bộ quy tắc cho từng cấp
    rules = [
        ("chapter", r"CHƯƠNG\s+([IVXLCDM]+)", "CHUONG_{}"),
        ("section", r"Mục\s+(\d+)", "Muc_{}"),
        ("subsection", r"Tiểu mục\s+(\d+)", "Tieu_muc_{}"),
        ("article", r"Điều\s+(\d+)", "Dieu_{}"),
        ("clause", r"^(\d+)\.", "Khoan_{}"),
        ("point", r"^([a-zA-Zàáạảãâăèéẹẻẽêôơưùúụủũđíìịỉĩ])\)", "Diem_{}"),
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
        if chunk["article"]:  # Only take the chunk with article and lower levels
            chunk_id = make_chunk_id(chunk)
            content_parts = []
            for field in [
                "chapter",
                "section",
                "subsection",
                "article",
                "clause",
                "point",
            ]:
                if chunk[field] is not None:
                    content_parts.append(chunk[field])
            content = "; ".join(content_parts)
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
        processed_count = 0
        skipped_count = 0

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
                root, "data", "processed", "new_texts", text_file_name
            )

            # Kiểm tra xem file có tồn tại không
            if not os.path.exists(text_file_path):
                logger.warning("File not found, skipping: %s", text_file_path)
                skipped_count += 1
                continue

            try:
                save_file_path = os.path.join(root, "data", "processed", "new_chunks")
                # Tạo thư mục save nếu chưa tồn tại
                os.makedirs(save_file_path, exist_ok=True)

                with open(text_file_path, "r", encoding="utf-8") as f:
                    text_file = f.read()
                    chunks = chunk_law_text(text_file)
                    chunk_id_container, content_container = chunks_to_right_schema(
                        chunks
                    )
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
                processed_count += 1
            except (FileNotFoundError, OSError, IOError) as file_error:
                logger.error("Error processing file %s: %s", text_file_name, file_error)
                skipped_count += 1
                continue

        logger.info(
            "Processing completed. Processed: %d, Skipped: %d",
            processed_count,
            skipped_count,
        )
    except (ValueError, KeyError) as e:
        logger.error("An error happened: %s", e)


if __name__ == "__main__":
    file_path = "src/preprocess/law.txt"
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            text_txt = file.read()
        result = chunk_law_text(text_txt)
        with open("test2.json", "w", encoding="utf-8") as file:
            json.dump(result, file, ensure_ascii=False, indent=4)
    except (ValueError, OSError) as e:
        print(f"Lỗi: {str(e)}")
