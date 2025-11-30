import io
import re
import fitz  # PyMuPDF
import requests
from PIL import Image
import pytesseract
from pathlib import Path
from argparse import ArgumentParser
from urllib.parse import urlparse
from .config import PDF_URLS  # reuse your existing list of source URLs

# Optional: set tesseract path on Windows if needed (keep empty otherwise)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def _filename_from_url(url: str) -> str:
    """Create a stable base name for output files."""
    name = urlparse(url).path.split('/')[-1] or "document"
    name = name.replace('%20', '_').replace('%C3%AB', 'ë')
    # strip extension to produce a .txt basename
    if name.lower().endswith('.pdf'):
        name = name[:-4]
    return name if name else "document"

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extract text from a PDF. Prefer digital text via PyMuPDF; fallback to OCR per page.
    (Based on the OCR pattern you use in pdf_xml.py.)
    """
    text_chunks = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    for page_idx in range(len(doc)):
        page = doc[page_idx]
        # Try digital text first
        page_text = page.get_text("text") or ""
        if page_text.strip():
            text_chunks.append(page_text)
            continue
        # Fallback: render page → OCR
        pix = page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        try:
            ocr = pytesseract.image_to_string(img, lang="sqi+eng")
        except Exception:
            ocr = pytesseract.image_to_string(img, lang="eng")
        text_chunks.append(ocr)
    doc.close()
    return "\n\n".join(chunk.strip() for chunk in text_chunks if chunk and chunk.strip())

_rx_header = re.compile(r"^\s*=+\s*Page\s*\(\s*\d+\s*\)\s*=+\s*$", re.IGNORECASE)
_rx_lone_pagenum = re.compile(r"^\s*\d+\s*$")
_rx_pagebreak = re.compile(r"\f|^\s*(?:-{3,}\s*Page\s*break\s*-{3,})\s*$", re.IGNORECASE)
_rx_ge = re.compile(r"\bg([ëé])", re.IGNORECASE)   # gé/gë at word start → që
_rx_gy = re.compile(r"\bgy", re.IGNORECASE)        # gy... → gj...

def normalise_text(s: str) -> str:
    """
    Apply the requested cleanups:
     - remove headers/footers & page breaks
     - character fixes and OCR misreads
    """
   # Split into lines to filter headers/footers
    lines = []
    for line in s.splitlines():
        if _rx_header.match(line):
            continue
        if _rx_lone_pagenum.match(line):
            continue
        if _rx_pagebreak.search(line):
            continue
        lines.append(line)
    s2 = "\n".join(lines)

    # Replace characters
    s2 = s2.replace("¢", "ç")
    s2 = s2.replace("é", "ë")

    # Fix gé/gë → që (preserve case of the vowel)
    def _fix_ge(m):
        vowel = m.group(1)
        # After earlier replacement, both 'é' and 'ë' should be ë
        return "q" + ("ë" if vowel.lower() in ("ë", "é") else vowel)
    s2 = _rx_ge.sub(_fix_ge, s2)

    # Fix gy → gj at word start (gyysm* → gjysm*)
    s2 = _rx_gy.sub("gj", s2)

    return s2

def _download_text(url: str) -> str:
    """Download plain text from a URL that serves .txt."""
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    # Try decode as UTF-8, fallback to latin-1 if needed
    try:
        return r.content.decode("utf-8")
    except UnicodeDecodeError:
        return r.content.decode("latin-1")

def crawl_to_txt(inbox_dir: Path, do_clean: bool = True) -> list[Path]:
    """
    For each URL in PDF_URLS:
      - if .txt → download as-is
      - if .pdf → extract text (digital or OCR)
    Save RAW to inbox/raw/*.txt and (optionally) CLEANED to inbox/cleaned/*.txt
    """
    raw_dir = inbox_dir / "raw"
    cleaned_dir = inbox_dir / "cleaned"
    raw_dir.mkdir(parents=True, exist_ok=True)
    if do_clean:
        cleaned_dir.mkdir(parents=True, exist_ok=True)

    written = []
    for url in PDF_URLS:
        base = _filename_from_url(url)
        out_raw = raw_dir / f"{base}.txt"

        if url.lower().endswith(".txt"):
            text = _download_text(url)
        else:
            # Assume PDF → text
            r = requests.get(url, timeout=90)
            r.raise_for_status()
            text = extract_text_from_pdf_bytes(r.content)

        out_raw.write_text(text, encoding="utf-8")
        written.append(out_raw)

        if do_clean:
            cleaned = normalise_text(text)
            (cleaned_dir / f"{base}.txt").write_text(cleaned, encoding="utf-8")

    return written

if __name__ == "__main__":
    ap = ArgumentParser()
    ap.add_argument("--out", default="inbox", help="Root inbox directory (will create raw/ and cleaned/)")
    ap.add_argument("--no-clean", action="store_true", help="Skip cleaned output")
    args = ap.parse_args()
    paths = crawl_to_txt(Path(args.out), do_clean=not args.no_clean)
    print("Saved TXT files:", *map(str, paths), sep="\n- ")
