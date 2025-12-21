# -*- coding: utf-8 -*-
"""
Optional crawler: fetch PDF agenda/minutes and extract text.
Requires: requests, pdfminer.six (or fallback to pure PDF copy if text layer missing).
You can skip this if you already have cleaned TXT in --inbox.
"""
from pathlib import Path
import argparse

def main():
    ap = argparse.ArgumentParser(description="Crawl PDFs to texts (optional).")
    ap.add_argument("--urls", required=True, help="Text file with one PDF URL per line")
    ap.add_argument("--pdf_out", default="pdfs", help="Folder to store PDFs")
    ap.add_argument("--txt_out", default="texts", help="Folder to store extracted TXT")
    args = ap.parse_args()

    urls_file = Path(args.urls)
    pdf_dir = Path(args.pdf_out); pdf_dir.mkdir(parents=True, exist_ok=True)
    txt_dir = Path(args.txt_out); txt_dir.mkdir(parents=True, exist_ok=True)

    try:
        import requests
    except Exception:
        raise SystemExit("Please `pip install requests pdfminer.six` to use the crawler.")

    for url in urls_file.read_text(encoding="utf-8").splitlines():
        url = url.strip()
        if not url: continue
        name = url.split("/")[-1]
        pdf_path = pdf_dir / name
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        pdf_path.write_bytes(resp.content)
        # try PDF text extraction (pdfminer)
        try:
            from pdfminer.high_level import extract_text
            txt = extract_text(str(pdf_path))
            if not txt or txt.strip() == "":
                # scanned PDF – leave TXT as empty (to be OCR’d by user pipeline), or keep a note
                txt = ""
        except Exception:
            txt = ""
        (txt_dir / (pdf_path.stem + ".txt")).write_text(txt, encoding="utf-8")

    print(f"Done. PDFs in {pdf_dir}, tentative TXT in {txt_dir}")

if __name__ == "__main__":
    main()
