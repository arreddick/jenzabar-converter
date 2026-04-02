#!/usr/bin/env python3
"""
One-step converter: DOCX or MD to Jenzabar LMS cartridge.
Detects the input file type and runs the appropriate conversion pipeline.

Usage:
    python convert.py exam.docx              # DOCX to Jenzabar cartridge
    python convert.py exam.md                # MD to Jenzabar cartridge
    python convert.py exam.docx output/      # With output folder
    python convert.py folder/                # Batch convert all .docx and .md files
"""

import sys
import os

def main():
    if len(sys.argv) < 2:
        print("Jenzabar LMS Converter")
        print("=" * 40)
        print("")
        print("Usage:")
        print("  python convert.py <file.docx>       Convert a Word document")
        print("  python convert.py <file.md>          Convert a markdown file")
        print("  python convert.py <folder/>          Batch convert all files in a folder")
        print("  python convert.py <file> <output/>   Specify output folder")
        print("")
        print("Supported input formats: .docx, .md")
        print("Output: Jenzabar/Blackboard compatible .zip cartridge")
        sys.exit(1)

    input_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    # Batch mode: input is a folder
    if os.path.isdir(input_path):
        batch_convert(input_path, output_dir)
        return

    # Single file mode
    if not os.path.exists(input_path):
        print(f"ERROR: File not found: {input_path}")
        sys.exit(1)

    ext = os.path.splitext(input_path)[1].lower()

    if ext == '.docx':
        convert_docx(input_path, output_dir)
    elif ext == '.md':
        convert_md(input_path, output_dir)
    else:
        print(f"ERROR: Unsupported file type: {ext}")
        print("Supported: .docx, .md")
        sys.exit(1)


def convert_docx(docx_path, output_dir):
    """Convert DOCX to markdown, then to Jenzabar cartridge."""
    from docx_to_md import convert_docx_to_md
    from md_to_jenzabar import create_cartridge

    print(f"Step 1/2: Converting DOCX to markdown...")
    md_path = convert_docx_to_md(docx_path, output_dir)
    if not md_path:
        print("ERROR: DOCX conversion failed.")
        sys.exit(1)

    print(f"\nStep 2/2: Converting markdown to Jenzabar cartridge...")
    zip_path = create_cartridge(md_path, output_dir)
    print(f"\nDone. Cartridge ready: {zip_path}")


def convert_md(md_path, output_dir):
    """Convert markdown to Jenzabar cartridge."""
    from md_to_jenzabar import create_cartridge

    print(f"Converting markdown to Jenzabar cartridge...")
    zip_path = create_cartridge(md_path, output_dir)
    print(f"\nDone. Cartridge ready: {zip_path}")


def batch_convert(folder_path, output_dir):
    """Batch convert all .docx and .md files in a folder."""
    if output_dir is None:
        output_dir = os.path.join(folder_path, 'jenzabar_output')

    os.makedirs(output_dir, exist_ok=True)

    files = []
    for f in sorted(os.listdir(folder_path)):
        ext = os.path.splitext(f)[1].lower()
        if ext in ('.docx', '.md'):
            files.append(f)

    if not files:
        print(f"No .docx or .md files found in {folder_path}")
        return

    print(f"Found {len(files)} files to convert")
    print(f"Output folder: {output_dir}")
    print("-" * 50)

    success = 0
    failed = 0

    for f in files:
        full_path = os.path.join(folder_path, f)
        ext = os.path.splitext(f)[1].lower()
        print(f"\n--- {f} ---")
        try:
            if ext == '.docx':
                convert_docx(full_path, output_dir)
            else:
                convert_md(full_path, output_dir)
            success += 1
        except Exception as e:
            print(f"ERROR: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print("CONVERSION SUMMARY")
    print("=" * 50)
    print(f"Success: {success}")
    print(f"Failed:  {failed}")
    print(f"Total:   {len(files)}")


if __name__ == '__main__':
    main()
