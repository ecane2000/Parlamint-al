# crawl.py
from __future__ import annotations

import io
from pathlib import Path
from typing import List, Optional

import fitz  # PyMuPDF
import requests
from PIL import Image
import pytesseract

from argparse import ArgumentParser

from .config import PDF_URLS
from .utils import filename_stem_from_url, normalise_text

def _filename_from_url(url: str) -> str:
    """
    Backwards-compatible wrapper around utils.filename_stem_from_url().
    """
    return filename_stem_from_url(url)


def pdf_bytes_to_text(pdf_bytes: bytes) -> str:
    """
    Extract text from PDFs coming from the Parliament website.

    Strategy per page:
      * try PyMuPDF's built-in text extraction
      * if the page is (mostly) empty, fall back to Tesseract OCR

    This is intentionally simple; tweak dpi / OCR language as needed.
    """
    text_parts: List[str] = []

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        for page in doc:
            txt = page.get_text("text") or ""
            if txt.strip():
                text_parts.append(txt)
                continue

            # No text layer – run OCR on a 300dpi bitmap
            pix = page.get_pixmap(dpi=300)
            mode = "RGB" if pix.n < 4 else "RGBA"
            img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
            ocr_txt = pytesseract.image_to_string(img)
            text_parts.append(ocr_txt)

    return "\n".join (text_parts)


def crawl_to_txt(
    inbox_root: Path,
    urls: Optional[List[str]] = None,
    do_clean: bool = True,
) -> List[Path]:
    """
    Download parliamentary PDFs listed in config.PDF_URLS (or the
    given `urls` list), convert them to TXT, and write them under:

        <inbox_root>/raw/<stem>.txt
        <inbox_root>/cleaned/<stem>.txt   (if do_clean)

    Returns a list of written TXT paths (cleaned if do_clean else raw).
    """
    urls = urls or list(PDF_URLS)
    raw_dir = inbox_root / "raw"
    cleaned_dir = inbox_root / "cleaned"

    raw_dir.mkdir(parents=True, exist_ok=True)
    if do_clean:
        cleaned_dir.mkdir(parents=True, exist_ok=True)

    written: List[Path] = []

    for url in urls:
        stem = _filename_from_url(url)
        raw_txt_path = raw_dir / f"{stem}.txt"

        resp = requests.get(url)
        resp.raise_for_status()
        text = pdf_bytes_to_text(resp.content)
        raw_txt_path.write_text(text, encoding="utf-8")

        target_path = raw_txt_path

        if do_clean:
            cleaned_text = normalise_text(text)
            cleaned_txt_path = cleaned_dir / f"{stem}.txt"
            cleaned_txt_path.write_text(cleaned_text, encoding="utf-8")
            target_path = cleaned_txt_path

        written.append(target_path)

    return written


if __name__ == "__main__":
    ap = ArgumentParser()
    ap.add_argument(
        "--out",
        default="inbox",
        type=Path,
        help="Root inbox directory (will create raw/ and cleaned/).",
    )
    ap.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip cleaned output (only raw/.txt will be written).",
    )
    args = ap.parse_args()

    paths = crawl_to_txt(Path(args.out), do_clean=not args.no_clean)
    print("Saved TXT files:")
    for p in paths:
        print("-", p)
