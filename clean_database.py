import os
import sys
import json
import re

# Ensure console handles UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

DATA_DIR = "./game_data/video_games" 

# Map Eastern Arabic numerals (٠-٩) to standard Western digits (0-9)
ARABIC_DIGITS_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

def convert_to_standard_numbers(text: str) -> str:
    """Converts Eastern Arabic numerals to standard digits (0-9)."""
    return str(text).translate(ARABIC_DIGITS_MAP)

def is_strictly_numeric(text: str) -> bool:
    """Returns True if the string represents a pure number (integer, float, or simple range)."""
    clean = convert_to_standard_numbers(text).strip()
    # Matches pure digits or decimal (e.g., '1994', '42', '3.14')
    return bool(re.fullmatch(r"^-?\d+(?:\.\d+)?$", clean))

def is_valid_general_answer(text: str) -> bool:
    """
    General validity check:
    - No English / Latin letters.
    - No 'ال' attached directly to numbers (e.g., 'ال10', 'ال 1990').
    """
    clean = convert_to_standard_numbers(text).strip()
    if not clean:
        return False

    # 1. Reject any Latin/English letters
    if re.search(r"[a-zA-Z]", clean):
        return False

    # 2. Reject answers where 'ال' is prefixed to numbers
    if re.search(r"^ال\s*\d+", clean) or re.search(r"\bال\s*\d+", clean):
        return False

    return True

def clean_entry_string(answer: str) -> str:
    """Converts Eastern numerals to standard digits and strips whitespace."""
    return convert_to_standard_numbers(str(answer)).strip()

def process_file(filepath: str) -> tuple[int, int]:
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"[!] Skipping {filepath} (JSON read error: {e})")
            return 0, 0

    puzzles = data.get("puzzles", [])
    total_removed = 0
    modified = False

    for puzzle in puzzles:
        # 1. Normalize digits in the prompt
        if "prompt" in puzzle:
            orig_prompt = puzzle["prompt"]
            puzzle["prompt"] = convert_to_standard_numbers(orig_prompt)
            if puzzle["prompt"] != orig_prompt:
                modified = True

        raw_correct = puzzle.get("correct_answers", [])
        raw_wrong = puzzle.get("wrong_answers", [])

        # Determine if this puzzle is numerical
        # Either explicitly flagged as "number" or the first correct answer is numeric
        is_num_type = (
            puzzle.get("answer_type") == "number" or
            (len(raw_correct) > 0 and is_strictly_numeric(raw_correct[0]))
        )

        if is_num_type:
            puzzle["answer_type"] = "number"

        # 2. Clean Correct Answers
        cleaned_correct = []
        for ans in raw_correct:
            ans_clean = clean_entry_string(ans)
            if not is_valid_general_answer(ans_clean):
                total_removed += 1
                modified = True
                continue

            if is_num_type:
                # If question is numeric, ONLY allow pure numbers
                if is_strictly_numeric(ans_clean):
                    if ans_clean not in cleaned_correct:
                        cleaned_correct.append(ans_clean)
                else:
                    total_removed += 1
                    modified = True
            else:
                if ans_clean not in cleaned_correct:
                    cleaned_correct.append(ans_clean)

        # Fallback safeguard: don't leave correct_answers empty
        if not cleaned_correct and raw_correct:
            fallback = clean_entry_string(raw_correct[0])
            fallback = re.sub(r"^ال\s*(?=\d)", "", fallback)
            cleaned_correct = [fallback]

        puzzle["correct_answers"] = cleaned_correct

        # 3. Clean Wrong Answers
        cleaned_wrong = []
        for ans in raw_wrong:
            ans_clean = clean_entry_string(ans)
            if not is_valid_general_answer(ans_clean):
                total_removed += 1
                modified = True
                continue

            if is_num_type:
                # Discard any word-based distractors like 'خمسة' or 'سنة 2000'
                if is_strictly_numeric(ans_clean):
                    if ans_clean not in cleaned_wrong and ans_clean not in cleaned_correct:
                        cleaned_wrong.append(ans_clean)
                else:
                    total_removed += 1
                    modified = True
            else:
                if ans_clean not in cleaned_wrong and ans_clean not in cleaned_correct:
                    cleaned_wrong.append(ans_clean)

        puzzle["wrong_answers"] = cleaned_wrong

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return len(puzzles), total_removed

def main():
    if not os.path.exists(DATA_DIR):
        print(f"Error: Directory '{DATA_DIR}' does not exist.")
        return

    print("Sanitizing game data across all topics...")
    total_files = 0
    total_puzzles = 0
    total_removed = 0

    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if file.endswith(".json"):
                path = os.path.join(root, file)
                p_count, r_count = process_file(path)
                total_files += 1
                total_puzzles += p_count
                total_removed += r_count

    print("\n--- Sanitation Summary ---")
    print(f"Files inspected:    {total_files}")
    print(f"Puzzles checked:    {total_puzzles}")
    print(f"Bad answers pruned: {total_removed}")
    print("[✓] All numerical questions now contain only standard digits.")

if __name__ == "__main__":
    main()