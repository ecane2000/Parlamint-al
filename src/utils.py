# utils.py
from __future__ import annotations

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


def normalize_whitespace(text: str) -> str:
    """
    Collapse all runs of whitespace (including newlines) into a single
    space and strip leading/trailing space.
    """
    return re.sub(r"\s+", " ", text).strip()


def normalise_text(text: str) -> str:
    """
    British spelling alias used elsewhere in the code base.
    """
    return normalize_whitespace(text)


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
