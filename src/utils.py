# -*- coding: utf-8 -*-
"""
Small reusable helpers used across the ParlaMint-AL repository.
"""
from __future__ import annotations
import re
from pathlib import Path
from urllib.parse import unquote

# Dash variations
UNICODE_DASHES = r"[–—-]"
SPACE_DASH_SPACE = re.compile(rf"\s*{UNICODE_DASHES}\s*")
BLANK_PARA_RE = re.compile(r"\n\s*\n", flags=re.UNICODE)
RE_VALID_PUNCT_END = re.compile(r"[.?!:;»\"]\s*$")


def ensure_dir(path: Path | str) -> Path:
    """Ensure directory exists, creating parents if necessary."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_text(path: Path | str) -> str:
    """Read a text file with UTF-8 encoding, ignoring decoding errors."""
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path | str, text: str) -> None:
    """Write text to file with UTF-8 encoding, creating parent directories."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def normalize_newlines(text: str) -> str:
    """Standardize CRLF and CR newlines to LF."""
    return (text or "").replace("\r\n", "\n").replace("\r", "\n")


def squash_ws(s: str) -> str:
    """Collapse internal spaces/tabs to a single space while keeping newlines."""
    return re.sub(r"[ \t]+", " ", s or "")


def normalize_whitespace(text: str) -> str:
    """Normalize all whitespace runs into single spaces and trim."""
    return re.sub(r"\s+", " ", text or "").strip()


def normalise_text(text: str, preserve_paragraphs: bool = False) -> str:
    """Normalize text encoding and whitespace."""
    if not text:
        return ""
    txt = normalize_newlines(text)
    if preserve_paragraphs:
        paras = [squash_ws(p.strip()) for p in txt.split("\n\n") if p.strip()]
        return "\n\n".join(paras)
    return normalize_whitespace(txt)


normalize_text = normalise_text


def count_words(text: str) -> int:
    """Count lexical words in text."""
    if not text:
        return 0
    # Split on whitespace after removing XML tags if present
    clean = re.sub(r"<[^>]+>", " ", text)
    tokens = [t for t in re.split(r"\s+", clean) if t.strip()]
    return len(tokens)


def safe_xml_text(text: str) -> str:
    """Remove control characters that are invalid in XML 1.0."""
    if not text:
        return ""
    # Remove XML-invalid characters (ASCII < 32 except \t, \n, \r)
    return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)


def guess_date_from_url(text: str) -> str:
    """
    Attempt to extract an ISO date (YYYY-MM-DD) from a URL or filename.
    Supports formats like dd.mm.yyyy, dd_mm_yyyy, dd.mm._yyyy, yyyymmdd, etc.
    """
    if not text:
        return ""
    decoded = unquote(text)

    # 1. Matches like 17.10.2025, 06.10.2025, 07.10._2025, 4.12.2025
    m = re.search(r"(\d{1,2})[\s._\-]+(\d{1,2})[\s._\-]+(\d{4})", decoded)
    if m:
        d, mo, y = m.groups()
        if 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
            return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"

    # 2. Matches like 2025-10-17 or 2025_10_17
    m2 = re.search(r"(\d{4})[\s._\-]+(\d{1,2})[\s._\-]+(\d{1,2})", decoded)
    if m2:
        y, mo, d = m2.groups()
        if 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
            return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"

    # 3. Matches like timestamp at beginning of filename e.g. 20251024...
    m3 = re.search(r"\b(20\d{2})(\d{2})(\d{2})\b", decoded)
    if m3:
        y, mo, d = m3.groups()
        if 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
            return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"

    return ""


def filename_stem_from_url(url: str) -> str:
    """Extract a sanitized, legible filename stem from a URL."""
    if not url:
        return "doc"
    raw_name = url.split("/")[-1].split("?")[0]
    decoded = unquote(raw_name)
    stem = Path(decoded).stem
    # Replace unsafe characters
    cleaned = re.sub(r"[^A-Za-z0-9_.%-]+", "_", stem).strip("_")
    return cleaned or "doc"


def normalize_name(name: str) -> str:
    """Normalize a person or speaker name for indexing and lookups."""
    return re.sub(r"\s+", " ", (name or "").strip()).lower()


def mint_person_id(full_name: str) -> str:
    """
    Create a stable, ParlaMint-style person id from a name.
    e.g. 'Agron Gjekmarkaj' -> 'AL_PERS_AgronGjekmarkaj'
    """
    full_name = (full_name or "").strip()
    parts = re.split(r"\s+", full_name)
    if len(parts) >= 2:
        surname = re.sub(r"[^A-Za-zÇËçëÀ-ÖØ-öø-ÿ]", "", parts[-1])
        forename = re.sub(r"[^A-Za-zÇËçëÀ-ÖØ-öø-ÿ]", "", parts[0])
        base = f"{forename}{surname}"
    else:
        base = re.sub(r"[^A-Za-zÇËçëÀ-ÖØ-öø-ÿ]", "", full_name) or "Unknown"
    return f"AL_PERS_{base}"


def split_paragraphs(text: str) -> list[str]:
    """Split on blank lines; trim single trailing/leading newlines per paragraph."""
    norm = normalize_newlines(text).strip("\n")
    if not norm:
        return []
    parts = BLANK_PARA_RE.split(norm)
    return [p.strip() for p in parts if p.strip()]


def reconstruct_broken_lines(text: str) -> str:
    """
    Merge lines that do not end with terminal punctuation (. ! ? : ; » ").
    Heals sentences broken across line wraps while preserving valid lines.
    """
    lines = normalize_newlines(text).splitlines()
    if not lines:
        return ""

    out: list[str] = []
    buffer = lines[0].strip()

    for i in range(1, len(lines)):
        next_line = lines[i].strip()
        if not next_line:
            if buffer:
                out.append(buffer)
                buffer = ""
            out.append("")
            continue

        if not buffer:
            buffer = next_line
            continue

        if RE_VALID_PUNCT_END.search(buffer):
            out.append(buffer)
            buffer = next_line
        else:
            buffer = buffer + " " + next_line

    if buffer:
        out.append(buffer)

    return "\n".join(out)
