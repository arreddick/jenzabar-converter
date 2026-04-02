# Jenzabar LMS Converter

Convert Word documents (.docx) or markdown (.md) exam files into Jenzabar/Blackboard compatible import cartridges.

Created by [Ashley Reddick](https://github.com/arreddick) | Ranken Technical College, Information Technology Department

## What It Does

Takes your exam questions (from Word or markdown files) and converts them into zip cartridge files that can be imported directly into Jenzabar (or any Blackboard-compatible LMS). Supports multiple choice, multiple answer (select all that apply), and true/false questions.

## Requirements

- Python 3.6 or higher
- For DOCX support: `pip install python-docx`
- For markdown only: no additional packages needed

## Quick Start

1. Clone this repo:
   ```
   git clone https://github.com/arreddick/jenzabar-converter.git
   cd jenzabar-converter
   ```

2. Install DOCX support (optional, only needed for Word files):
   ```
   pip install python-docx
   ```

3. Convert your exam:
   ```
   python convert.py your_exam.docx
   ```
   or
   ```
   python convert.py your_exam.md
   ```

4. Upload the generated .zip file to Jenzabar

## Usage

### One-step converter (recommended)

The `convert.py` script auto-detects your file type and handles everything:

```bash
# Convert a Word document
python convert.py exam.docx

# Convert a markdown file
python convert.py exam.md

# Specify output folder
python convert.py exam.docx output/

# Batch convert all .docx and .md files in a folder
python convert.py exams_folder/
```

### Individual scripts

If you prefer to run the steps separately:

```bash
# Step 1: Convert DOCX to markdown (only for Word files)
python docx_to_md.py exam.docx

# Step 2: Convert markdown to Jenzabar cartridge
python md_to_jenzabar.py exam.md

# Batch convert all .md files in a folder
python batch_convert.py homework_folder/

# Batch with custom output folder
python batch_convert.py homework_folder/ cartridges/
```

## Markdown Format

Write your questions in a .md file using this format:

```markdown
# Exam Title Here

**1. What is the capital of France?**

A. London
B. Berlin
C. Paris
D. Madrid

**Answer: C**

**Rationale:** Paris is the capital and largest city of France.

---

**2. Which of the following are primary colors? (Select all that apply)**

A. Red
B. Green
C. Blue
D. Yellow

**Answer: A, C, D**

**Rationale:** The primary colors are red, blue, and yellow.

---

**3. The Earth is flat.**

**Answer: FALSE**

**Rationale:** The Earth is an oblate spheroid.
```

### Rules

- Questions start with `**1.` (bold number with period)
- Choices use `A.` through `E.` (letter with period)
- Answers use `**Answer: X**` (bold, with letter)
- Rationale is optional but recommended: `**Rationale:** explanation`
- Separate questions with `---`
- The title on the first line (after `#`) becomes the assessment name in the LMS

## Supported Question Types

| Type | Format | LMS Display |
|------|--------|-------------|
| Multiple Choice | `**Answer: B**` | Radio buttons (pick one) |
| Multiple Answer | `**Answer: A, B, C**` | Checkboxes (select all that apply) |
| True/False | `**Answer: TRUE**` or `**Answer: FALSE**` | Radio buttons (True/False) |

## What Gets Generated

Each conversion produces a .zip cartridge containing:

| File | Purpose |
|------|---------|
| questions.dat | QTI XML with questions, answers, and rationales |
| imsmanifest.xml | Package manifest |
| categories.dat | Category definitions |
| itemcategories.dat | Item category mappings |
| settings.dat | Assessment creation settings |
| .bb-package-info | Package version info |

## Importing to Jenzabar

1. Log into your Jenzabar LMS
2. Navigate to Course Content Import
3. Click "Choose File" under "Upload a cartridge"
4. Select the generated .zip file
5. Click Upload

The questions will appear in your course with all answers, rationales, and correct answer markings intact.

## Example

An example quiz file is included in the `examples/` folder:

```bash
python md_to_jenzabar.py examples/example_quiz.md
```

This creates a .zip with 5 questions (3 multiple choice, 2 true/false) that you can import to verify everything works.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No .md files found" | Make sure your files have the .md extension |
| Questions not parsing | Check that questions use `**1.**` format (bold number with period) |
| Answers not detected | Ensure `**Answer: X**` format with double asterisks on both sides |
| Multi-select showing as single | Make sure answers are comma-separated: `**Answer: A, B, C**` |
| Import fails in LMS | Verify the zip was not modified after generation |
| Special characters breaking | The script escapes XML entities automatically |

## License

MIT License - free to use, modify, and distribute.

## Credits

Created by **Ashley Reddick**
Ranken Technical College, Information Technology Department
YouTube: [Ashley's IT Lab](https://www.youtube.com/@ashleysitlab)
