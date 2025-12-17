# utils.py
from __future__ import annotations
from typing import Optional, Tuple, List
import re
from datetime import datetime
from urllib.parse import urlparse


# Match dd.mm.yyyy patterns as used in Albanian parliament file names
DATE_RE = re.compile(r"(\d{2})[.](\d{2})[.](\d{4})")


def guess_date_from_url(text: str) -> str:
    """
    Extract an ISO date (YYYY-MM-DD) from a URL or file stem that
    contains dd.mm.yyyy. If no date is found we fall back to 'today'
    so the pipeline never crashes, but you really want the date to be
    present in the filenames or keep a proper metadata CSV.
    """
    m = DATE_RE.search(text)
    if m:
        d, mth, y = m.groups()
        return f"{y}-{mth}-{d}"
    return datetime.today().strftime("%Y-%m-%d")

def _ascii_norm(s: str) -> str:
    """Lowercase and fold Albanian accents for matching."""
    return (
        s.lower()
         .replace("ë", "e")
         .replace("ç", "c")
         .strip()
    )


def filename_stem_from_url(url: str) -> str:
    """
    Create a stable stem used by the crawler for TXT names, so we can map
    TXT files back to their source URLs.

    We keep diacritics in UTF-8 (e.g. ë) as ParlaMint expects UTF-8
    filenames and IDs.
    """
    name = urlparse(url).path.split("/")[-1] or "document"
    # Decode the most common escapes in the current sample; for more
    # general handling you could run urllib.parse.unquote
    name = name.replace("%20", "_")
    # Leave 'ë' etc. in place
    if name.lower().endswith(".pdf"):
        name = name[:-4]
    return name or "document"

def extract_meeting_title_from_cleaned(text: str, max_scan_lines: int = 80) -> Optional[Tuple[str, List[int]]]:
    """
    From a cleaned TXT, detect title lines between:
      REPUBLIKA E SHQIPËRISË
      KUVENDI
      <ONE OR MORE TITLE LINES>
      PROCESVERBAL
    Returns (title_string, line_indexes_used) or None if not found.
    Supports multi-line titles (e.g., two commissions).
    """
    lines = text.splitlines()
    scan = lines[:max_scan_lines]
    # Normalize for matching
    norm = [_ascii_norm(x) for x in scan]

    def is_header_rep(idx): return "republika e shqiperise" == norm[idx]
    def is_header_kuv(idx): return "kuvendi" == norm[idx]
    def is_procesverbal(idx): return "procesverbal" == norm[idx].replace(" ", "")

    i = 0
    while i < len(scan) - 3:  # need at least 4 lines ahead
        if is_header_rep(i) and is_header_kuv(i+1):
            # collect title lines until we hit PROCESVERBAL
            j = i + 2
            title_lines: List[str] = []
            used_idx: List[int] = [i, i+1]
            while j < len(scan):
                if is_procesverbal(j):
                    # stop before PROCESVERBAL
                    used_idx.append(j)
                    title = "\n".join([lines[k].strip() for k in range(i+2, j) if lines[k].strip()])
                    if title:
                        # include all indices used: header, title block, PROCESVERBAL
                        used_idx.extend(list(range(i+2, j)))
                        return (title, sorted(set(used_idx)))
                    break
                j += 1
        i += 1
    return None

def strip_detected_header_block(text: str, used_line_indexes: List[int]) -> str:
    """Remove the header lines used to form the title from the text body."""
    lines = text.splitlines()
    keep = [ln for idx, ln in enumerate(lines) if idx not in set(used_line_indexes)]
    # Remove possible leading empty lines after strip
    while keep and not keep[0].strip():
        keep.pop(0)
    return "\n".join(keep)

def normalize_preserve_para_before_caps(text: str) -> str:
    """
    Normalize horizontal whitespace but:
      - if the next non-space char on the next line is uppercase (incl. Ç, Ë),
        keep a PARAGRAPH break (blank line) before it,
      - otherwise collapse that newline to a space.

    Effect:
      - normal lines are joined into running text,
      - lines starting with a capital letter start a new paragraph that
        segment.py can detect via blank lines (\n\n).
    """
    # collapse spaces/tabs but keep \n
    t = re.sub(r"[^\S\r\n]+", " ", text).strip()

    def _joiner(m):
        ch = m.group(1)
        return ("\n" + ch) if (ch.isupper() or ch in "ÇË") else (" " + ch)

    # decide per newline: preserve before uppercase, else flatten
    return re.sub(r"\n[ \t]*([^\n])", _joiner, t)

def normalize_text(text: str) -> str:
    """
    Pipeline entry point:
      - remove page-number artefacts
      - then normalize whitespace / paragraph breaks.
    """
    text = remove_page_numbers(text)
    return normalize_preserve_para_before_caps(text)

# British spelling alias used by crawl.py
def normalise_text(text: str) -> str:
    return normalize_text(text)

_RE_YMD = re.compile(r"(?P<y>\d{4})[-_](?P<m>\d{2})[-_](?P<d>\d{2})")
_RE_DMY = re.compile(r"(?P<d>\d{2})[.\-/_](?P<m>\d{2})[.\-/_](?P<y>\d{4})")
_RE_YYYYMMDD = re.compile(r"(?P<y>\d{4})(?P<m>\d{2})(?P<d>\d{2})")

def _safe_date(y: str, m: str, d: str) -> str | None:
    try:
        return datetime(int(y), int(m), int(d)).strftime("%Y-%m-%d")
    except ValueError:
        return None
    

def _extract_date(s: str) -> str | None:
    if not s:
        return None
    m = _RE_YMD.search(s)
    if m:
        got = _safe_date(m["y"], m["m"], m["d"])
        if got: return got
    m = _RE_DMY.search(s)
    if m:
        got = _safe_date(m["y"], m["m"], m["d"])
        if got: return got
    m = _RE_YYYYMMDD.search(s)
    if m:
        got = _safe_date(m["y"], m["m"], m["d"])
        if got: return got
    return None

def normalize_for_segmentation(text: str) -> str:
    # Replace NBSPs with regular spaces so \s matches:
    text = text.replace('\u00A0', ' ').replace('\u202F', ' ')
    # Unify dash characters
    text = (text
            .replace('\u2014', '–')   # em dash → en dash
            .replace('\u2212', '-')   # minus sign → hyphen
    )
    # IMPORTANT: do NOT collapse single \n into spaces; keep paragraph breaks.
    # If you previously had something like re.sub(r'\n{1,}', ' ', ...), remove it.
    return text

def parse_date_from_filename_or_text(stem: str, text: str | None = None) -> str:
    """
    Try to find a date for this document. Preference order:
      1) filename/stem (e.g., ParlaMint-AL_2025-10-08, 08.10.2025, 20251008)
      2) first date-like pattern in the text
      3) fallback to today's date
    Returns ISO date 'YYYY-MM-DD'.
    """
    # 1) stem
    got = _extract_date(stem)
    if got:
        return got
    # 2) text
    if text:
        got = _extract_date(text[:2000]) or _extract_date(text)  # quick scan first
        if got:
            return got
    # 3) fallback
    return datetime.today().strftime("%Y-%m-%d")

import re
# ... rest of imports already there

def remove_page_numbers(text: str) -> str:
    """
    Remove page numbers from a cleaned text.

    Rules:
    1) Drop lines that consist only of digits + whitespace (e.g. " 2   ").
    2) If a line starts with optional spaces, then digits, then AT LEAST two spaces,
       and then some text, strip off the number + spaces and keep the text.
       Example: " 16    edhe një herë..." -> "edhe një herë..."
    """
    out_lines = []
    for line in text.splitlines():
        stripped = line.strip()

        # Case 1: line is just a number (page number alone)
        if stripped.isdigit():
            continue

        # Case 2: page number at line start, then 2+ spaces, then text
        m = re.match(r"^(\s*)(\d{1,3})(\s{2,})(.+)$", line)
        if m:
            leading_ws, num, spaces, rest = m.groups()
            cleaned_line = leading_ws + rest.lstrip()
            out_lines.append(cleaned_line)
        else:
            out_lines.append(line)

    return "\n".join(out_lines)


