#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để format lại file titles.txt - tách từng luật thành một dòng riêng
Approach mới: Dùng regex đơn giản hơn
"""

import re


def format_titles_simple():
    """
    Đọc file titles.txt và format lại để mỗi luật trên một dòng
    """
    try:
        # Đọc nội dung file
        with open("titles.txt", "r", encoding="utf-8") as f:
            content = f.read().strip()

        print(f"Độ dài nội dung gốc: {len(content)} ký tự")

        # Đơn giản hóa: thay thế tất cả " Bộ luật" và " Luật" thành "\nBộ luật" và "\nLuật"
        # Nhưng không thay thế cái đầu tiên

        # Approach mới: Sử dụng regex để tìm và thay thế chính xác hơn
        # Pattern: space + (Bộ luật|Luật) + space + chữ cái (có dấu hoặc không)
        pattern = r"(\s+)(Bộ luật|Luật)\s+([A-ZÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬÈÉẺẼẸÊỀẾỂỄỆÌÍỈĨỊÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢÙÚỦŨỤƯỪỨỬỮỰỲÝỶỸỴĐ])"

        # Thay thế bằng xuống dòng + luật mới
        formatted_content = re.sub(pattern, r"\n\2 \3", content)

        # Loại bỏ xuống dòng đầu tiên nếu có
        if formatted_content.startswith("\n"):
            formatted_content = formatted_content[1:]

        # Tách thành các dòng và loại bỏ dòng trống
        laws_list = [
            law.strip() for law in formatted_content.split("\n") if law.strip()
        ]

        print(f"Tìm thấy {len(laws_list)} luật")

        # Ghi vào file mới
        with open("titles_formatted.txt", "w", encoding="utf-8") as f:
            for law in laws_list:
                f.write(law + "\n")

        print(
            f"✅ Đã format thành công {len(laws_list)} luật vào file titles_formatted.txt"
        )

        # In ra 5 luật đầu tiên để kiểm tra
        print("\n📊 Thống kê:")
        print(f"   - Tổng số luật: {len(laws_list)}")
        print("   - 5 luật đầu tiên:")
        for i, law in enumerate(laws_list[:5], 1):
            print(f"     {i}. {law[:80]}...")

        return laws_list

    except Exception as e:
        print(f"❌ Lỗi khi format file: {str(e)}")
        return None


if __name__ == "__main__":
    print("🔄 Bắt đầu format file titles.txt...")
    format_titles_simple()
