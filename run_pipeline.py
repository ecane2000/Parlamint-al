#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ParlaMint-AL Pipeline Runner:
Executes the Albanian Parliamentary TEI Corpus Pipeline in accordance with ParlaMint v5 standards.

Usage:
    python3 run_pipeline.py                          # Full pipeline: lists -> tei -> root
    python3 run_pipeline.py --stage lists            # Build listPerson and listOrg XML
    python3 run_pipeline.py --stage tei              # Process cleaned TXT -> component TEI files
    python3 run_pipeline.py --stage root             # Generate master ParlaMint-AL.xml root
    python3 run_pipeline.py --stage ana              # Run linguistic annotation (.ana)
    python3 run_pipeline.py --crawl                  # Download new PDFs first, then process
    python3 run_pipeline.py --clean                  # Clean raw_txt into inbox/cleaned first
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import main as pipeline_main


def main():
    parser = argparse.ArgumentParser(
        description="Run ParlaMint-AL Parliamentary Pipeline",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--stage",
        choices=["tei", "lists", "root", "ana", "all"],
        default="all",
        help="Pipeline stage to execute",
    )
    parser.add_argument("--crawl", action="store_true", help="Crawl and download PDFs before processing")
    parser.add_argument("--clean", action="store_true", help="Clean raw text from inbox/raw before building TEI")
    parser.add_argument("--inbox", type=str, default="inbox/cleaned", help="Input directory of cleaned transcripts")
    parser.add_argument("--out", type=str, default="out/TEI", help="Output directory for TEI XML files")
    parser.add_argument("--metadata_dir", type=str, default="metadata", help="Directory containing metadata CSV files")
    parser.add_argument("--annotator", choices=["stanza", "udpipe"], default="stanza", help="Annotator for stage 'ana'")
    parser.add_argument("--with_ana", action="store_true", help="Include .ana linguistic annotation when running stage all")

    args = parser.parse_args()

    cmd_args = [
        "--stage", args.stage,
        "--inbox", args.inbox,
        "--out", args.out,
        "--metadata_dir", args.metadata_dir,
        "--annotator", args.annotator,
    ]
    if args.crawl:
        cmd_args.append("--crawl")
    if args.clean:
        cmd_args.append("--clean")
    if args.with_ana:
        cmd_args.append("--with_ana")

    print(f"\n{'='*65}")
    print("🇦🇱  ParlaMint-AL Parliamentary Corpus Pipeline")
    print(f"{'='*65}")
    print(f"  Stage        : {args.stage}")
    print(f"  Inbox        : {args.inbox}")
    print(f"  Output       : {args.out}")
    print(f"  Metadata     : {args.metadata_dir}")
    print(f"  Crawl        : {args.crawl}")
    print(f"  Clean        : {args.clean}")
    print(f"{'='*65}\n")

    pipeline_main(cmd_args)


if __name__ == "__main__":
    main()
