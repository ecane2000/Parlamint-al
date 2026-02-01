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
    flags=re.UNICODE | re.DOTALL,
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
    # Preserve the rest as a single string to keep blank lines intact initially
    body   = "\n".join(lines[i_open + 1 :])
    return header, body

def _reinsert_breaks_before_cues(body: str) -> str:
    """
    Ensure every speaker cue is preceded by a blank line, so it becomes its own paragraph.
    This handles cues glued mid-line AND cues that are just on a new line without a blank line before them.
    """
    out: List[str] = []
    # We'll process line by line.
    lines = normalize_newlines(body).splitlines()
    
    # Regex to find a cue. match mid-line or start-of-line.
    # We want to detect: [start_of_line_or_space]Name Surname[dash]
    
    cue_pattern = re.compile(
        rf"(^|[^\n])\s*(?P<cue>[A-ZÇË][{ALPHA_CLASS}’'\.\-]*\s+[A-ZÇË][{ALPHA_CLASS}’'\.\-]*\s*[{DASH_CLASS}])\s+"
    )
    
    # Validation pattern: The preceding text must end with [.?!] followed by optional spaces.
    valid_split_end_re = re.compile(r'[.?!]\s*$')

    # To handle cross-line checks (start of line case), we need to track the "previous valid line content"
    # accumulated so far in 'out'. However, 'out' contains strings.
    # We can peek at out[-1] if exists.

    for l in lines:
        stripped = l.strip()
        if not stripped:
            out.append(l)
            continue
            
        if stripped.startswith("HAPET MBLEDHJA"):
             out.append(l)
             continue
             
        # Search for cue pattern
        match = cue_pattern.search(l)
        if match:
            # We found something looking like a cue
            start_idx = match.start('cue')
            
            prefix = l[:start_idx].strip()
            rest = l[start_idx:].strip()
            
            # DECISION LOGIC:
            should_split = False
            
            if prefix:
                # Case 1: Mid-line split.
                # Check if prefix ends with valid punctuation.
                if valid_split_end_re.search(prefix):
                    should_split = True
            else:
                # Case 2: Start-of-line split.
                # Check if the PREVIOUS line in 'out' ends with valid punctuation.
                # We need to find the last non-empty line in 'out' to check.
                # If 'out' is empty, it's the start of body -> split is fine/irrelevant (no previous text to merge with).
                # But usually "body" follows header, so splitting at very start is OK.
                
                # Find last non-empty line
                prev_text = ""
                for prev_line in reversed(out):
                    if prev_line.strip():
                        prev_text = prev_line
                        break
                
                if not prev_text:
                    # No previous text, so essentially a start of block. can treat as split or just new para.
                    # We will force a break just to be consistent with "speaker starts new para".
                    should_split = True
                else:
                    if valid_split_end_re.search(prev_text):
                        should_split = True

            if should_split:
                if prefix:
                    out.append(prefix)
                    out.append("")
                    out.append(rest)
                else:
                    out.append("")
                    out.append(rest)
            else:
                # MERGE / NO SPLIT
                # If it was mid-line (prefix exists), we just keep the line as is.
                # If it was start-of-line, we just append the line (it remains a separate line in the list, 
                # but no blank line is inserted, so split_paragraphs won't see it as a new paragraph 
                # unless there was already a blank line before it in 'lines', which we handled at start of loop?)
                
                # Careful: 'lines' iteration doesn't include the blank lines if we used splitlines() on meaningful text? 
                # actually normalize_newlines(body).splitlines() preserves blank lines as empty strings.
                # And we handle `if not stripped: out.append(l); continue` at top.
                # So if we are here, 'l' is not empty.
                
                out.append(l)

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
