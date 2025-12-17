
from typing import Dict, Tuple, List
try:
    import regex as re
except Exception:
    import re

from .utils import (
    normalize_for_segmentation,
    strip_page_numbers,
    find_idx,
    parse_date_from_filename_or_text,
    extract_date_time_from_header,
    extract_event_type_from_cleaned,
)

HEADER_DIRECTS = "Drejton mbledhjen"
HEADER_AGENDA = "Rendi i ditës"
HEADER_PRESENT = "Marrin pjesë"
HEADER_ABSENT = "Mungojnë"
HEADER_INVITED = "Të ftuar"
OPEN_MEETING = "HAPET MBLEDHJA"

SPEAKER_RE = re.compile(
    r"^\s*(?P<name>[A-ZÇË][\p{L}.'’\-]*\s+[A-ZÇË][\p{L}.'’\-]*)\s*(?:[–—-])\s+(?P<rest>.+)$",
    re.UNICODE,
)

def reinsert_breaks_before_speakers(text: str) -> str:
    out = []
    for ln in text.splitlines():
        if SPEAKER_RE.match(ln) and out and out[-1].strip() != "":
            out.append("")
        out.append(ln)
    return "\n".join(out)

def _split_header_and_body(text: str) -> Tuple[str, str]:
    t = normalize_for_segmentation(text)
    lines = strip_page_numbers(t.splitlines())
    i_body = find_idx(lines, OPEN_MEETING)
    if i_body >= 0:
        header = "\n".join(lines[:i_body+1])
        body = "\n".join(lines[i_body+1:])
    else:
        header = "\n".join(lines[:120])
        body = "\n".join(lines[120:])
    return header, body

def _split_name_role(s: str):
    for sep in (" – ", " — ", " - ", " –", " —", " -"):
        if sep in s:
            parts = [p.strip() for p in s.split(sep, 1)]
            if len(parts) == 2:
                return parts[0], parts[1]
    return s.strip(), None

def _extract_session_metadata(header_text: str) -> Dict:
    meta: Dict[str, object] = {}
    lines = [ln.rstrip() for ln in header_text.splitlines()]

    ev = extract_event_type_from_cleaned(header_text)
    if ev:
        meta["eventType"] = ev

    i_dir = find_idx(lines, HEADER_DIRECTS)
    if i_dir >= 0:
        for j in range(i_dir+1, min(i_dir+6, len(lines))):
            s = lines[j].strip()
            if not s:
                continue
            name, role = _split_name_role(s)
            meta["chair_name"] = name
            if role:
                meta["chair_role"] = role
            break

    i_ag = find_idx(lines, HEADER_AGENDA)
    i_pres = find_idx(lines, HEADER_PRESENT)
    topics: List[Dict[str, str]] = []
    if 0 <= i_ag < len(lines):
        end = i_pres if i_pres > i_ag else len(lines)
        block = [ln.strip() for ln in lines[i_ag+1:end] if ln.strip()]
        n = 0
        for ln in block:
            n += 1
            topics.append({"n": n, "text": ln})
    if topics:
        meta["topics"] = topics

    if i_pres >= 0:
        present_line = ""
        for j in range(i_pres+1, min(i_pres+6, len(lines))):
            s = lines[j].strip()
            if s:
                present_line = s
                break
        if present_line:
            present_line = present_line.replace(" dhe ", ", ")
            meta["participants_present"] = present_line.strip().rstrip(".")

    i_abs = find_idx(lines, HEADER_ABSENT)
    if i_abs >= 0:
        abs_line = ""
        for j in range(i_abs+1, min(i_abs+4, len(lines))):
            s = lines[j].strip()
            if s:
                abs_line = s
                break
        if abs_line:
            abs_line = abs_line.replace(" dhe ", ", ")
            meta["participants_absent"] = abs_line.strip().rstrip(".")

    i_inv = find_idx(lines, HEADER_INVITED)
    if i_inv >= 0:
        invited_lines = []
        for j in range(i_inv+1, min(i_inv+60, len(lines))):
            s = lines[j].strip()
            if not s:
                continue
            if s.startswith(OPEN_MEETING):
                break
            if re.fullmatch(r"\d+", s):
                continue
            invited_lines.append(s)
        if invited_lines:
            meta["participants_guests"] = " ".join(invited_lines).strip()

    when_iso, when_time = extract_date_time_from_header(header_text)
    if when_iso:
        meta["date"] = when_iso
    if when_time:
        meta["time"] = when_time

    return meta

def _paragraphs(text: str) -> List[str]:
    parts = re.split(r"\n\s*\n", text)
    return [p.strip("\n") for p in parts if p.strip("\n")]

def segment_by_speakers(stem: str, cleaned_text: str) -> Dict:
    header_text, body_text = _split_header_and_body(cleaned_text)
    meta = _extract_session_metadata(header_text)

    if "date" not in meta:
        meta["date"] = ""  # leave fallback to pipeline if needed

    body_text = reinsert_breaks_before_speakers(body_text)
    paragraphs = _paragraphs(body_text)

    utterances: List[Dict[str, str]] = []
    speakers_found = set()
    current_speaker = None

    for para in paragraphs:
        first = para.splitlines()[0]
        m = SPEAKER_RE.match(first)
        if m:
            name = m.group("name").strip()
            rest = m.group("rest").strip()
            current_speaker = name
            speakers_found.add(name)
            utterances.append({"who_name": name, "text": rest})
        else:
            if current_speaker is not None:
                utterances[-1]["text"] += "\n\n" + para

    session = {
        "stem": stem,
        "date": meta.get("date", ""),
        "time": meta.get("time"),
        "eventType": meta.get("eventType"),
        "chair_name": meta.get("chair_name"),
        "chair_role": meta.get("chair_role"),
        "topics": meta.get("topics", []),
        "participants_present": meta.get("participants_present"),
        "participants_absent": meta.get("participants_absent"),
        "participants_guests": meta.get("participants_guests"),
        "utterances": utterances,
        "speakers_found": sorted(speakers_found),
    }
    return session
