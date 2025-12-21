# -*- coding: utf-8 -*-
"""
Speaker segmentation:
- Identify header/body split at "HAPET MBLEDHJA"
- Reinstate paragraph breaks before speaker cues if they were lost
- Speaker cue pattern: two Capitalized tokens at paragraph start, then dash, then text
"""
import re
from typing import List, Dict
from .utils import split_paragraphs, normalize_newlines, SPACE_DASH_SPACE

# Two tokens starting uppercase (incl. Ç/Ë), then dash, then text
SPEAKER_RE = re.compile(
    r"^\s*(?P<name>[A-ZÇË][\w’'\.-]*\s+[A-ZÇË][\w’'\.-]*)\s*[–—-]\s*(?P<rest>.+)$",
    flags=re.UNICODE
)

def _split_header_body(txt: str):
    lines = normalize_newlines(txt).splitlines()
    i_open = None
    for i, l in enumerate(lines):
        if l.strip().startswith("HAPET MBLEDHJA"):
            i_open = i
            break
    header = "\n".join(lines[:i_open]) if i_open is not None else ""
    body = "\n".join(lines[i_open+1:]) if i_open is not None else txt
    return header, body

def _reinsert_breaks_before_cues(body: str) -> str:
    """
    If cues appear mid-paragraph, put a blank line before them so segmentation sees paragraph starts.
    """
    lines = normalize_newlines(body).splitlines()
    out = []
    for i, l in enumerate(lines):
        # detect a cue after some non-empty text in same line: “… bla. Niko Peleshi – …”
        m = re.search(r"([^\n])\s([A-ZÇË][\w’'\.-]*\s+[A-ZÇË][\w’'\.-]*)\s*[–—-]\s+", l)
        if m:
            # split into two lines: before + cue start
            prefix, cue = l[:m.start(2)-1].rstrip(), l[m.start(2):]
            if prefix:
                out.append(prefix)
            out.append("")  # blank line = new paragraph
            out.append(cue)
        else:
            out.append(l)
    return "\n".join(out)

def segment_by_speakers(clean_txt: str) -> Dict:
    header_txt, body_txt = _split_header_body(clean_txt)
    body_txt = _reinsert_breaks_before_cues(body_txt)

    paras = split_paragraphs(body_txt)
    utterances = []
    current = None

    for para in paras:
        m = SPEAKER_RE.match(para)
        if m:
            # start a new utterance
            if current:
                utterances.append(current)
            who = m.group("name").strip()
            rest = m.group("rest").strip()
            current = {"who_name": who, "paragraphs": [rest] if rest else []}
        else:
            # continuation of current speaker if any
            if current:
                current["paragraphs"].append(para)
            else:
                # body text before first cue — keep if you want; here we skip
                pass
    if current:
        utterances.append(current)

    return {
        "header_text": header_txt,
        "utterances": utterances,
    }
