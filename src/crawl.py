# -*- coding: utf-8 -*-
"""
Crawl Albanian Parliament PDFs and extract raw TXT.

Usage:
  python -m src.crawl --urls urls.txt --pdf_out pdfs --txt_out raw_txt

You can also call crawl_urls([...]) from the pipeline.
"""

import argparse
from pathlib import Path
from typing import Iterable, List
import re
import requests
from pdfminer.high_level import extract_text

# -------- utilities -----------------------------------------------------------

def _sanitize_filename_from_url(url: str) -> str:
    # take last path component, strip query, keep safe chars
    name = url.split("/")[-1].split("?")[0]
    name = re.sub(r"[^A-Za-z0-9_.%-]+", "_", name).strip("_")
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    return name

def download_pdf(url: str, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    fname = _sanitize_filename_from_url(url)
    pdf_path = out_dir / fname
    # stream to file
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(pdf_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                if chunk:
                    f.write(chunk)
    return pdf_path

def pdf_to_text(pdf_path: Path) -> str:
    try:
        txt = extract_text(str(pdf_path))  # pdfminer.six
        return txt or ""
    except Exception as e:
        # don’t crash the batch; return empty and let caller warn
        return ""

def write_txt(txt_path: Path, text: str) -> None:
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    txt_path.write_text(text, encoding="utf-8")

def download_pdf_and_extract_text(url: str, pdf_dir: Path, txt_dir: Path) -> Path:
    pdf_path = download_pdf(url, pdf_dir)
    text = pdf_to_text(pdf_path)
    stem = pdf_path.stem
    # keep some URL encoding so names stay unique; replace % with _
    stem = stem.replace("%", "_")
    txt_path = txt_dir / (stem + "_.txt")
    write_txt(txt_path, text)
    if not text.strip():
        print(f"[WARN] Empty/near-empty text for {pdf_path.name} (might be a scanned PDF; consider OCR).")
    else:
        print(f"[OK]   {pdf_path.name} -> {txt_path.name}")
    return txt_path

# -------- public API used by pipeline ----------------------------------------

def crawl_urls(urls: Iterable[str], pdf_out: str = "pdfs", txt_out: str = "raw_txt") -> List[Path]:
    pdf_dir = Path(pdf_out); pdf_dir.mkdir(parents=True, exist_ok=True)
    txt_dir = Path(txt_out); txt_dir.mkdir(parents=True, exist_ok=True)
    out_paths: List[Path] = []
    for url in urls:
        url = (url or "").strip()
        if not url or url.startswith("#"):
            continue
        try:
            out_paths.append(download_pdf_and_extract_text(url, pdf_dir, txt_dir))
        except Exception as e:
            print(f"[ERROR] {url}: {e}")
    return out_paths

# -------- CLI ----------------------------------------------------------------

def _load_urls_from_file(path: Path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(f"URLs file not found: {path}")
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")]

def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Crawl Parliament PDFs and extract raw TXT")
    ap.add_argument("--urls", required=True, help="Path to urls.txt (one PDF URL per line)")
    ap.add_argument("--pdf_out", default="pdfs", help="Directory for downloaded PDFs")
    ap.add_argument("--txt_out", default="raw_txt", help="Directory for extracted TXT")
    return ap

def main():
    args = build_arg_parser().parse_args()
    urls = _load_urls_from_file(Path(args.urls))
    crawl_urls(urls, pdf_out=args.pdf_out, txt_out=args.txt_out)

if __name__ == "__main__":
    main()
