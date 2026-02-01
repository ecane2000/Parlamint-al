#!/usr/bin/env python3
"""
Complete pipeline runner: crawl PDFs, extract text, clean, and convert to TEI XML.

This script runs the full pipeline in the correct order:
1. Crawl PDFs from parlament.al (optional, if --crawl is set)
2. Extract text from PDFs
3. Clean raw text files
4. Convert to TEI XML

Usage:
    python3 run_pipeline.py              # Process existing raw_txt files
    python3 run_pipeline.py --crawl      # Crawl new PDFs first, then process
    python3 run_pipeline.py --limit 5    # Crawl only 5 PDFs
"""
import sys
import argparse
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and print status."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    
    if result.returncode != 0:
        print(f"\n❌ Error: {description} failed with exit code {result.returncode}")
        return False
    
    print(f"\n✅ {description} completed successfully")
    return True

def main():
    parser = argparse.ArgumentParser(description="Run the complete ParlaMint-AL pipeline")
    parser.add_argument("--crawl", action="store_true", help="Crawl new PDFs before processing")
    parser.add_argument("--limit", type=int, default=10, help="Number of PDFs to crawl (default: 10)")
    parser.add_argument("--out", type=str, default="out", help="Output directory (default: out)")
    
    args = parser.parse_args()
    
    # Step 1: Optional crawl
    if args.crawl:
        if not run_command(
            ["python3", "src/crawl_pdfs_selenium.py", "--limit", str(args.limit)],
            f"Step 1: Crawling {args.limit} PDFs from parlament.al"
        ):
            return 1
    
    # Step 2: Run pipeline with cleaning
    if not run_command(
        ["python3", "-m", "src.pipeline", "--clean_from", "raw_txt", "--out", args.out],
        "Step 2: Processing PDFs (extract → clean → TEI XML)"
    ):
        return 1
    
    print(f"\n{'='*60}")
    print("✅ Pipeline completed successfully!")
    print(f"{'='*60}")
    print(f"\nResults:")
    print(f"  - PDFs: pdfs/")
    print(f"  - Raw text: raw_txt/")
    print(f"  - Cleaned text: texts/")
    print(f"  - TEI XML: {args.out}/plain/")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
