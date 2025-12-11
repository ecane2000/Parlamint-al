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
      - keep a newline ONLY if the next non-space char is uppercase (incl. Ç, Ë)
      - otherwise collapse that newline to a space.
    """
    # collapse spaces/tabs but keep \n
    t = re.sub(r"[^\S\r\n]+", " ", text).strip()

    def _joiner(m):
        ch = m.group(1)
        return ("\n" + ch) if (ch.isupper() or ch in "ÇË") else (" " + ch)

    # decide per newline: preserve before uppercase, else flatten
    return re.sub(r"\n[ \t]*([^\n])", _joiner, t)


def normalise_text(text: str) -> str:
    """
    British spelling alias used elsewhere in the code base.
    """
    return normalize_preserve_para_before_caps(text)
