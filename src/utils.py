# -*- coding: utf-8 -*-
import re
from pathlib import Path

# Accept hyphen-minus, en dash, em dash
UNICODE_DASHES = r"[–—-]"
SPACE_DASH_SPACE = re.compile(rf"\s*{UNICODE_DASHES}\s*")
BLANK_PARA_RE = re.compile(r"\n\s*\n", flags=re.UNICODE)

def read_text(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def squash_ws(s: str) -> str:
    """Collapse internal spaces/tabs but keep newlines."""
    return re.sub(r"[ \t]+", " ", s)

def normalize_newlines(txt: str) -> str:
    return txt.replace("\r\n", "\n").replace("\r", "\n")

def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip()).lower()

def mint_person_id(full_name: str) -> str:
    """Create a stable-ish ParlaMint-style person id from a name."""
    full_name = (full_name or "").strip()
    parts = re.split(r"\s+", full_name)
    if len(parts) >= 2:
        surname = re.sub(r"[^A-Za-zÇËçëÀ-ÖØ-öø-ÿ]", "", parts[-1])
        name = re.sub(r"[^A-Za-zÇËçëÀ-ÖØ-öø-ÿ]", "", parts[0])
        base = f"{surname}{name}"
    else:
        base = re.sub(r"[^A-Za-zÇËçëÀ-ÖØ-öø-ÿ]", "", full_name) or "UNKNOWN"
    return f"pAL_{base}"

def looks_like_committee(header_block: str) -> bool:
    return bool(re.search(r"\bKomision\w*", header_block or "", flags=re.I))

def split_paragraphs(text: str):
    """Split on blank lines; trim single trailing/leading newlines per paragraph."""
    text = normalize_newlines(text).strip("\n")
    parts = BLANK_PARA_RE.split(text)
    return [p.strip("\n") for p in parts if p.strip("\n")]

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

# Regex for line ending with punctuation [.?!] followed by optional spaces
RE_VALID_PUNCT_END = re.compile(r"[.?!]\s*$")

def reconstruct_broken_lines(text: str) -> str:
    """
    Merge lines that do NOT end with valid punctuation (. ! ?).
    This heals broken sentences split across lines.
    
    Logic:
      - Split into lines.
      - Iterate:
        - If current buffer (accumulated line) ends with punctuation, flush it (newline).
        - Else, append next line with a space (merge).
    """
    lines = normalize_newlines(text).splitlines()
    if not lines:
        return ""
    
    out = []
    buffer = lines[0]
    
    for i in range(1, len(lines)):
        next_line = lines[i]
        
        # If the current buffer ends with valid punctuation, it is a complete line/sentence.
        # We can flush it.
        if RE_VALID_PUNCT_END.search(buffer):
            out.append(buffer)
            buffer = next_line
        else:
            # It's a broken line (or header/text that shouldn't split).
            # Merge with next line.
            # Handle spacing: avoiding double spaces if one ends with space?
            # User wants standard merge. space is safer.
            buffer = buffer.strip() + " " + next_line.strip()
            
    # Flush the last buffer
    if buffer:
        out.append(buffer)
        
    return "\n".join(out)
