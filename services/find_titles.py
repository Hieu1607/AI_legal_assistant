import asyncio
import os
import re
from difflib import SequenceMatcher

from dotenv import load_dotenv
from groq import AsyncGroq, Groq

# Load environment variables
load_dotenv()


def load_titles_from_file(file_path):
    """Read all law titles from titles.txt file"""
    titles = []
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line:
                    # Remove line numbers at the beginning (e.g., "1. ")
                    title = re.sub(r"^\d+\.\s*", "", line)
                    titles.append(title)
        return titles
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []


def similarity(a, b):
    """Calculate similarity between two strings"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def extract_year_from_title(title):
    """Extract year from law title"""
    # Find years in the title (prioritize 4-digit years)
    years = re.findall(r"\b(20\d{2}|19\d{2})\b", title)
    if years:
        return int(max(years))  # Get the largest year
    return 0


def extract_base_law_name(law_name):
    """Extract basic law name (remove year, number)"""
    # Remove year and law number
    base_name = re.sub(r"\b(19|20)\d{2}\b", "", law_name)
    base_name = re.sub(r"số\s+\d+[/\w]*", "", base_name)
    base_name = re.sub(r"sửa đổi|bổ sung", "", base_name)
    return base_name.strip()


def is_same_law_type(base_name, title):
    """Check if two laws are of the same type"""
    title_base = extract_base_law_name(title)

    # Compare similarity of base names
    similarity_score = similarity(base_name.lower(), title_base.lower())
    return similarity_score > 0.7


def extract_keywords(text):
    """Extract important keywords from law name"""
    # Remove unimportant words
    stop_words = {
        "luật",
        "bộ",
        "của",
        "về",
        "và",
        "các",
        "năm",
        "số",
        "sửa",
        "đổi",
        "bổ",
        "sung",
    }

    # Split words and remove punctuation
    words = re.findall(r"\b\w+\b", text.lower())
    keywords = [word for word in words if word not in stop_words and len(word) > 2]

    return keywords


def calculate_keyword_match(keywords, title):
    """Calculate keyword match score"""
    if not keywords:
        return 0

    title_lower = title.lower()
    matched_keywords = 0

    for keyword in keywords:
        if keyword in title_lower:
            matched_keywords += 1

    return matched_keywords / len(keywords)


def group_similar_laws(candidates, llm_input):
    """Group similar laws together"""
    # Extract base law name from LLM input
    base_name = extract_base_law_name(llm_input)

    # Filter candidates that contain the base name
    filtered_candidates = []
    for candidate in candidates:
        if is_same_law_type(base_name, candidate["title"]):
            filtered_candidates.append(candidate)

    return filtered_candidates if filtered_candidates else candidates


def is_amendment_law(title):
    """Check if it is an amendment/supplemental law"""
    amendment_keywords = [
        "sửa đổi",
        "bổ sung",
        "cập nhật",
        "điều chỉnh",
        "thay đổi",
        "tu chính",
        "hiệu chỉnh",
    ]
    title_lower = title.lower()
    return any(keyword in title_lower for keyword in amendment_keywords)


def select_latest_version(candidates):
    """Select the latest version from candidates list, prioritizing original non-amendment versions"""
    # Classify candidates into 2 groups: original and amendment versions
    original_laws = []
    amendment_laws = []

    for candidate in candidates:
        if is_amendment_law(candidate["title"]):
            amendment_laws.append(candidate)
        else:
            original_laws.append(candidate)

    # Prioritize latest original version, if not available then take amendment version
    if original_laws:
        # Sort original versions by year descending, then by score descending
        sorted_originals = sorted(
            original_laws, key=lambda x: (x["year"], x["score"]), reverse=True
        )
        return sorted_originals[0]
    else:
        # If only amendment versions available, take the latest one
        sorted_amendments = sorted(
            amendment_laws, key=lambda x: (x["year"], x["score"]), reverse=True
        )
        return sorted_amendments[0]


def find_best_matches(llm_results, all_titles, threshold=0.3):
    """
    Find best matching titles from LLM results, prioritize latest version
    Args:
        llm_results: List of law names from LLM
        all_titles: List of all titles from titles.txt
        threshold: Minimum similarity threshold
    """
    matches = []

    for llm_law in llm_results:
        llm_law_clean = llm_law.strip()
        if not llm_law_clean:
            continue

        # Find all matching candidates
        candidates = []

        for title in all_titles:
            # Calculate similarity
            score = similarity(llm_law_clean, title)

            # Check if important keywords appear in title
            keywords = extract_keywords(llm_law_clean)
            keyword_match_score = calculate_keyword_match(keywords, title)

            # Combined score
            combined_score = score * 0.7 + keyword_match_score * 0.3

            if combined_score >= threshold:
                year = extract_year_from_title(title)
                candidates.append(
                    {"title": title, "score": combined_score, "year": year}
                )

        # Sort candidates by score and year (prioritize high score and recent year)
        if candidates:
            # Group candidates of the same law type
            grouped_candidates = group_similar_laws(candidates, llm_law_clean)

            if grouped_candidates:
                # Select the latest law in the group with highest score
                best_candidate = select_latest_version(grouped_candidates)
                matches.append(
                    {
                        "llm_input": llm_law_clean,
                        "exact_title": best_candidate["title"],
                        "confidence": best_candidate["score"],
                    }
                )
            else:
                matches.append(
                    {"llm_input": llm_law_clean, "exact_title": None, "confidence": 0}
                )
        else:
            matches.append(
                {"llm_input": llm_law_clean, "exact_title": None, "confidence": 0}
            )

    return matches


def get_llm_analysis(question, max_retries=3):
    """
    Call LLM to analyze question and return list of laws with improved accuracy and error handling

    Args:
        question (str): Legal question to analyze
        max_retries (int): Maximum number of retry attempts

    Returns:
        list: List of law names, empty list if error occurs
    """
    if not question or not question.strip():
        return []

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("Error: GROQ_API_KEY environment variable not set")
        return []

    # Enhanced system prompt for better accuracy
    enhanced_prompt = """Bạn là luật sư chuyên nghiệp với kinh nghiệm sâu về pháp luật Việt Nam.

NHIỆM VỤ: Phân tích câu hỏi pháp luật và xác định CHÍNH XÁC các bộ luật cần thiết.

QUY TẮC QUAN TRỌNG:
1. Chỉ trả về TÊN CHÍNH XÁC của bộ luật (không giải thích)
2. Tối đa 3 bộ luật quan trọng nhất
3. Mỗi bộ luật trên 1 dòng riêng
4. Sử dụng tên đầy đủ và chính thức của bộ luật
5. Ưu tiên bộ luật trực tiếp liên quan nhất

VÍ DỤ FORMAT:
Bộ luật Lao động 2019
Luật An toàn, vệ sinh lao động 2015
Luật Bảo hiểm xã hội 2014

CÂU HỎI CẦN PHÂN TÍCH:"""

    for attempt in range(max_retries):
        try:
            client = Groq(api_key=api_key)

            completion = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": enhanced_prompt},
                    {"role": "user", "content": question.strip()},
                ],
                temperature=0.05,  # Lower temperature for more consistent results
                max_completion_tokens=10000,  # Reduced for focused responses
                top_p=0.8,  # More focused sampling
                frequency_penalty=0.1,  # Reduce repetition
                presence_penalty=0.1,  # Encourage diversity
                stop=[
                    "\n\n",
                    "Giải thích:",
                    "Lý do:",
                ],  # Stop tokens to prevent explanations
            )

            # Get result from LLM
            result = completion.choices[0].message.content

            if not result or not result.strip():
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1}: Empty response, retrying...")
                    continue
                return []

            # Enhanced processing for better accuracy
            law_names = []
            lines = result.strip().split("\n")

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Remove common prefixes/suffixes that might appear
                line = re.sub(r"^[-•*]\s*", "", line)  # Remove bullet points
                line = re.sub(r"^\d+\.\s*", "", line)  # Remove numbers
                line = re.sub(r"^[A-Z]\)\s*", "", line)  # Remove A), B), etc.

                # Clean up the line
                line = line.strip()

                # Skip if line is too short or contains explanation keywords
                if len(line) < 10 or any(
                    keyword in line.lower()
                    for keyword in [
                        "giải thích",
                        "lý do",
                        "vì",
                        "do",
                        "tại sao",
                        "như sau",
                    ]
                ):
                    continue

                # Only add if it looks like a law name
                if any(
                    keyword in line.lower()
                    for keyword in [
                        "luật",
                        "bộ luật",
                        "nghị định",
                        "thông tư",
                        "quyết định",
                    ]
                ):
                    law_names.append(line)

                    # Limit to maximum 3 laws for better focus
                    if len(law_names) >= 3:
                        break

            if law_names:
                return law_names
            elif attempt < max_retries - 1:
                print(f"Attempt {attempt + 1}: No valid laws found, retrying...")
                continue
            else:
                return []

        except Exception as e:
            error_msg = f"Attempt {attempt + 1} failed: {str(e)}"
            if attempt < max_retries - 1:
                print(f"{error_msg}, retrying...")
                continue
            else:
                print(f"Final attempt failed: {error_msg}")
                return []

    return []


def find_exact_law_titles(question, verbose=True):
    """
    Main function to find exact names of laws from question
    Args:
        question (str): Legal question to analyze
        verbose (bool): Display detailed process or not
    Returns:
        list: List of exact names of laws
    """
    if verbose:
        print("=== ANALYZE QUESTION AND FIND EXACT LAWS ===\n")
        print(f"Question: {question}\n")

    # Step 1: Get results from LLM
    if verbose:
        print("Step 1: Analyze question using LLM...")
    llm_results = get_llm_analysis(question)

    if verbose:
        print("Results from LLM:")
        for i, law in enumerate(llm_results, 1):
            print(f"  {i}. {law}")
        print()

    # Step 2: Read list of all titles
    if verbose:
        print("Step 2: Read list of all laws from titles.txt...")

    # Get absolute path to titles.txt file (in the root directory)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    titles_path = os.path.join(project_root, "titles.txt")

    all_titles = load_titles_from_file(titles_path)
    if verbose:
        print(f"Loaded {len(all_titles)} laws from titles.txt file\n")

    # Step 3: Find best matching titles
    if verbose:
        print("Step 3: Find exact names (prioritize latest version)...")
    matches = find_best_matches(llm_results, all_titles)

    # Process results
    found_exact_titles = []

    if verbose:
        print("=== DETAILED SEARCH RESULTS ===\n")

    for i, match in enumerate(matches, 1):
        if verbose:
            print(f"{i}. From LLM: '{match['llm_input']}'")

        if match["exact_title"]:
            if verbose:
                print(f"   ✓ Found: {match['exact_title']}")
                print(f"   ✓ Confidence: {match['confidence']:.2f}")

            found_exact_titles.append(match["exact_title"])

            # Display year of selected law
            year = extract_year_from_title(match["exact_title"])
            if verbose and year > 0:
                print(f"   ✓ Year issued: {year}")
        else:
            if verbose:
                print("   ✗ No suitable match found")

        if verbose:
            print()

    # Final result summary
    if verbose:
        print("=== LIST OF EXACT LAWS NEEDED (LATEST VERSION) ===")
        if found_exact_titles:
            for i, title in enumerate(found_exact_titles, 1):
                print(f"{i}. {title}")
        else:
            print("No matching laws found.")

    return found_exact_titles
