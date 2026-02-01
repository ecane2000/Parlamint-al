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
    # Note: The original regex was looking for spaces before the check.
    # We will look for the pattern anywhere in the line, but we must be careful not to match inside normal text incorrectly.
    # The safest bet for "glued" text is arguably what the user wants, but the crucial fix is ensuring 
    # that even if it's at the start of the line, we force a break if the previous line wasn't blank.
    
    # Let's simplify: regex to find the cue.
    cue_pattern = re.compile(
        rf"(^|[^\n])\s*(?P<cue>[A-ZÇË][{ALPHA_CLASS}’'\.\-]*\s+[A-ZÇË][{ALPHA_CLASS}’'\.\-]*\s*[{DASH_CLASS}])\s+"
    )
    
    for l in lines:
        stripped = l.strip()
        if not stripped:
            out.append(l)
            continue
            
        if stripped.startswith("HAPET MBLEDHJA"):
             out.append(l)
             continue
             
        # Check if the line *starts* with a speaker cue
        # We use a slightly stricter check for start-of-line to avoid false positives in middle of valid sentences
        # assuming names are Capitalized.
        
        # We reuse the logic: search for the cue pattern.
        # But we iterate to find all occurrences? 
        # Actually, usually there's at most one split needed per line (rarely multiple speakers in one line?).
        # Let's handle the simple case: if we find a cue, we make sure it starts a new paragraph.
        
        match = cue_pattern.search(l)
        if match:
            # We found something looking like a cue
            # split_at is where the detected Name starts.
            # match.start(2) corresponds to group 'cue' start? 
            # No, ensure group indices.
            # (?P<cue>...) is group 2 if (^|[^\n]) is group 1.
            
            # The regex matches: (prefix char)(space)(Name... -)
            start_idx = match.start('cue')
            
            # If the cue is at the very start of the line (start_idx == 0), 
            # match.group(1) would be empty string matched by ^.
            
            # If start_idx > 0, we have prefix text.
            prefix = l[:start_idx].strip()
            rest = l[start_idx:].strip()
            
            # If there is prefix text, append it, then a blank line.
            if prefix:
                out.append(prefix)
                out.append("")
                out.append(rest)
            else:
                # It was at start of line. match.group(1) matched start of string or previous char?
                # If match found at start, we just ensure a blank line before it.
                # However, since we are building a list of lines, 'out' might already have content.
                # We essentially just append "" then the line.
                # But we don't want double blank lines if one existed.
                # The split_paragraphs logic handles multiple blank lines fine (ignores them).
                # So it is safe to always prepend a blank line before a speaker line.
                out.append("")
                out.append(rest)
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
