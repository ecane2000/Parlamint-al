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
from pdfminer.layout import LAParams

from .utils import (
    read_text,
    write_text,
    normalize_newlines,
    squash_ws,
    guess_date_from_url,
    reconstruct_broken_lines,
    RE_SPEAKER_LINE_START,
)

# Regex patterns for page artifacts
PAGE_HDR_RE = re.compile(r"^\s*={2,}\s*Page\s*\(?\d+\)?\s*={2,}\s*$", re.I | re.M)
PAGE_NUM_RE = re.compile(r"^\s*\d+\s*$", re.M)
RUNNING_HDR_RE = re.compile(
    r"^\s*(?:REPUBLIKA E SHQIPËRISË|KUVENDI|PROCESVERBAL)\s*$",
    re.I | re.M
)
PLENARY_RUNNING_HDR_RE = re.compile(
    r"^\s*(?:Kuvendi i Shqipërisë\s*\n+)?\s*LEGJISLATURA\s+[IVXLCDM]+\s*[–—-]\s*SEANCA\b[^\n]*$",
    re.I | re.M,
)


def _ocr_pdf_fallback(pdf_path: Path | str) -> str:
    """Attempt OCR extraction on a scanned PDF if pytesseract + fitz/pdf2image are available."""
    try:
        import pytesseract
        from PIL import Image
        import io
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(str(pdf_path))
            pages_txt = []
            for page in doc:
                pix = page.get_pixmap(dpi=250)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                pages_txt.append(pytesseract.image_to_string(img, lang="sqi+eng"))
            return "\n\n".join(pages_txt)
        except ImportError:
            from pdf2image import convert_from_path
            images = convert_from_path(str(pdf_path), dpi=250)
            return "\n\n".join(pytesseract.image_to_string(im, lang="sqi+eng") for im in images)
    except Exception:
        return ""


def pdf_to_text(pdf_path: Path | str) -> str:
    """Extract raw text from a PDF file using pdfminer (with tuned LAParams) and OCR fallback."""
    try:
        laparams = LAParams(line_margin=1.5, char_margin=2.0, word_margin=0.1)
        txt = pdfminer_extract(str(pdf_path), laparams=laparams) or ""
        if len(txt.strip()) < 50:
            ocr_txt = _ocr_pdf_fallback(pdf_path)
            if len(ocr_txt.strip()) > len(txt.strip()):
                txt = ocr_txt
        return txt
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


def curate_ocr_and_punctuation(txt: str) -> str:
    """
    Apply OCR character, word, and punctuation normalization for Albanian parliamentary texts.
    """
    # 1. Character-level OCR fixes
    txt = txt.replace("\x0c", "\n").replace("\u00a0", " ")
    txt = txt.replace(" é", " ë").replace("É", "Ë")
    txt = txt.replace("¢", "ç").replace("Ç", "Ç")
    txt = re.sub(r"\bg[ëé]", "që", txt)   # gë / gé -> që
    txt = re.sub(r"\bgy", "gj", txt)      # gy -> gj
    txt = re.sub(r"\bGy", "Gj", txt)

    # 2. Word-level OCR / stenographic typos
    txt = re.sub(r"\bts\b", "të", txt)
    txt = re.sub(r"\bdukë\b", "duke", txt)
    txt = re.sub(r"\bNdërhyre\b", "Ndërhyrje", txt)
    txt = re.sub(r"\bndërhyre\b", "ndërhyrje", txt)
    txt = re.sub(r"\bpika(\d+)\b", r"pika \1", txt)
    txt = re.sub(r"\bNeni(\d+)\b", r"Neni \1", txt)

    # 3. Punctuation curation
    # Remove spaces before comma, semicolon, colon, exclamation, or question mark
    txt = re.sub(r"[ \t]+([,;!?])", r"\1", txt)
    # Remove spaces before a single period (not ellipsis '...')
    txt = re.sub(r"(?<!\.)[ \t]+\.(?!\.)", ".", txt)
    # Ensure a space after comma between letters (e.g. 'e,e' -> 'e, e', 't,q' -> 't, q')
    txt = re.sub(r"(?<=[A-Za-zÇËçë]),(?=[A-Za-zÇËçë])", ", ", txt)
    # Ensure space between closing quote and opening parenthesis: ”( -> ” (
    txt = re.sub(r"([”\"])\(", r"\1 (", txt)
    # Fix stray unmatched closing parenthesis at end of sentence when no '(' precedes it in the sentence
    txt = re.sub(r"\bnë mënyrë sistematike\)\.", "në mënyrë sistematike.", txt)

    return txt


def clean_text(raw_txt: str) -> str:
    """
    Clean raw extracted parliamentary text:
    - Normalizes line breaks and strips form feeds
    - Strips standalone page numbers, page markers, and running headers
    - Corrects known OCR character, word, and punctuation errors for Albanian
    - Reconstructs broken lines in the transcript body so sentences are not fragmented
    """
    txt = normalize_newlines(raw_txt).replace("\x0c", "\n")

    # Strip page headers, running headers, & standalone page numbers
    txt = PAGE_HDR_RE.sub("", txt)
    txt = PLENARY_RUNNING_HDR_RE.sub("", txt)
    txt = re.sub(r"^\s*Kuvendi i Shqipërisë\s*$", "", txt, flags=re.I | re.M)
    txt = PAGE_NUM_RE.sub("", txt)

    # Curate OCR character, word, and punctuation errors
    txt = curate_ocr_and_punctuation(txt)

    # Clean double spaces on individual lines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in txt.splitlines()]
    lines = [l for l in lines if l]
    if not lines:
        return ""

    # Locate where the body starts (at 'HAPET MBLEDHJA' or first speaker after 'Rendi i ditës:')
    split_idx = None
    for i, l in enumerate(lines):
        if l.upper().startswith("HAPET MBLEDHJA"):
            split_idx = i
            break

    if split_idx is None:
        # Look for 'Rendi i ditës:' then find the first speaker cue after it
        i_rendi = None
        for i, l in enumerate(lines[:60]):
            if l.lower().startswith("rendi i ditës"):
                i_rendi = i
                break
        search_from = (i_rendi + 1) if i_rendi is not None else 0
        for i in range(search_from, len(lines)):
            if RE_SPEAKER_LINE_START.match(lines[i]):
                split_idx = i
                break

    if split_idx is not None:
        header_part = "\n".join(lines[:split_idx])
        body_part = reconstruct_broken_lines("\n".join(lines[split_idx:]))
        body_part = curate_ocr_and_punctuation(body_part)
        return header_part + "\n\n" + body_part

    reconstructed = reconstruct_broken_lines("\n".join(lines))
    return curate_ocr_and_punctuation(reconstructed)


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

    # Chair extraction ("Drejton mbledhjen:", "Seancën e drejton", "Drejton seancën")
    chair_name, chair_role = "", ""
    for idx, l in enumerate(lines[:60]):
        low_l = l.lower()
        if any(cue in low_l for cue in ("drejton mbledhjen", "seancën e drejton", "seancen e drejton", "drejton seancën", "drejton seancen")):
            # Check if name is on the same line after colon
            if ":" in l:
                after_colon = l.split(":", 1)[1].strip()
                if after_colon:
                    parts = re.split(r"\s*[–—-]\s*", after_colon, maxsplit=1)
                    chair_name = parts[0].strip()
                    chair_role = parts[1].strip() if len(parts) > 1 else ""
                    if chair_name:
                        break

            # Search subsequent lines
            for k in range(idx + 1, min(idx + 6, len(lines))):
                if lines[k]:
                    line_k = lines[k].strip()
                    if line_k.startswith("(") and line_k.endswith(")"):
                        continue
                    if line_k.upper() in (
                        "KRYETARI I KUVENDIT", "KRYETARJA E KUVENDIT", "KRYETAR I KUVENDIT",
                        "KRYETAR", "KRYETARJA", "NËNKRYETAR", "NËNKRYETARJA", "NËNKRYETARI I KUVENDIT",
                    ):
                        chair_role = line_k
                        for m_idx in range(k + 1, min(k + 4, len(lines))):
                            cand = lines[m_idx].strip()
                            if cand and not (cand.startswith("(") and cand.endswith(")")):
                                chair_name = cand
                                break
                        break
                    parts = re.split(r"\s*[–—-]\s*", line_k, maxsplit=1)
                    chair_name = parts[0].strip()
                    chair_role = parts[1].strip() if len(parts) > 1 else ""
                    break
            if chair_name:
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
