#!/usr/bin/env python3
"""
Script to extract unique titles from titles.txt file
"""


def extract_unique_titles(input_file="titles.txt", output_file="unique_titles.txt"):
    """
    Extract unique titles from input file and write to output file

    Args:
        input_file (str): Path to input file containing titles
        output_file (str): Path to output file for unique titles
    """
    unique_titles = set()

    print(f"Reading titles from: {input_file}")

    try:
        # Read all lines and add to set (automatically removes duplicates)
        with open(input_file, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                title = line.strip()
                if title:  # Skip empty lines
                    unique_titles.add(title)

                # Progress indicator for large files
                if line_num % 1000 == 0:
                    print(
                        f"Processed {line_num:,} lines... Found {len(unique_titles)} unique titles"
                    )

        # Convert to sorted list for consistent output
        unique_titles_list = sorted(list(unique_titles))

        # Write unique titles to output file
        with open(output_file, "w", encoding="utf-8") as f:
            for title in unique_titles_list:
                f.write(f"{title}\n")

        print(f"\n✅ Success!")
        print(f"📄 Total lines processed: {line_num:,}")
        print(f"🔗 Unique titles found: {len(unique_titles_list):,}")
        print(f"💾 Saved to: {output_file}")
        print(f"📉 Duplicates removed: {line_num - len(unique_titles_list):,}")
        print(
            f"🗜️  Compression ratio: {(1 - len(unique_titles_list)/line_num)*100:.1f}%"
        )

    except FileNotFoundError:
        print(f"❌ Error: File '{input_file}' not found!")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

    return True


def main():
    """Main function"""
    print("🔍 Unique Titles Extractor")
    print("=" * 40)

    # Extract unique titles
    success = extract_unique_titles()

    if success:
        # Also create a statistics file
        with open("title_stats.txt", "w", encoding="utf-8") as f:
            f.write("Title Statistics\n")
            f.write("================\n\n")

            # Count titles by type
            unique_titles = set()
            with open("titles.txt", "r", encoding="utf-8") as input_file:
                for line in input_file:
                    title = line.strip()
                    if title:
                        unique_titles.add(title)

            f.write(f"Total unique titles: {len(unique_titles)}\n\n")
            f.write("Titles by category:\n")

            # Group by common patterns
            bo_luat = [t for t in unique_titles if "Bộ luật" in t]
            luat = [t for t in unique_titles if "Luật" in t and "Bộ luật" not in t]
            nghi_dinh = [t for t in unique_titles if "Nghị định" in t]
            thong_tu = [t for t in unique_titles if "Thông tư" in t]
            quyet_dinh = [t for t in unique_titles if "Quyết định" in t]

            f.write(f"- Bộ luật: {len(bo_luat)}\n")
            f.write(f"- Luật: {len(luat)}\n")
            f.write(f"- Nghị định: {len(nghi_dinh)}\n")
            f.write(f"- Thông tư: {len(thong_tu)}\n")
            f.write(f"- Quyết định: {len(quyet_dinh)}\n")
            f.write(
                f"- Other: {len(unique_titles) - len(bo_luat) - len(luat) - len(nghi_dinh) - len(thong_tu) - len(quyet_dinh)}\n"
            )

        print(f"📊 Statistics saved to: title_stats.txt")


if __name__ == "__main__":
    main()
