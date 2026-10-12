```markdown
# Game Data Sanitizer (`clean_database.py`)

A post-processing batch processor that scans all generated JSON files in `./game_data`, removes AI-generated artifacts, standardizes numeric values, and guarantees data consistency for quiz engines.

---

## 1. What This Script Fixes

1. **Removes English/Latin Content**: Strips any choices containing Latin alphabet characters (`[a-zA-Z]`) from Arabic trivia questions.
2. **Eliminates AI Prefix Artifacts**: Discards unnatural constructions where the definite article `ال` is attached to numbers (e.g., `"ال10"`, `"ال 1998"`).
3. **Normalizes Numerals**: Converts all Eastern Arabic numerals (`٠-٩`) to standard Western digits (`0-9`) across questions, correct answers, and distractors.
4. **Enforces Numerical Type Consistency**:
   - If a question's `answer_type` is `"number"` or the target answer is numeric, all distractors (`wrong_answers`) are filtered to allow **only pure digits** (e.g., removing words like `"خمسة"` or `"سنة 2000"`).
5. **Deduplication & Cross-Check**: Removes duplicate answers and prevents correct answers from leaking into `wrong_answers`.
6. **Safety Fallback**: Ensures at least one valid, cleaned correct answer is preserved per puzzle so no question is broken or unplayable.

---

## 2. Prerequisites

- **Python 3.10+**
- Standard library modules only (`os`, `sys`, `json`, `re`). No external dependencies required.

---

## 3. Directory Structure

The script expects the generated JSON files to reside within the `./game_data` directory (matching the output structure of `web_gemini_generator.py`):

```text
project-root/
│
├── game_data/
│   ├── science/
│   │   └── عالم_البحار.json
│   ├── sports/
│   │   └── كرة_قدم.json
│   └── ...
│
└── clean_database.py

```

---

## 4. How to Run

Execute the script in your terminal from the project root:

```bash
python clean_database.py

```

---

## 5. Execution Workflow

```text
[./game_data/*.json]
        │
        ├── 1. Standardize prompt digits (٠-٩ -> 0-9)
        ├── 2. Inspect answer_type & first answer format
        │         ├── Numeric: Enforce pure digits only (0-9)
        │         └── Textual: Reject Latin letters & 'ال' attached to numbers
        ├── 3. Deduplicate entries & cross-filter distractors
        └── 4. Overwrite file in-place if modifications occurred

```

---

## 6. Console Output Example

```text
Sanitizing game data across all topics...

--- Sanitation Summary ---
Files inspected:    12
Puzzles checked:    2400
Bad answers pruned: 314
[✓] All numerical questions now contain only standard digits.

```

```

```