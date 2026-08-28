# -*- coding: utf-8 -*-
"""
Text extraction & cleaning layer for ParlaMint-AL:
- Extracts text from PDF, HTML, or raw text files.
- Cleans page numbers, headers/footers, OCR noise, and unicode quirks.
- Extracts sitting metadata headers (date, time, eventType, chair, agenda).
"""
from __future__ import annotations
import re
from pathlib import Path
from pdfminer.high_level import extract_text as pdfminer_extract

from .utils import read_text, write_text, normalize_newlines, squash_ws, guess_date_from_url

# Regex patterns for page artifacts
PAGE_HDR_RE = re.compile(r"^\s*={2,}\s*Page\s*\(?\d+\)?\s*={2,}\s*$", re.I | re.M)
PAGE_NUM_RE = re.compile(r"^\s*\d+\s*$", re.M)
RUNNING_HDR_RE = re.compile(
    r"^\s*(?:REPUBLIKA E SHQIPËRISË|KUVENDI|PROCESVERBAL)\s*$",
    re.I | re.M
)


def pdf_to_text(pdf_path: Path | str) -> str:
    """Extract raw text from a PDF file using pdfminer."""
    try:
        txt = pdfminer_extract(str(pdf_path))
        return txt or ""
    except Exception as e:
        print(f"[WARN] Error extracting from PDF {pdf_path}: {e}")
        return ""


def html_to_text(html: str) -> str:
    """Strip HTML tags and convert HTML to readable plain text."""
    # Basic regex stripper for HTML without requiring bs4
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&quot;", '"', text)
    return squash_ws(text)


def extract_text_from_file(path: Path | str) -> str:
    """Extract text based on file suffix."""
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix == ".pdf":
        return pdf_to_text(p)
    elif suffix in (".html", ".htm"):
        raw_html = read_text(p)
        return html_to_text(raw_html)
    else:
        return read_text(p)


def clean_text(raw_txt: str) -> str:
    """
    Clean raw extracted parliamentary text:
    - Normalizes line breaks
    - Strips standalone page numbers and page markers
    - Corrects known OCR character errors for Albanian
    """
    txt = normalize_newlines(raw_txt)

    # Strip page headers & page numbers
    txt = PAGE_HDR_RE.sub("", txt)
    txt = PAGE_NUM_RE.sub("", txt)

    # OCR corrections for Albanian proceedings
    txt = txt.replace(" é", " ë").replace("É", "Ë")
    txt = txt.replace("¢", "ç").replace("Ç", "Ç")
    txt = re.sub(r"\bg[ëé]", "që", txt)   # gë / gé -> që
    txt = re.sub(r"\bgy", "gj", txt)      # gy -> gj
    txt = re.sub(r"\bGy", "Gj", txt)

    # Clean double spaces on individual lines
    cleaned_lines = [re.sub(r"[ \t]+", " ", line).rstrip() for line in txt.splitlines()]
    return "\n".join(cleaned_lines)


def extract_header_block(txt: str) -> dict:
    """
    Extract parliamentary session metadata from the cleaned text header before 'HAPET MBLEDHJA'.
    Returns dictionary with:
      - eventType
      - date (YYYY-MM-DD)
      - time (HH:MM)
      - chair_name
      - chair_role
      - agenda_text
    """
    lines = [l.strip() for l in normalize_newlines(txt).splitlines()]

    # Find position of KUVENDI and PROCESVERBAL
    i_kv = -1
    i_proc = -1
    for idx, l in enumerate(lines[:50]):
        if "KUVENDI" in l.upper() and i_kv < 0:
            i_kv = idx
        if "PROCESVERBAL" in l.upper() and i_proc < 0:
            i_proc = idx

    event_lines = []
    if i_kv >= 0 and i_proc > i_kv:
        event_lines = [l for l in lines[i_kv + 1 : i_proc] if l]

    # Date and time extraction
    date, time = "", ""
    date_line = ""
    start_search = i_proc + 1 if i_proc >= 0 else 0
    for j in range(start_search, min(start_search + 10, len(lines))):
        if re.search(r"(\d{1,2})[._\-](\d{1,2})[._\-](\d{4})", lines[j]):
            date_line = lines[j]
            break

    if date_line:
        m_time = re.search(r"ora\s*(\d{1,2}:\d{2})", date_line, re.I)
        if m_time:
            time = m_time.group(1)
        date = guess_date_from_url(date_line)

    # Chair extraction ("Drejton mbledhjen:")
    chair_name, chair_role = "", ""
    for idx, l in enumerate(lines[:60]):
        if l.lower().startswith("drejton mbledhjen"):
            for k in range(idx + 1, min(idx + 5, len(lines))):
                if lines[k]:
                    parts = re.split(r"\s*[–—-]\s*", lines[k], maxsplit=1)
                    chair_name = parts[0].strip()
                    chair_role = parts[1].strip() if len(parts) > 1 else ""
                    break
            break

    # Agenda extraction (between "Rendi i ditës:" and "Marrin pjesë:" or "HAPET MBLEDHJA")
    agenda_text = ""
    try:
        i_ag = next(i for i, l in enumerate(lines[:80]) if l.lower().startswith("rendi i ditës"))
        end = None
        for key in ("marrin pjesë", "hapet mbledhja"):
            try:
                j = next(i for i, l in enumerate(lines) if l.lower().startswith(key) and i > i_ag)
                end = j if (end is None or j < end) else end
            except StopIteration:
                pass
        block = lines[i_ag + 1 : end] if end else lines[i_ag + 1 : i_ag + 10]
        agenda_text = "\n".join([b for b in block if b])
    except StopIteration:
        pass

    return {
        "eventType": "\n".join(event_lines),
        "date": date,
        "time": time,
        "chair_name": chair_name,
        "chair_role": chair_role,
        "agenda_text": agenda_text,
    }


def clean_folder(raw_dir: Path | str, cleaned_dir: Path | str) -> list[Path]:
    """Clean every *.txt in raw_dir into cleaned_dir."""
    raw_path = Path(raw_dir)
    cleaned_path = Path(cleaned_dir)
    cleaned_path.mkdir(parents=True, exist_ok=True)
    out_files: list[Path] = []

    for p in sorted(raw_path.glob("*.txt")):
        raw = read_text(p)
        out = clean_text(raw)
        target = cleaned_path / p.name
        write_text(target, out)
        out_files.append(target)

    return out_files
