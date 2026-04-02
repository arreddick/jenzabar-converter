#!/usr/bin/env python3
"""
Batch convert markdown exam files to Jenzabar LMS cartridges.
Usage: python3 batch_convert.py <input_folder> [output_folder]
"""

import os
import sys

# Ensure this script can find md_to_jenzabar.py in the same folder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from md_to_jenzabar import create_cartridge

def batch_convert(input_folder, output_folder=None):
    """Convert all markdown files in a folder to Jenzabar cartridges."""
    
    if output_folder is None:
        output_folder = os.path.join(input_folder, 'jenzabar_output')
    
    # Create output folder if needed
    os.makedirs(output_folder, exist_ok=True)
    
    # Find all markdown files
    md_files = [f for f in os.listdir(input_folder) if f.endswith('.md')]
    
    if not md_files:
        print(f"No .md files found in {input_folder}")
        return []
    
    print(f"Found {len(md_files)} markdown files to convert")
    print(f"Output folder: {output_folder}")
    print("-" * 50)
    
    results = []
    for md_file in sorted(md_files):
        md_path = os.path.join(input_folder, md_file)
        try:
            zip_path = create_cartridge(md_path, output_folder)
            results.append({'file': md_file, 'status': 'success', 'output': zip_path})
        except Exception as e:
            print(f"ERROR converting {md_file}: {e}")
            results.append({'file': md_file, 'status': 'error', 'error': str(e)})
        print()
    
    # Summary
    print("=" * 50)
    print("CONVERSION SUMMARY")
    print("=" * 50)
    success = sum(1 for r in results if r['status'] == 'success')
    failed = sum(1 for r in results if r['status'] == 'error')
    print(f"Success: {success}")
    print(f"Failed:  {failed}")
    print(f"Total:   {len(results)}")
    
    if failed > 0:
        print("\nFailed files:")
        for r in results:
            if r['status'] == 'error':
                print(f"  - {r['file']}: {r['error']}")
    
    return results

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 batch_convert.py <input_folder> [output_folder]")
        print("\nExamples:")
        print("  python3 batch_convert.py ./homework/")
        print("  python3 batch_convert.py ./homework/ ./jenzabar_cartridges/")
        sys.exit(1)
    
    input_folder = sys.argv[1]
    output_folder = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.isdir(input_folder):
        print(f"Error: {input_folder} is not a directory")
        sys.exit(1)
    
    batch_convert(input_folder, output_folder)
