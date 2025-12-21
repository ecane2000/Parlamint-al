# -*- coding: utf-8 -*-
"""
Cleaning + header block extraction from raw text.
Removes page headers/footers and page numbers, keeps paragraph breaks.
"""
import re
from pathlib import Path
from .utils import read_text, write_text, normalize_newlines, split_paragraphs

PAGE_HDR_RE = re.compile(r"^\s*={2,}\s*Page\s*\(?\d+\)?\s*={2,}\s*$", re.I | re.M)
PAGE_NUM_RE = re.compile(r"^\s*\d+\s*$", re.M)

def clean_text(raw_txt: str) -> str:
    txt = normalize_newlines(raw_txt)
    # strip obvious page headers/footers
    txt = PAGE_HDR_RE.sub("", txt)
    txt = PAGE_NUM_RE.sub("", txt)
    # common OCR fixes the user listed
    txt = txt.replace(" é", " ë").replace("É", "Ë")
    txt = txt.replace("¢", "ç").replace("Ç", "Ç")
    # Occasionally 'gé'/'gë' should be 'që' based on their note
    txt = re.sub(r"\bg[ëé]", "që", txt)
    # 'gy' -> 'gj' (heuristic; keep conservative)
    txt = re.sub(r"\bgy", "gj", txt)
    return txt

def extract_header_block(txt: str) -> dict:
    """
    Returns dict with fields required downstream:
     - eventType (lines between KUVENDI and PROCESVERBAL)
     - date (YYYY-MM-DD) and time (HH:MM) parsed from 'Tiranë, më d.m.yyyy, ora HH:MM'
     - chair_name / chair_role
     - agenda_text (between 'Rendi i ditës:' and 'Marrin pjesë:' if present)
    """
    lines = [l.strip() for l in normalize_newlines(txt).splitlines()]
    # locate markers
    try:
        i_kv = lines.index("KUVENDI")
    except ValueError:
        i_kv = -1
    try:
        i_proc = lines.index("PROCESVERBAL")
    except ValueError:
        i_proc = -1

    event_lines = []
    if i_kv >= 0 and i_proc > i_kv:
        event_lines = [l for l in lines[i_kv+1:i_proc] if l]

    # date/time line is the next non-empty after PROCESVERBAL
    date_line = ""
    if i_proc >= 0:
        for j in range(i_proc+1, min(i_proc+6, len(lines))):
            if lines[j]:
                date_line = lines[j]
                break
    # parse date/time
    date, time = "", ""
    m = re.search(r"m[ëe]\s*(\d{1,2})\.(\d{1,2})\.(\d{4}).*ora\s*(\d{1,2}:\d{2})", date_line)
    if m:
        d, mo, y, t = m.groups()
        date = f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
        time = t

    # chair
    chair_name, chair_role = "", ""
    for idx, l in enumerate(lines):
        if l.startswith("Drejton mbledhjen"):
            # next non-empty line should contain “Name – role”
            for k in range(idx+1, min(idx+5, len(lines))):
                if lines[k]:
                    parts = re.split(r"\s*[–—-]\s*", lines[k], maxsplit=1)
                    chair_name = parts[0].strip()
                    chair_role = parts[1].strip() if len(parts) > 1 else ""
                    break
            break

    # agenda
    agenda_text = ""
    try:
        i_ag = next(i for i, l in enumerate(lines) if l.startswith("Rendi i ditës"))
        # until "Marrin pjesë:" or "HAPET MBLEDHJA"
        end = None
        for key in ("Marrin pjesë", "HAPET MBLEDHJA"):
            try:
                j = next(i for i, l in enumerate(lines) if l.startswith(key) and i > i_ag)
                end = j if (end is None or j < end) else end
            except StopIteration:
                pass
        block = lines[i_ag+1:end] if end else lines[i_ag+1:i_ag+8]
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

def clean_folder(inbox: Path, cleaned: Path):
    cleaned.mkdir(parents=True, exist_ok=True)
    for p in sorted(inbox.glob("*.txt")):
        raw = read_text(p)
        out = clean_text(raw)
        write_text(cleaned / p.name, out)
