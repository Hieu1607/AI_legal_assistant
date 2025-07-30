#!/usr/bin/env python3
"""
Script to filter chunks that are larger than 14 KB
Author: AI Assistant
Date: 2025-07-29
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
# print(root)
sys.path.insert(0, root)


def get_chunk_size_in_bytes(chunk: Dict[str, Any]) -> int:
    """
    Calculate the size of a chunk in bytes

    Args:
        chunk: Dictionary containing chunk data

    Returns:
        Size of chunk in bytes
    """
    # Convert chunk to JSON string and calculate size
    chunk_json = json.dumps(chunk, ensure_ascii=False)
    return len(chunk_json.encode("utf-8"))


def filter_large_chunks(
    input_file: str, size_threshold_kb: int = 14
) -> List[Dict[str, Any]]:
    """
    Filter chunks that are larger than the specified threshold

    Args:
        input_file: Path to the input JSON file containing chunks
        size_threshold_kb: Size threshold in KB (default: 14 KB)

    Returns:
        List of chunks that exceed the size threshold
    """
    size_threshold_bytes = size_threshold_kb * 1024  # Convert KB to bytes
    large_chunks = []

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        print(f"Processing {len(chunks)} chunks from {input_file}")

        for i, chunk in enumerate(chunks):
            chunk_size = get_chunk_size_in_bytes(chunk)

            if chunk_size > size_threshold_bytes:
                chunk_with_size = chunk.copy()
                chunk_with_size["size_bytes"] = chunk_size
                chunk_with_size["size_kb"] = round(chunk_size / 1024, 2)
                large_chunks.append(chunk_with_size)

                print(
                    f"Large chunk found: {chunk.get('chunk_id', f'chunk_{i}')} - "
                    f"{chunk_size} bytes ({chunk_size/1024:.2f} KB)"
                )

        print(f"Found {len(large_chunks)} chunks larger than {size_threshold_kb} KB")

    except FileNotFoundError:
        print(f"Error: File {input_file} not found")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file {input_file}")
    except Exception as e:
        print(f"Error processing file {input_file}: {str(e)}")

    return large_chunks


def process_all_chunk_files(
    data_dir: str = "data_to_render", size_threshold_kb: int = 14
) -> None:
    """
    Process all chunk files in the specified directory

    Args:
        data_dir: Directory containing chunk files
        size_threshold_kb: Size threshold in KB
    """
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"Error: Directory {data_dir} not found")
        return

    all_large_chunks = []
    chunk_files = list(data_path.glob("chunks_part_*.json"))

    if not chunk_files:
        print(f"No chunk files found in {data_dir}")
        return

    print(f"Found {len(chunk_files)} chunk files to process")
    print("=" * 60)

    for chunk_file in sorted(chunk_files):
        print(f"\nProcessing: {chunk_file.name}")
        large_chunks = filter_large_chunks(str(chunk_file), size_threshold_kb)
        all_large_chunks.extend(large_chunks)

    print("\n" + "=" * 60)
    print(
        f"SUMMARY: Found {len(all_large_chunks)} total chunks larger than {size_threshold_kb} KB"
    )

    if all_large_chunks:
        # Save results to output file
        output_file = f"large_chunks_over_{size_threshold_kb}kb.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_large_chunks, f, ensure_ascii=False, indent=2)

        print(f"Large chunks saved to: {output_file}")

        # Print detailed statistics
        print("\nDetailed Statistics:")
        print("-" * 40)

        sizes = [chunk["size_kb"] for chunk in all_large_chunks]
        sizes.sort(reverse=True)

        print(f"Largest chunk: {max(sizes):.2f} KB")
        print(f"Smallest large chunk: {min(sizes):.2f} KB")
        print(f"Average size: {sum(sizes)/len(sizes):.2f} KB")

        print(f"\nTop 10 largest chunks:")
        for i, chunk in enumerate(
            sorted(all_large_chunks, key=lambda x: x["size_kb"], reverse=True)[:10]
        ):
            print(
                f"{i+1:2d}. {chunk.get('chunk_id', 'Unknown ID'):<50} "
                f"{chunk['size_kb']:>8.2f} KB"
            )

    else:
        print(f"No chunks found larger than {size_threshold_kb} KB")


def remove_large_chunks_from_file(input_file: str, size_threshold_kb: int = 14) -> None:
    """
    Remove chunks larger than threshold from the input file and save back to the same file

    Args:
        input_file: Path to the input JSON file containing chunks
        size_threshold_kb: Size threshold in KB (default: 14 KB)
    """
    size_threshold_bytes = size_threshold_kb * 1024  # Convert KB to bytes

    try:
        # Read the original file
        with open(input_file, "r", encoding="utf-8") as f:
            original_chunks = json.load(f)

        print(f"Original file contains {len(original_chunks)} chunks")

        # Filter out large chunks
        filtered_chunks = []
        removed_chunks = []

        for i, chunk in enumerate(original_chunks):
            chunk_size = get_chunk_size_in_bytes(chunk)

            if chunk_size > size_threshold_bytes:
                chunk_with_size = chunk.copy()
                chunk_with_size["size_bytes"] = chunk_size
                chunk_with_size["size_kb"] = round(chunk_size / 1024, 2)
                removed_chunks.append(chunk_with_size)

                print(
                    f"Removing large chunk: {chunk.get('chunk_id', f'chunk_{i}')} - "
                    f"{chunk_size} bytes ({chunk_size/1024:.2f} KB)"
                )
            else:
                filtered_chunks.append(chunk)

        # Create backup of original file
        backup_file = input_file.replace(".json", "_backup.json")
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(original_chunks, f, ensure_ascii=False, indent=2)
        print(f"Original file backed up to: {backup_file}")

        # Save filtered chunks back to original file
        with open(input_file, "w", encoding="utf-8") as f:
            json.dump(filtered_chunks, f, ensure_ascii=False, indent=2)

        # Save removed chunks for reference
        if removed_chunks:
            removed_file = f"removed_large_chunks_over_{size_threshold_kb}kb.json"
            with open(removed_file, "w", encoding="utf-8") as f:
                json.dump(removed_chunks, f, ensure_ascii=False, indent=2)
            print(f"Removed chunks saved to: {removed_file}")

        print(f"\nSUMMARY:")
        print(f"- Original chunks: {len(original_chunks)}")
        print(f"- Removed chunks: {len(removed_chunks)}")
        print(f"- Remaining chunks: {len(filtered_chunks)}")
        print(f"- File updated: {input_file}")

    except FileNotFoundError:
        print(f"Error: File {input_file} not found")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file {input_file}")
    except Exception as e:
        print(f"Error processing file {input_file}: {str(e)}")


def main():
    """Main function"""
    print("Large Chunks Filter Tool")
    print("=" * 60)

    # Default parameters
    input_file = os.path.join(root, "data", "processed", "new_all_chunks.json")
    size_threshold_kb = 14
    remove_mode = False

    # Parse command line arguments if provided
    if len(sys.argv) > 1:
        if sys.argv[1].lower() == "remove":
            remove_mode = True
            if len(sys.argv) > 2:
                try:
                    size_threshold_kb = int(sys.argv[2])
                except ValueError:
                    print(
                        f"Invalid threshold value: {sys.argv[2]}. Using default: {size_threshold_kb} KB"
                    )
            if len(sys.argv) > 3:
                input_file = sys.argv[3]
        else:
            try:
                size_threshold_kb = int(sys.argv[1])
            except ValueError:
                print(
                    f"Invalid threshold value: {sys.argv[1]}. Using default: {size_threshold_kb} KB"
                )
            if len(sys.argv) > 2:
                input_file = sys.argv[2]

    print(
        f"Mode: {'Remove large chunks' if remove_mode else 'Filter and report large chunks'}"
    )
    print(f"Size threshold: {size_threshold_kb} KB")
    print(f"Input file: {input_file}")
    print("-" * 60)

    # Check if file exists
    if not os.path.exists(input_file):
        print(f"Error: File {input_file} not found")
        return

    if remove_mode:
        # Remove large chunks from file
        remove_large_chunks_from_file(input_file, size_threshold_kb)
    else:
        # Just filter and report large chunks
        large_chunks = filter_large_chunks(input_file, size_threshold_kb)

        print("\n" + "=" * 60)
        print(
            f"SUMMARY: Found {len(large_chunks)} total chunks larger than {size_threshold_kb} KB"
        )

        if large_chunks:
            # Save results to output file
            output_file = f"large_chunks_over_{size_threshold_kb}kb.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(large_chunks, f, ensure_ascii=False, indent=2)

            print(f"Large chunks saved to: {output_file}")

            # Print detailed statistics
            print("\nDetailed Statistics:")
            print("-" * 40)

            sizes = [chunk["size_kb"] for chunk in large_chunks]
            sizes.sort(reverse=True)

            print(f"Largest chunk: {max(sizes):.2f} KB")
            print(f"Smallest large chunk: {min(sizes):.2f} KB")
            print(f"Average size: {sum(sizes)/len(sizes):.2f} KB")

            print(f"\nTop 10 largest chunks:")
            for i, chunk in enumerate(
                sorted(large_chunks, key=lambda x: x["size_kb"], reverse=True)[:10]
            ):
                print(
                    f"{i+1:2d}. {chunk.get('chunk_id', 'Unknown ID'):<50} "
                    f"{chunk['size_kb']:>8.2f} KB"
                )

        else:
            print(f"No chunks found larger than {size_threshold_kb} KB")


if __name__ == "__main__":
    main()
