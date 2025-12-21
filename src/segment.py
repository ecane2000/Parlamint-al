# -*- coding: utf-8 -*-
"""
Speaker segmentation with paragraph-aware cues.

Rules:
- Start segmentation only *after* the line that begins with "HAPET MBLEDHJA".
- A speaker-cue line looks like:
    <Name Surname> <dash> <space> <text>
  where Name and Surname both start with a capital (including Ç, Ë),
  and dash can be hyphen-minus, en dash, or em dash.
- If a cue was glued mid-line (cleaning merged paragraphs), we try to
  reinsert a paragraph break right before that cue so it matches.
"""
import re
from typing import Dict, List
from .utils import split_paragraphs, normalize_newlines

# Accept letters, digits, underscore, periods, hyphens, straight/curly apostrophes, and Latin-1 ranges
ALPHA_CLASS = r"\wÀ-ÖØ-öø-ÿÇËçë"
DASH_CLASS  = r"–—-"

# Full speaker cue at start of paragraph
SPEAKER_RE = re.compile(
    rf"^\s*(?P<name>[A-ZÇË][{ALPHA_CLASS}’'\.\-]*\s+[A-ZÇË][{ALPHA_CLASS}’'\.\-]*)\s*[{DASH_CLASS}]\s*(?P<rest>.+)$",
    flags=re.UNICODE,
)

def _split_header_body(txt: str) -> (str, str):
    """
    Return (header_text, body_text) by splitting at 'HAPET MBLEDHJA'.
    If the marker is missing, treat entire text as body.
    """
    lines = normalize_newlines(txt).splitlines()
    i_open = None
    for i, l in enumerate(lines):
        if l.strip().startswith("HAPET MBLEDHJA"):
            i_open = i
            break
    if i_open is None:
        # No marker found: no header, whole text is body
        return "", normalize_newlines(txt)
    header = "\n".join(lines[:i_open])
    body   = "\n".join(lines[i_open + 1 :])
    return header, body

def _reinsert_breaks_before_cues(body: str) -> str:
    """
    If cleaning merged a cue into the middle of a line, put a blank line
    before the cue so the next stage can match it at paragraph start.
    """
    out: List[str] = []
    for l in normalize_newlines(body).splitlines():
        # Look for: <...><space><Name Surname><dash>
        m = re.search(
            rf"(^|[^\n])\s([A-ZÇË][{ALPHA_CLASS}’'\.\-]*\s+[A-ZÇË][{ALPHA_CLASS}’'\.\-]*)\s*[{DASH_CLASS}]\s+",
            l
        )
        if m and l.strip() and not l.strip().startswith("HAPET MBLEDHJA"):
            # Split the line just before the cue (group 2 start)
            split_at = m.start(2)
            prefix = l[:split_at].rstrip()
            cue    = l[split_at:].lstrip()
            if prefix:
                out.append(prefix)
            out.append("")   # blank line -> paragraph boundary
            out.append(cue)
        else:
            out.append(l)
    return "\n".join(out)

def segment_by_speakers(clean_txt: str) -> Dict:
    """
    Input: a cleaned TXT (paragraphs preserved).
    Output:
      {
        "header_text": "<text before HAPET MBLEDHJA>",
        "utterances": [
           {"who_name": "...", "paragraphs": ["...", "..."]},
           ...
        ]
      }
    """
    header_txt, body_txt = _split_header_body(clean_txt)
    body_txt = _reinsert_breaks_before_cues(body_txt)

    paras = split_paragraphs(body_txt)
    utterances = []
    current = None

    for para in paras:
        m = SPEAKER_RE.match(para)
        if m:
            # flush previous
            if current:
                utterances.append(current)
            who = m.group("name").strip()
            rest = m.group("rest").strip()
            current = {"who_name": who, "paragraphs": [rest] if rest else []}
        else:
            if current:
                current["paragraphs"].append(para)
            else:
                # text before first speaker inside the body: ignore
                pass

    if current:
        utterances.append(current)

    return {"header_text": header_txt, "utterances": utterances}
