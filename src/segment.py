# segment.py — speaker-based segmentation per spec
import re
from typing import List, Dict, Tuple
from .utils import parse_date_from_filename_or_text, normalize_text, normalize_for_segmentation


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
    pattern = r"\n\s*\n"
    parts = _RE.split(pattern, text) if _RE is not re else re.split(pattern, text)
    return [p.strip("\n") for p in parts if p.strip("\n")]

def _split_header_and_body(text: str) -> Tuple[str, str]:
    """
    Split the cleaned text into:
      - header_text: everything before 'HAPET MBLEDHJA'
      - body_text:   everything after that line
    If 'HAPET MBLEDHJA' is not found, the whole text is body_text.
    """
    m = re.search(r"^ *HAPET MBLEDHJA\b.*$", text, flags=re.MULTILINE)
    if not m:
        return "", text
    header = text[:m.start()]
    body = text[m.end():]
    return header, body


def _extract_session_metadata(header_text: str) -> Dict:
    """
    From the header (before 'HAPET MBLEDHJA'), extract:
      - chair_name, chair_role
      - topics: list of {n, text}
      - participants_present / _absent / _guests
    according to the patterns you described.
    """
    meta: Dict[str, object] = {}

    # --- Chair: 'Drejton mbledhjen:' + next non-empty line 'Name – Role'
    m = re.search(r"Drejton mbledhjen:\s*(.*)", header_text)
    chair_line = None
    if m:
        after = m.group(1).strip()
        if after:
            chair_line = after
        else:
            # take first non-empty line after
            tail = header_text[m.end():].splitlines()
            for ln in tail:
                if ln.strip():
                    chair_line = ln.strip()
                    break
    if chair_line:
        m2 = re.match(r"(?P<name>[A-ZÇË][^–\-]+?)\s*[–\-]\s*(?P<role>.+)$", chair_line)
        if m2:
            meta["chair_name"] = m2.group("name").strip()
            meta["chair_role"] = m2.group("role").strip()
        else:
            meta["chair_raw"] = chair_line

    # --- Agenda / topics: from 'Rendi i ditës:' until next block
    m = re.search(
        r"Rendi i ditës:?\s*(.*?)(?=\nMarrin pjesë:|\nMungojnë:|\nTë ftuar:|\nHAPET MBLEDHJA\b|$)",
        header_text,
        flags=re.S,
    )
    if m:
        topic_block = m.group(1).strip()
        # collapse whitespace to a single space
        topic_block = re.sub(r"\s+", " ", topic_block)
        # split by numbered points: 1. ..., 2. ..., 3. ...
        parts = re.split(r"\b(\d+)\.\s*", topic_block)
        topics = []
        for i in range(1, len(parts), 2):
            num = parts[i]
            txt = parts[i + 1].strip()
            if txt:
                topics.append({"n": num, "text": txt})
        if topics:
            meta["topics"] = topics

    # helper: extract a block between a label and the next label
    def _extract_block(label: str, stop_labels):

        # stop_labels is a tuple of strings like "Mungojnë:", "Të ftuar:", "HAPET MBLEDHJA"
        pattern = (
            re.escape(label)
            + r":\s*(.*?)(?="
            + "|".join(r"\n" + re.escape(lbl) for lbl in stop_labels)
            + r"|$)"
        )
        mm = re.search(pattern, header_text, flags=re.S)
        if not mm:
            return None
        block = mm.group(1)
        # drop pure page-number lines inside participants
        lines = [ln for ln in block.splitlines() if not ln.strip().isdigit()]
        text = " ".join(ln.strip() for ln in lines if ln.strip())
        text = re.sub(r"\s+", " ", text).strip()
        return text or None

    # --- Participants present: 'Marrin pjesë:'
    present = _extract_block("Marrin pjesë", ("Mungojnë:", "Të ftuar:", "HAPET MBLEDHJA"))
    if present:
        meta["participants_present"] = present

    # --- Participants absent: 'Mungojnë:'
    absent = _extract_block("Mungojnë", ("Të ftuar:", "HAPET MBLEDHJA"))
    if absent:
        meta["participants_absent"] = absent

    # --- Guests: 'Të ftuar:'
    guests = _extract_block("Të ftuar", ("HAPET MBLEDHJA",))
    if guests:
        meta["participants_guests"] = guests

    return meta

# in segment.py
try:
    import regex as re  # supports \p{L}
except ImportError:
    import re

SPEAKER_RE = re.compile(
    r'^\s*(?P<name>[A-ZÇË][\p{L}\.'’\-]*\s+[A-ZÇË][\p{L}\.'’\-]*)'
    r'\s*(?:[–—-])\s+(?P<rest>.+)$',
    re.UNICODE
)

def segment_by_speakers(stem: str, text: str):
    text = normalize_for_segmentation(text)  # from step 1
    lines = text.splitlines()

    utterances = []
    current = None

    for ln in lines:
        m = SPEAKER_RE.match(ln)
        if m:
            # start a new utterance
            who = m.group('name')
            rest = m.group('rest').strip()
            if current:
                utterances.append(current)
            current = {"who_name": who, "text": rest}
        else:
            # continuation
            if current:
                if ln.strip() == "":
                    # preserve paragraph boundaries inside <u> as blank lines
                    current["text"] += "\n\n"
                else:
                    # keep natural line breaks
                    current["text"] += ("\n" + ln)
            # if no current, we’re in preamble; ignore or collect separately

    if current:
        utterances.append(current)

    # build session dict (date/title—you already have helpers)
    date = parse_date_from_filename_or_text(stem, text)
    title = f"Seancë {date}"
    speakers_found = {u["who_name"] for u in utterances}
    return {
        "date": date,
        "title": title,
        "utterances": utterances,
        "speakers_found": speakers_found,
    }

def reinsert_breaks_before_speakers(text: str) -> str:
    out = []
    for ln in text.splitlines():
        if SPEAKER_RE.match(ln) and out and out[-1].strip() != "":
            out.append("")  # insert a blank line
        out.append(ln)
    return "\n".join(out)