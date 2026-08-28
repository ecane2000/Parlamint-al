# -*- coding: utf-8 -*-
"""
Source acquisition layer for ParlaMint-AL:
Download parliamentary proceeding files (PDF/HTML) and extract raw TXT into inbox/raw/.

Usage:
  python -m src.crawl --urls urls.txt --pdf_out pdfs --txt_out inbox/raw
"""
from __future__ import annotations
import argparse
import io
import re
from pathlib import Path
from typing import Iterable, List
from urllib.parse import unquote

import requests
from pdfminer.high_level import extract_text

from .config import RAW_DIR, PDF_URLS, PROJECT_ROOT
from .utils import ensure_dir, write_text, filename_stem_from_url


def _sanitize_filename_from_url(url: str) -> str:
    raw_name = url.split("/")[-1].split("?")[0]
    decoded = unquote(raw_name)
    name = re.sub(r"[^A-Za-z0-9_.%-]+", "_", decoded).strip("_")
    if not name.lower().endswith(".pdf") and not name.lower().endswith(".html"):
        name += ".pdf"
    return name


def download_file(url: str, out_path: Path) -> Path:
    """Download a file from a URL to out_path."""
    ensure_dir(out_path.parent)
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                if chunk:
                    f.write(chunk)
    return out_path


def pdf_bytes_to_text(pdf_bytes: bytes) -> str:
    """Extract plain text from in-memory PDF bytes."""
    try:
        with io.BytesIO(pdf_bytes) as stream:
            txt = extract_text(stream)
            return txt or ""
    except Exception as e:
        print(f"[WARN] Failed extracting text from PDF stream: {e}")
        return ""


def pdf_to_text(pdf_path: Path) -> str:
    """Extract plain text from a local PDF file."""
    try:
        txt = extract_text(str(pdf_path))
        return txt or ""
    except Exception as e:
        print(f"[WARN] Failed extracting text from {pdf_path}: {e}")
        return ""


def download_pdf(url: str, out_dir: Path) -> Path:
    """Download PDF to directory and return saved path."""
    fname = _sanitize_filename_from_url(url)
    pdf_path = out_dir / fname
    return download_file(url, pdf_path)


def download_and_extract_raw(url: str, pdf_dir: Path, raw_dir: Path) -> Path:
    """Download PDF and save extracted raw text to inbox/raw/."""
    pdf_path = download_pdf(url, pdf_dir)
    text = pdf_to_text(pdf_path)
    stem = pdf_path.stem
    txt_path = raw_dir / f"{stem}.txt"
    write_text(txt_path, text)
    if not text.strip():
        print(f"[WARN] Empty/near-empty text for {pdf_path.name} (possible scan; check OCR).")
    else:
        print(f"[OK]   {pdf_path.name} -> {txt_path.name}")
    return txt_path


def crawl_urls(
    urls: Iterable[str],
    pdf_out: str | Path = "pdfs",
    txt_out: str | Path = RAW_DIR,
) -> List[Path]:
    """Crawl a list of URLs, downloading PDFs and saving raw text."""
    pdf_dir = ensure_dir(pdf_out)
    txt_dir = ensure_dir(txt_out)
    out_paths: List[Path] = []

    for url in urls:
        url = (url or "").strip()
        if not url or url.startswith("#"):
            continue
        try:
            out_paths.append(download_and_extract_raw(url, pdf_dir, txt_dir))
        except Exception as e:
            print(f"[ERROR] Crawl error on {url}: {e}")

    return out_paths


def crawl_to_txt(
    inbox_root: Path | str | None = None,
    urls: list[str] | None = None,
    do_clean: bool = True,
) -> list[Path]:
    """Top-level crawl function to populate raw text files."""
    target_urls = urls if urls is not None else PDF_URLS
    raw_dir = Path(inbox_root) / "raw" if inbox_root else PROJECT_ROOT / RAW_DIR
    pdf_dir = PROJECT_ROOT / "pdfs"
    return crawl_urls(target_urls, pdf_out=pdf_dir, txt_out=raw_dir)


def _load_urls_from_file(path: Path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(f"URLs file not found: {path}")
    return [
        ln.strip()
        for ln in path.read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]


def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Crawl Parliament PDFs and extract raw TXT into inbox/raw")
    ap.add_argument("--urls", default=None, help="Path to urls.txt (one URL per line)")
    ap.add_argument("--pdf_out", default="pdfs", help="Directory for downloaded PDFs")
    ap.add_argument("--txt_out", default=RAW_DIR, help="Directory for raw extracted TXT (default: inbox/raw)")
    return ap


def main():
    args = build_arg_parser().parse_args()
    if args.urls:
        urls = _load_urls_from_file(Path(args.urls))
    else:
        urls = PDF_URLS
    crawl_urls(urls, pdf_out=args.pdf_out, txt_out=args.txt_out)


if __name__ == "__main__":
    main()
