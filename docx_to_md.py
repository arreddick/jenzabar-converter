#!/usr/bin/env python3
"""
DOCX to Markdown Exam Converter
Converts Word document exams into the markdown format required by md_to_jenzabar.py.

Supports common exam formats:
- Numbered questions (1. or 1) or **1.)
- Lettered choices (A. or a. or A) or a))
- Answer lines with various formats
- True/False questions

Usage:
    python docx_to_md.py exam.docx
    python docx_to_md.py exam.docx output_folder/

Requirements:
    pip install python-docx
"""

import re
import sys
import os

try:
    from docx import Document
except ImportError:
    print("ERROR: python-docx is required.")
    print("Install it with: pip install python-docx")
    sys.exit(1)


def extract_text_from_docx(docx_path):
    """Extract all text from a DOCX file, preserving paragraph breaks."""
    doc = Document(docx_path)
    lines = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            lines.append(text)
    return lines


def detect_format(lines):
    """Detect the exam format used in the document."""
    patterns = {
        'q_bold_num': re.compile(r'^\*\*\d+[\.\)]\s'),       # **1. or **1)
        'q_plain_num': re.compile(r'^\d+[\.\)]\s'),            # 1. or 1)
        'q_paren_num': re.compile(r'^\(\d+\)\s'),              # (1)
        'choice_letter_dot': re.compile(r'^[A-Ea-e]\.\s'),     # A. or a.
        'choice_letter_paren': re.compile(r'^[A-Ea-e]\)\s'),   # A) or a)
        'choice_paren_letter': re.compile(r'^\([A-Ea-e]\)\s'), # (A) or (a)
        'answer_bold': re.compile(r'^\*\*Answer:', re.IGNORECASE),
        'answer_plain': re.compile(r'^Answer:', re.IGNORECASE),
        'answer_key': re.compile(r'^(Correct Answer|ANSWER|Key):', re.IGNORECASE),
    }

    counts = {k: 0 for k in patterns}
    for line in lines:
        for name, pat in patterns.items():
            if pat.match(line):
                counts[name] += 1

    return counts


def parse_docx_exam(lines):
    """Parse exam lines into structured question data."""
    questions = []
    current_question = None
    current_num = 0
    current_choices = []
    current_answer = None
    current_rationale = None

    # Question patterns (ordered by specificity)
    q_patterns = [
        re.compile(r'^\*?\*?(\d+)[\.\)]\s*(.+?)[\*]*$'),   # 1. or **1. or 1)
        re.compile(r'^\((\d+)\)\s*(.+)$'),                   # (1)
        re.compile(r'^Question\s+(\d+)[:\.\)]\s*(.+)$', re.IGNORECASE),  # Question 1:
    ]

    # Choice patterns
    choice_patterns = [
        re.compile(r'^([A-Ea-e])\.\s+(.+)$'),               # A. text
        re.compile(r'^([A-Ea-e])\)\s+(.+)$'),               # A) text
        re.compile(r'^\(([A-Ea-e])\)\s+(.+)$'),             # (A) text
    ]

    # Answer patterns
    answer_patterns = [
        re.compile(r'^\*?\*?Answer:\s*([A-Ea-e,\s]+|TRUE|FALSE)\*?\*?$', re.IGNORECASE),
        re.compile(r'^Correct Answer:\s*([A-Ea-e,\s]+|TRUE|FALSE)$', re.IGNORECASE),
        re.compile(r'^ANSWER:\s*([A-Ea-e,\s]+|TRUE|FALSE)$', re.IGNORECASE),
        re.compile(r'^Key:\s*([A-Ea-e,\s]+|TRUE|FALSE)$', re.IGNORECASE),
    ]

    # Rationale patterns
    rationale_patterns = [
        re.compile(r'^\*?\*?Rationale:\*?\*?\s*(.+)$', re.IGNORECASE),
        re.compile(r'^Explanation:\s*(.+)$', re.IGNORECASE),
        re.compile(r'^Feedback:\s*(.+)$', re.IGNORECASE),
        re.compile(r'^Why:\s*(.+)$', re.IGNORECASE),
    ]

    def save_question():
        nonlocal current_question, current_num, current_choices, current_answer, current_rationale
        if current_question and current_answer:
            questions.append({
                'num': current_num,
                'text': current_question,
                'choices': current_choices,
                'answer': current_answer,
                'rationale': current_rationale or ''
            })
        current_question = None
        current_choices = []
        current_answer = None
        current_rationale = None

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for question start
        q_match = None
        for pat in q_patterns:
            q_match = pat.match(line)
            if q_match:
                break

        if q_match:
            save_question()
            current_num = int(q_match.group(1))
            current_question = q_match.group(2).strip().rstrip('*')
            i += 1
            continue

        # Check for choices
        choice_match = None
        for pat in choice_patterns:
            choice_match = pat.match(line)
            if choice_match:
                break

        if choice_match:
            letter = choice_match.group(1).upper()
            text = choice_match.group(2).strip()
            current_choices.append({'letter': letter, 'text': text})
            i += 1
            continue

        # Check for answer
        answer_match = None
        for pat in answer_patterns:
            answer_match = pat.match(line)
            if answer_match:
                break

        if answer_match:
            current_answer = answer_match.group(1).strip().upper()
            i += 1
            continue

        # Check for rationale
        rat_match = None
        for pat in rationale_patterns:
            rat_match = pat.match(line)
            if rat_match:
                break

        if rat_match:
            current_rationale = rat_match.group(1).strip()
            # Continue reading multi-line rationale
            i += 1
            while i < len(lines):
                next_line = lines[i]
                # Stop if we hit a new question, separator, or answer
                is_new_q = any(p.match(next_line) for p in q_patterns)
                is_separator = next_line.strip() in ('---', '___', '***', '')
                is_answer = any(p.match(next_line) for p in answer_patterns)
                if is_new_q or is_separator or is_answer:
                    break
                current_rationale += ' ' + next_line.strip()
                i += 1
            continue

        # If we have a current question and no choices yet, this might be
        # a continuation of the question text
        if current_question and not current_choices and not current_answer:
            if line and line not in ('---', '___', '***'):
                current_question += ' ' + line.strip()

        i += 1

    # Save last question
    save_question()

    return questions


def questions_to_markdown(questions, title):
    """Convert parsed questions to the standard markdown format."""
    md_lines = [f"# {title}", ""]

    for q in questions:
        md_lines.append(f"**{q['num']}. {q['text']}**")
        md_lines.append("")

        if q['answer'].upper() in ('TRUE', 'FALSE'):
            # True/False - no choices needed
            pass
        else:
            for choice in q['choices']:
                md_lines.append(f"{choice['letter']}. {choice['text']}")
            md_lines.append("")

        md_lines.append(f"**Answer: {q['answer']}**")
        md_lines.append("")

        if q['rationale']:
            md_lines.append(f"**Rationale:** {q['rationale']}")
            md_lines.append("")

        md_lines.append("---")
        md_lines.append("")

    return '\n'.join(md_lines)


def convert_docx_to_md(docx_path, output_dir=None):
    """Convert a DOCX exam file to markdown format."""
    if not os.path.exists(docx_path):
        print(f"ERROR: File not found: {docx_path}")
        return None

    print(f"Reading: {docx_path}")
    lines = extract_text_from_docx(docx_path)
    print(f"  Extracted {len(lines)} lines of text")

    # Try to get title from first line
    title = lines[0] if lines else os.path.splitext(os.path.basename(docx_path))[0]
    # Clean up title (remove # if present)
    title = re.sub(r'^#+\s*', '', title).strip()

    questions = parse_docx_exam(lines)
    print(f"  Parsed {len(questions)} questions")

    if not questions:
        print("  WARNING: No questions found. Check that the document follows a recognizable exam format.")
        return None

    # Count types
    tf_count = sum(1 for q in questions if q['answer'].upper() in ('TRUE', 'FALSE'))
    multi_count = sum(1 for q in questions if ',' in q['answer'])
    mc_count = len(questions) - tf_count - multi_count
    print(f"  - Multiple Choice: {mc_count}")
    print(f"  - Multiple Answer: {multi_count}")
    print(f"  - True/False: {tf_count}")

    md_content = questions_to_markdown(questions, title)

    # Output path
    if output_dir is None:
        output_dir = os.path.dirname(docx_path) or '.'

    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(docx_path))[0]
    md_path = os.path.join(output_dir, f"{base_name}.md")

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"  Saved: {md_path}")
    return md_path


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python docx_to_md.py <exam.docx> [output_folder]")
        print("")
        print("Converts a Word document exam to markdown format.")
        print("The markdown file can then be converted to a Jenzabar cartridge with:")
        print("  python md_to_jenzabar.py <exam.md>")
        sys.exit(1)

    docx_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    result = convert_docx_to_md(docx_file, output_dir)
    if result:
        print(f"\nDone. Now convert to Jenzabar cartridge with:")
        print(f"  python md_to_jenzabar.py \"{result}\"")
