from typing import Dict, Tuple, List
try:
    import regex as re  # better \p{L}
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
            out.append("")  # insert a blank line before a new speaker line
        out.append(ln)
    return "\n".join(out)

def _split_header_and_body(text: str) -> Tuple[str, str]:
    t = normalize_for_segmentation(text)
    lines = strip_page_numbers(t.splitlines())
    i_body = find_idx(lines, OPEN_MEETING)
    if i_body >= 0:
        header = "\n".join(lines[:i_body+1])  # include the marker line
        body = "\n".join(lines[i_body+1:])
    else:
        header = "\n".join(lines[:120])
        body = "\n".join(lines[120:])
    return header, body

def _extract_session_metadata(header_text: str) -> Dict:
    meta: Dict[str, object] = {}
    lines = [ln.rstrip() for ln in header_text.splitlines()]
    # eventType
    ev = extract_event_type_from_cleaned(header_text)
    if ev:
        meta["eventType"] = ev

    # chair
    i_dir = find_idx(lines, HEADER_DIRECTS)
    if i_dir >= 0:
        for j in range(i_dir+1, min(i_dir+6, len(lines))):
            s = lines[j].strip()
            if not s:
                continue
            # name – role
            name, role = _split_name_role(s)
            meta["chair_name"] = name
            if role:
                meta["chair_role"] = role
            break

    # agenda (topics): from 'Rendi i ditës' until 'Marrin pjesë'
    i_ag = find_idx(lines, HEADER_AGENDA)
    i_pres = find_idx(lines, HEADER_PRESENT)
    topics: List[Dict[str,str]] = []
    if 0 <= i_ag < len(lines):
        end = i_pres if i_pres > i_ag else len(lines)
        block = [ln.strip() for ln in lines[i_ag+1:end] if ln.strip()]
        # keep each item as one line; simple numbering if '. ' occurs
        n = 0
        for ln in block:
            n += 1
            topics.append({"n": n, "text": ln})
    if topics:
        meta["topics"] = topics

    # participants present
    if i_pres >= 0:
        present_line = ""
        for j in range(i_pres+1, min(i_pres+6, len(lines))):
            s = lines[j].strip()
            if s:
                present_line = s
                break
        if present_line:
            # normalize " dhe " as comma separator
            present_line = present_line.replace(" dhe ", ", ")
            meta["participants_present"] = present_line.strip().rstrip(".")

    # absent
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

    # invited: from 'Të ftuar' until a page number or OPEN_MEETING
    i_inv = find_idx(lines, HEADER_INVITED)
    if i_inv >= 0:
        invited_lines = []
        for j in range(i_inv+1, min(i_inv+60, len(lines))):
            s = lines[j].strip()
            if not s:
                continue
            if s.startswith(OPEN_MEETING):
                break
            # ignore pure numbers (page headers)
            if re.fullmatch(r"\d+", s):
                continue
            invited_lines.append(s)
        if invited_lines:
            meta["participants_guests"] = " ".join(invited_lines).strip()

    # date/time
    when_iso, when_time = extract_date_time_from_header(header_text)
    if when_iso:
        meta["date"] = when_iso
    if when_time:
        meta["time"] = when_time

    return meta

def _split_name_role(s: str):
    # tolerate different dash glyphs
    for sep in (" – ", " — ", " - ", " –", " —", " -"):
        if sep in s:
            parts = [p.strip() for p in s.split(sep, 1)]
            if len(parts) == 2:
                return parts[0], parts[1]
    return s.strip(), None

def _paragraphs(text: str) -> List[str]:
    # paragraphs separated by blank lines; keep structure
    parts = re.split(r"\n\s*\n", text)
    return [p.strip("\n") for p in parts if p.strip("\n")]

def segment_by_speakers(stem: str, cleaned_text: str) -> Dict:
    header_text, body_text = _split_header_and_body(cleaned_text)
    meta = _extract_session_metadata(header_text)

    # Fallback date if not found in header
    if "date" not in meta:
        meta["date"] = parse_date_from_filename_or_text(stem) or ""

    # Reinsert blank line before speaker cues and segment
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
'''

tei_py = r'''
from pathlib import Path
import xml.etree.ElementTree as ET
from .utils import normalize_text

TEI_NS = "http://www.tei-c.org/ns/1.0"
def q(tag: str) -> str:
    return f"{{{TEI_NS}}}{tag}"

ET.register_namespace("", TEI_NS)

def tei_root(title: str, when_iso: str, license_url: str):
    TEI = ET.Element(q("TEI"))
    teiHeader = ET.SubElement(TEI, q("teiHeader"))
    fileDesc = ET.SubElement(teiHeader, q("fileDesc"))
    titleStmt = ET.SubElement(fileDesc, q("titleStmt"))
    ET.SubElement(titleStmt, q("title"), {"type": "main"}).text = title or "Mbledhje"
    publicationStmt = ET.SubElement(fileDesc, q("publicationStmt"))
    availability = ET.SubElement(publicationStmt, q("availability"), {"status": "free"})
    ET.SubElement(availability, q("licence"), {"target": license_url}).text = license_url
    if when_iso:
        ET.SubElement(publicationStmt, q("date"), {"when": when_iso}).text = when_iso
    sourceDesc = ET.SubElement(fileDesc, q("sourceDesc"))
    ET.SubElement(sourceDesc, q("p")).text = "Burimi: Kuvendi i Shqipërisë."
    # Create profileDesc for agenda/participants later
    ET.SubElement(teiHeader, q("profileDesc"))
    return TEI

def write_plain_day(session, speakers_idx, out_path: Path, license_url: str = "https://creativecommons.org/licenses/by/4.0/"):
    # Title encodes parliament + event type + date (if available)
    title = f"Kuvendi i Shqipërisë, Procesverbal, {session.get('date','')}"
    if session.get("eventType"):
        one_line = " / ".join([ln.strip() for ln in session["eventType"].splitlines() if ln.strip()])
        title = f"Kuvendi i Shqipërisë — {one_line}, {session.get('date','')}"
    root = tei_root(title, session.get("date") or "", license_url)

    # meeting block
    teiHeader = root.find(q("teiHeader"))
    fileDesc = teiHeader.find(q("fileDesc"))
    titleStmt = fileDesc.find(q("titleStmt"))
    meeting = ET.SubElement(titleStmt, q("meeting"), {"ana": "#parla.sitting"})
    if session.get("eventType"):
        for line in session["eventType"].splitlines():
            if line.strip():
                ET.SubElement(meeting, q("p")).text = line.strip()
    if session.get("date"):
        ET.SubElement(meeting, q("date"), {"when": session["date"]}).text = session["date"]
    if session.get("time"):
        ET.SubElement(meeting, q("time")).text = session["time"]
    if session.get("chair_name"):
        chair_text = session["chair_name"]
        if session.get("chair_role"):
            chair_text = f"{chair_text} — {session['chair_role']}"
        ET.SubElement(meeting, q("chair")).text = chair_text

    # profileDesc: agenda + participants
    profileDesc = teiHeader.find(q("profileDesc"))
    if session.get("topics"):
        list_el = ET.SubElement(profileDesc, q("list"), {"type": "agenda"})
        for it in session["topics"]:
            li = ET.SubElement(list_el, q("item"))
            if "n" in it:
                li.set("n", str(it["n"]))
            li.text = it.get("text") or ""
    for label, key in (("present", "participants_present"),
                       ("absent", "participants_absent"),
                       ("guests", "participants_guests")):
        val = session.get(key)
        if val:
            p = ET.SubElement(profileDesc, q("p"), {"type": f"participants:{label}"})
            p.text = val

    # body
    text = ET.SubElement(root, q("text"))
    body = ET.SubElement(text, q("body"))
    div = ET.SubElement(body, q("div"), {"type": "debateSection"})
    # write utterances preserving paragraph breaks as <seg>
    def _norm(s: str) -> str:
        try:
            return normalize_text(s, preserve_paragraphs=True)
        except TypeError:
            return normalize_text(s)

    for i, u in enumerate(session.get("utterances", []), 1):
        who_name = u.get("who_name") or "UNKNOWN"
        pid = None
        if isinstance(speakers_idx, dict):
            pid = speakers_idx.get((who_name or "").lower())
        who = f"#{pid}" if pid else "#pAL_UNKNOWN"
        u_el = ET.SubElement(div, q("u"), {"xml:id": f"spAL_{i:04d}", "who": who})
        utext = _norm(u.get("text",""))
        paras = [p for p in utext.split("\n\n") if p.strip()]
        if not paras:
            paras = [utext] if utext else []
        for para in paras:
            seg = ET.SubElement(u_el, q("seg"))
            seg.text = para

    # write file
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(root)
    tree.write(out_path, encoding="utf-8", xml_declaration=True)