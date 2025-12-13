# segment.py — speaker-based segmentation per spec
import re
from typing import List, Dict, Tuple
from .utils import parse_date_from_filename_or_text

# Accept EN dash, EM dash, hyphen; require exactly TWO tokens, each Initial-capital,
# paragraph start, followed by a space and a dash char, e.g.:
# "Niko Peleshi – Mirëdita…"
# We keep diacritics by allowing letters beyond ASCII.
_DASH = r"[–—-]"
_NAME_TOKEN = r"[A-ZÇË][\w\p{L}\.'’-]*"
try:
    import regex as _rx  # allows \p{L}
    _RE = _rx
    SPEAKER_LINE = _rx.compile(rf"^({_NAME_TOKEN}\s+{_NAME_TOKEN})\s{_DASH}\s(.*)$")
    
except Exception:
    # Fallback without \p{L} (works reasonably for Albanian too)
    _RE = re
    NAME_TOKEN_FALLBACK = r"[A-ZÇË][A-Za-zÇËçëĞğŠšŽžËëÇçÀ-ÖØ-öø-ÿ'\.\-’]*"
    SPEAKER_LINE = re.compile(rf"^({NAME_TOKEN_FALLBACK}\s+{NAME_TOKEN_FALLBACK})\s{_DASH}\s(.*)$")

SESSION_HDR = re.compile(r"^\s*(Seanca|Mbledhja|Konferenca e Kryetarëve)\b.*$", re.I)


def _paragraphs(text: str) -> List[str]:
    # Split on blank lines, preserve internal newlines
    text = text.replace("\r\n", "\n")
    parts = _RE.split(r"\n\s*\n", text)  # pattern first, then text
    return [p.strip("\n") for p in parts if p.strip("\n")]

def segment_by_speakers(stem: str, text: str) -> Dict:
    """
    Returns:
      {
        "date": "YYYY-MM-DD",
        "title": "...",
        "utterances": [
           {"who_name":"Niko Peleshi", "text":"Mirëdita…\n…"},
           ...
        ],
        "speakers_found": {"Niko Peleshi", "Agron Gjekmarkaj", ...}
      }
    """
    date = parse_date_from_filename_or_text(stem, text)
    title = None
    utterances: List[Dict] = []
    speakers_found = set()

    cur: Dict | None = None
    for para in _paragraphs(text):
        # use first line of paragraph to test speaker
        first_line = para.splitlines()[0].strip()
        if not title and SESSION_HDR.match(first_line):
            title = first_line
        m = SPEAKER_LINE.match(first_line)
        if m:
            # close previous utterance
            if cur and cur["text"].strip():
                utterances.append(cur)
            who_name = m.group(1).strip()
            # keep entire paragraph text, but replace the starting "Name – " with remaining text
            # i.e., utterance body is the whole paragraph with the name+dash removed from its first line
            rest_first = m.group(2)
            rest_lines = para.splitlines()
            rest_lines[0] = rest_first
            body = "\n".join(rest_lines).strip()
            cur = {"who_name": who_name, "text": body}
            speakers_found.add(who_name)
        else:
            # continuation of current speaker if any; otherwise ignore as preamble
            if cur is not None:
                cur["text"] += "\n\n" + para

    if cur and cur["text"].strip():
        utterances.append(cur)

    return {
        "date": date,
        "title": title or f"Seancë {date}",
        "utterances": utterances,
        "speakers_found": speakers_found,
    }
