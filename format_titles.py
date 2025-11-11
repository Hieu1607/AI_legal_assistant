#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để format lại file titles.txt - tách từng luật thành một dòng riêng
"""

import re


def format_titles_file(input_file, output_file):
    """
    Đọc file titles.txt và format lại để mỗi luật trên một dòng
    """
    try:
        # Đọc nội dung file
        with open(input_file, "r", encoding="utf-8") as f:
            content = f.read().strip()

        # Pattern để tách các luật:
        # Tìm các vị trí mà sau đó là " Bộ luật" hoặc " Luật"
        # (có dấu cách trước và sau từ "Luật" hoặc "Bộ luật")

        # Thêm xuống dòng trước mỗi "Bộ luật" hoặc "Luật" mới (trừ cái đầu tiên)
        # Pattern: tìm khoảng trắng + (Bộ luật|Luật) + khoảng trắng + chữ cái in hoa
        formatted_content = re.sub(
            r"(\s)(Bộ\s+luật|Luật)(\s+[A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ])",
            r"\n\2\3",
            content,
        )

        # Tách thành các dòng và loại bỏ dòng trống
        laws_list = [
            law.strip() for law in formatted_content.split("\n") if law.strip()
        ]

        # Ghi vào file mới
        with open(output_file, "w", encoding="utf-8") as f:
            for law in laws_list:
                f.write(law + "\n")

        print(f"✅ Đã format thành công {len(laws_list)} luật vào file {output_file}")
        return laws_list

    except Exception as e:
        print(f"❌ Lỗi khi format file: {str(e)}")
        return None


if __name__ == "__main__":
    input_file = "titles.txt"
    output_file = "titles_formatted.txt"

    print("🔄 Bắt đầu format file titles.txt...")
    laws = format_titles_file(input_file, output_file)

    if laws:
        print(f"\n📊 Thống kê:")
        print(f"   - Tổng số luật: {len(laws)}")
        print(f"   - 5 luật đầu tiên:")
        for i, law in enumerate(laws[:5], 1):
            print(f"     {i}. {law[:60]}...")
