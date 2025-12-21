# This cell writes a complete, consistent src/ stack aligned to the Hungarian ParlaMint
# header/body style and zips it for download. It does not run the pipeline itself.
from pathlib import Path
import textwrap, zipfile, io, os, json

root = Path("/mnt/data/hu_aligned_stack")
src = root / "src"
src.mkdir(parents=True, exist_ok=True)

files = {}

files["src/__init__.py"] = ""

files["src/utils.py"] = textwrap.dedent("""\
# -*- coding: utf-8 -*-
import re
from pathlib import Path

# Unicode dash set: hyphen-minus, en dash, em dash
UNICODE_DASHES = r"[–—-]"
SPACE_DASH_SPACE = re.compile(rf"\\s*{UNICODE_DASHES}\\s*")
BLANK_PARA_RE = re.compile(r"\\n\\s*\\n", flags=re.UNICODE)

def read_text(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")

def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")

def squash_ws(s: str) -> str:
    \"\"\"Collapse internal spaces/tabs but keep newlines.\"\"\"
    return re.sub(r\"[ \\t]+\", \" \", s)

def normalize_newlines(txt: str) -> str:
    return txt.replace(\"\\r\\n\", \"\\n\").replace(\"\\r\", \"\\n\")

def normalize_name(name: str) -> str:
    return re.sub(r\"\\s+\", \" \", (name or \"\").strip()).lower()

def mint_person_id(full_name: str) -> str:
    full_name = (full_name or \"\").strip()
    parts = re.split(r\"\\s+\", full_name)
    if len(parts) >= 2:
        surname = re.sub(r\"[^A-Za-zÇËçëÀ-ÖØ-öø-ÿ]\", \"\", parts[-1])
        name = re.sub(r\"[^A-Za-zÇËçëÀ-ÖØ-öø-ÿ]\", \"\", parts[0])
        base = f\"{surname}{name}\"
    else:
        base = re.sub(r\"[^A-Za-zÇËçëÀ-ÖØ-öø-ÿ]\", \"\", full_name) or \"UNKNOWN\"
    return f\"pAL_{base}\"

def looks_like_committee(header_block: str) -> bool:
    return bool(re.search(r\"\\bKomision\\w*\", header_block or \"\", flags=re.I))

def split_paragraphs(text: str):
    text = normalize_newlines(text).strip(\"\\n\")
    parts = BLANK_PARA_RE.split(text)
    return [p.strip(\"\\n\") for p in parts if p.strip(\"\\n\")]

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
""")

files["src/crawl.py"] = textwrap.dedent("""\
# -*- coding: utf-8 -*-
\"\"\"Optional PDF crawler (PDF->TXT). You can skip if TXT already exists.\"\"\"
from pathlib import Path
import argparse

def main():
    ap = argparse.ArgumentParser(description=\"Crawl PDFs to texts (optional).")
    ap.add_argument(\"--urls\", required=True, help=\"Text file: one PDF URL per line\")
    ap.add_argument(\"--pdf_out\", default=\"pdfs\", help=\"Folder to store PDFs\")
    ap.add_argument(\"--txt_out\", default=\"texts\", help=\"Folder to store extracted TXT\")
    args = ap.parse_args()

    urls_file = Path(args.urls)
    pdf_dir = Path(args.pdf_out); pdf_dir.mkdir(parents=True, exist_ok=True)
    txt_dir = Path(args.txt_out); txt_dir.mkdir(parents=True, exist_ok=True)

    try:
        import requests
    except Exception:
        raise SystemExit(\"Please `pip install requests pdfminer.six` to use the crawler.\")

    for url in urls_file.read_text(encoding=\"utf-8\").splitlines():
        url = url.strip()
        if not url: continue
        name = url.split(\"/\")[-1]
        pdf_path = pdf_dir / name
        resp = requests.get(url, timeout=60); resp.raise_for_status()
        pdf_path.write_bytes(resp.content)
        # Try to extract text; empty if scanned
        try:
            from pdfminer.high_level import extract_text
            txt = extract_text(str(pdf_path))
            if not txt or txt.strip() == \"\":
                txt = \"\"
        except Exception:
            txt = \"\"
        (txt_dir / (pdf_path.stem + \".txt\")).write_text(txt, encoding=\"utf-8\")
    print(f\"Done. PDFs in {pdf_dir}, TXT in {txt_dir}\")

if __name__ == \"__main__\":
    main()
""")

files["src/extract.py"] = textwrap.dedent("""\
# -*- coding: utf-8 -*-
\"\"\"Cleaning + header extraction from raw text (keeps paragraph breaks).\"\"\"
import re
from pathlib import Path
from .utils import read_text, write_text, normalize_newlines

PAGE_HDR_RE = re.compile(r\"^\\s*={2,}\\s*Page\\s*\\(?\\d+\\)?\\s*={2,}\\s*$\", re.I | re.M)
PAGE_NUM_RE = re.compile(r\"^\\s*\\d+\\s*$\", re.M)

def clean_text(raw_txt: str) -> str:
    txt = normalize_newlines(raw_txt)
    txt = PAGE_HDR_RE.sub(\"\", txt)
    txt = PAGE_NUM_RE.sub(\"\", txt)
    # OCR tidy-ups (user-provided heuristics)
    txt = txt.replace(\" é\", \" ë\").replace(\"É\", \"Ë\")
    txt = txt.replace(\"¢\", \"ç\")
    txt = re.sub(r\"\\bg[ëé]\", \"që\", txt)
    txt = re.sub(r\"\\bgy\", \"gj\", txt)
    return txt

def extract_header_block(txt: str) -> dict:
    lines = [l.strip() for l in normalize_newlines(txt).splitlines()]
    # Find eventType between KUVENDI and PROCESVERBAL
    try:
        i_kv = lines.index(\"KUVENDI\")
    except ValueError:
        i_kv = -1
    try:
        i_proc = lines.index(\"PROCESVERBAL\")
    except ValueError:
        i_proc = -1

    event_lines = []
    if i_kv >= 0 and i_proc > i_kv:
        event_lines = [l for l in lines[i_kv+1:i_proc] if l]

    # Date/time line (next non-empty after PROCESVERBAL)
    date_line = \"\"
    if i_proc >= 0:
        for j in range(i_proc+1, min(i_proc+6, len(lines))):
            if lines[j]:
                date_line = lines[j]; break

    date, time = \"\", \"\"
    m = re.search(r\"m[ëe]\\s*(\\d{1,2})\\.(\\d{1,2})\\.(\\d{4}).*ora\\s*(\\d{1,2}:\\d{2})\", date_line)
    if m:
        d, mo, y, t = m.groups()
        date = f\"{int(y):04d}-{int(mo):02d}-{int(d):02d}\"
        time = t

    # Chair
    chair_name, chair_role = \"\", \"\"
    for idx, l in enumerate(lines):
        if l.startswith(\"Drejton mbledhjen\"):
            for k in range(idx+1, min(idx+5, len(lines))):
                if lines[k]:
                    parts = re.split(r\"\\s*[–—-]\\s*\", lines[k], maxsplit=1)
                    chair_name = parts[0].strip()
                    chair_role = parts[1].strip() if len(parts) > 1 else \"\"
                    break
            break

    # Agenda: between \"Rendi i ditës:\" and \"Marrin pjesë:\" or \"HAPET MBLEDHJA\"
    agenda_text = \"\"
    try:
        i_ag = next(i for i, l in enumerate(lines) if l.startswith(\"Rendi i ditës\"))
        end = None
        for key in (\"Marrin pjesë\", \"HAPET MBLEDHJA\"):
            try:
                j = next(i for i, l in enumerate(lines) if l.startswith(key) and i > i_ag)
                end = j if (end is None or j < end) else end
            except StopIteration:
                pass
        block = lines[i_ag+1:end] if end else lines[i_ag+1:i_ag+8]
        agenda_text = \"\\n\".join([b for b in block if b])
    except StopIteration:
        pass

    return {
        \"eventType\": \"\\n\".join(event_lines),
        \"date\": date,
        \"time\": time,
        \"chair_name\": chair_name,
        \"chair_role\": chair_role,
        \"agenda_text\": agenda_text,
    }

def clean_folder(inbox: Path, cleaned: Path):
    cleaned.mkdir(parents=True, exist_ok=True)
    for p in sorted(inbox.glob(\"*.txt\")):
        raw = read_text(p)
        out = clean_text(raw)
        write_text(cleaned / p.name, out)
""")

files["src/metadata.py"] = textwrap.dedent("""\
# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Optional, Dict
from .utils import normalize_name, mint_person_id

@dataclass
class DocumentMetadata:
    date: str
    time: Optional[str]
    eventType: Optional[str]
    eventTypeAna: Optional[str] = None
    chair_name: Optional[str] = None
    chair_role: Optional[str] = None
    topics: Optional[str] = None
    place: str = \"Tiranë, AL\"
    licence_url: str = \"https://creativecommons.org/licenses/by/4.0/\"
    speakers_idx: Dict[str, str] = field(default_factory=dict)

    def speaker_id(self, full_name: str) -> str:
        key = normalize_name(full_name)
        if key in self.speakers_idx:
            return self.speakers_idx[key]
        pid = mint_person_id(full_name)
        self.speakers_idx[key] = pid
        return pid
""")

files["src/segment.py"] = textwrap.dedent("""\
# -*- coding: utf-8 -*-
\"\"\"Speaker segmentation with paragraph-aware cues.\"\"\"
import re
from typing import Dict
from .utils import split_paragraphs, normalize_newlines

SPEAKER_RE = re.compile(
    r\"^\\s*(?P<name>[A-ZÇË][\\w’'\\.\\-]*\\s+[A-ZÇË][\\w’'\\.\\-]*)\\s*[–—-]\\s*(?P<rest>.+)$\",
    flags=re.UNICODE
)

def _split_header_body(txt: str):
    lines = normalize_newlines(txt).splitlines()
    i_open = None
    for i, l in enumerate(lines):
        if l.strip().startswith(\"HAPET MBLEDHJA\"):
            i_open = i; break
    header = \"\".join([ln+\"\\n\" for ln in lines[:i_open]]) if i_open is not None else \"\"
    body = \"\".join([ln+\"\\n\" for ln in lines[i_open+1:]]) if i_open is not None else txt
    return header, body

def _reinsert_breaks_before_cues(body: str) -> str:
    lines = normalize_newlines(body).splitlines()
    out = []
    for l in lines:
        m = re.search(r\"(^|[^\\n])\\s([A-ZÇË][\\w’'\\.\\-]*\\s+[A-ZÇË][\\w’'\\.\\-]*)\\s*[–—-]\\s+\", l)
        if m and l.strip() and not l.strip().startswith(tuple([\"HAPET MBLEDHJA\"])):
            prefix = l[:m.start(2)-1].rstrip()
            cue = l[m.start(2):]
            if prefix:
                out.append(prefix)
            out.append(\"\")
            out.append(cue)
        else:
            out.append(l)
    return \"\\n\".join(out)

def segment_by_speakers(clean_txt: str) -> Dict:
    header_txt, body_txt = _split_header_body(clean_txt)
    body_txt = _reinsert_breaks_before_cues(body_txt)

    paras = split_paragraphs(body_txt)
    utterances = []
    current = None

    for para in paras:
        m = SPEAKER_RE.match(para)
        if m:
            if current:
                utterances.append(current)
            who = m.group(\"name\").strip()
            rest = m.group(\"rest\").strip()
            current = {\"who_name\": who, \"paragraphs\": [rest] if rest else []}
        else:
            if current:
                current[\"paragraphs\"].append(para)
            else:
                # text before first speaker (skip)
                pass
    if current:
        utterances.append(current)

    return {\"header_text\": header_txt, \"utterances\": utterances}
""")

files["src/tei.py"] = textwrap.dedent("""\
# -*- coding: utf-8 -*-
from xml.etree import ElementTree as ET
from typing import Dict, Optional
from pathlib import Path
from .utils import squash_ws

NS = {\"tei\": \"http://www.tei-c.org/ns/1.0\"}
def q(tag): return f\"{{{NS['tei']}}}{tag}\"

def tei_root(title: str, when_iso: str, license_url: str) -> ET.Element:
    root = ET.Element(q(\"TEI\"), {\"xmlns:tei\": NS[\"tei\"]})
    teiHeader = ET.SubElement(root, q(\"teiHeader\"))

    fileDesc = ET.SubElement(teiHeader, q(\"fileDesc\"))
    titleStmt = ET.SubElement(fileDesc, q(\"titleStmt\"))
    ET.SubElement(titleStmt, q(\"title\"), {\"type\": \"main\"}).text = title

    publicationStmt = ET.SubElement(fileDesc, q(\"publicationStmt\"))
    ET.SubElement(publicationStmt, q(\"publisher\")).text = \"Kuvendi i Shqipërisë; CLARIN ERIC\"
    ET.SubElement(publicationStmt, q(\"pubPlace\")).text = \"Tiranë\"
    avail = ET.SubElement(publicationStmt, q(\"availability\"), {\"status\": \"free\"})
    ET.SubElement(avail, q(\"licence\"), {\"target\": license_url}).text = \"CC BY 4.0\"
    if when_iso:
        ET.SubElement(publicationStmt, q(\"date\"), {\"when\": when_iso}).text = when_iso

    sourceDesc = ET.SubElement(fileDesc, q(\"sourceDesc\"))
    bibl = ET.SubElement(sourceDesc, q(\"bibl\"))
    ET.SubElement(bibl, q(\"title\")).text = \"Procesverbal i Kuvendit të Shqipërisë\"
    ET.SubElement(bibl, q(\"idno\"), {\"type\": \"URL\"}).text = \"https://www.kuvendi.gov.al/\"
    if when_iso:
        ET.SubElement(bibl, q(\"date\"), {\"when\": when_iso}).text = when_iso

    encodingDesc = ET.SubElement(teiHeader, q(\"encodingDesc\"))
    projectDesc = ET.SubElement(encodingDesc, q(\"projectDesc\"))
    ET.SubElement(projectDesc, q(\"p\")).text = (
        \"ParlaMint-AL: korpus i krahasueshëm i seancave parlamentare, i përputhshëm me ParlaMint v5.\"
    )
    classDecl = ET.SubElement(encodingDesc, q(\"classDecl\"))
    tax = ET.SubElement(classDecl, q(\"taxonomy\"), {\"xml:id\": \"parla-taxonomy\"})
    # roles
    cat_roles = ET.SubElement(tax, q(\"category\"), {\"xml:id\": \"parla.roles\", \"n\": \"Speaker roles\"})
    cr1 = ET.SubElement(cat_roles, q(\"category\"), {\"xml:id\": \"parla.speaker\"})
    ET.SubElement(cr1, q(\"catDesc\")).text = \"Folës\"
    cr2 = ET.SubElement(cat_roles, q(\"category\"), {\"xml:id\": \"parla.chair\"})
    ET.SubElement(cr2, q(\"catDesc\")).text = \"Kryetar/Moderues\"
    # events
    cat_events = ET.SubElement(tax, q(\"category\"), {\"xml:id\": \"parla.events\", \"n\": \"Event types\"})
    ce1 = ET.SubElement(cat_events, q(\"category\"), {\"xml:id\": \"parla.sitting\"})
    ET.SubElement(ce1, q(\"catDesc\")).text = \"Seancë/mbledhje\"
    ce2 = ET.SubElement(cat_events, q(\"category\"), {\"xml:id\": \"parla.committee\"})
    ET.SubElement(ce2, q(\"catDesc\")).text = \"Komision\"

    profileDesc = ET.SubElement(teiHeader, q(\"profileDesc\"))
    settingDesc = ET.SubElement(profileDesc, q(\"settingDesc\"))
    setting = ET.SubElement(settingDesc, q(\"setting\"))
    ET.SubElement(setting, q(\"name\")).text = \"Kuvendi i Shqipërisë\"
    if when_iso:
        ET.SubElement(setting, q(\"date\"), {\"when\": when_iso}).text = when_iso
    ET.SubElement(setting, q(\"placeName\")).text = \"Tiranë, AL\"
    ET.SubElement(profileDesc, q(\"p\")).text = \"Pjesëmarrësit referohen te listPerson/listOrg në nivel korpusi.\"

    revisionDesc = ET.SubElement(teiHeader, q(\"revisionDesc\"))
    ET.SubElement(revisionDesc, q(\"change\"), {\"when\": when_iso or \"\"}).text = \"Konvertimi fillestar në TEI (ParlaMint-AL).\"
    return root

def write_plain_day(
    session: dict,
    speakers_idx: Dict[str, str],
    out_path: str,
    license_url: str,
    eventTypeAna: Optional[str] = None,
):
    title = session.get(\"title\") or f\"Kuvendi i Shqipërisë, Procesverbal, {session.get('date','')}\"
    root = tei_root(title, session.get(\"date\",\"\"), license_url)

    # <meeting>
    teiHeader = root.find(q(\"teiHeader\"))
    titleStmt = teiHeader.find(f\".//{q('titleStmt')}\")
    meeting = ET.SubElement(titleStmt, q(\"meeting\"))
    if session.get(\"eventType\"):
        for line in session[\"eventType\"].splitlines():
            if line.strip():
                ET.SubElement(meeting, q(\"p\")).text = line.strip()
    if session.get(\"date\"):
        ET.SubElement(meeting, q(\"date\"), {\"when\": session[\"date\"]}).text = session[\"date\"]
    if session.get(\"time\"):
        ET.SubElement(meeting, q(\"time\")).text = session[\"time\"]
    if session.get(\"chair_name\"):
        chair_text = session[\"chair_name\"]
        if session.get(\"chair_role\"):
            chair_text += f\" — {session['chair_role']}\"
        ET.SubElement(meeting, q(\"chair\")).text = chair_text
    if eventTypeAna:
        meeting.set(\"ana\", eventTypeAna)

    text = ET.SubElement(root, q(\"text\"), {\"xml:lang\": \"sq\"})
    body = ET.SubElement(text, q(\"body\"))
    div_attrs = {\"type\": \"debateSection\"}
    if eventTypeAna:
        div_attrs[\"ana\"] = eventTypeAna
    div = ET.SubElement(body, q(\"div\"), div_attrs)

    for i, u in enumerate(session.get(\"utterances\", []), 1):
        who_name = u.get(\"who_name\") or \"UNKNOWN\"
        pid = speakers_idx.get((who_name or \"\").strip().lower())
        who = f\"#{pid}\" if pid else \"#pAL_UNKNOWN\"
        u_el = ET.SubElement(
            div, q(\"u\"),
            {
                \"xml:id\": f\"uAL_{session.get('date','0000-00-00').replace('-','')}_{i:04d}\",
                \"who\": who,
                \"ana\": \"#parla.speaker\",
            }
        )
        for seg in u.get(\"paragraphs\", []):
            seg_el = ET.SubElement(u_el, q(\"seg\"))
            seg_el.text = squash_ws(seg)

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(out_path, encoding=\"utf-8\", xml_declaration=True)
""")

files["src/root.py"] = textwrap.dedent("""\
# -*- coding: utf-8 -*-
from pathlib import Path

def repo_root_for(module_file: str) -> Path:
    return Path(module_file).resolve().parents[1]
""")

files["src/pipeline.py"] = textwrap.dedent("""\
# -*- coding: utf-8 -*-
import argparse
from pathlib import Path
from .root import repo_root_for
from .utils import ensure_dir, read_text, looks_like_committee
from .extract import clean_folder, extract_header_block
from .segment import segment_by_speakers
from .metadata import DocumentMetadata
from .tei import write_plain_day

REPO_ROOT = repo_root_for(__file__)

def convert_inbox_to_tei(inbox: str, out_dir: str):
    inbox_p = Path(inbox)
    out_p = Path(out_dir)
    ensure_dir(out_p)

    for p in sorted(inbox_p.glob(\"*.txt\")):
        clean_txt = read_text(p)
        header = extract_header_block(clean_txt)
        eventType = header.get(\"eventType\", \"\")
        eventTypeAna = \"#parla.sitting\"
        if looks_like_committee(eventType):
            eventTypeAna += \" #parla.committee\"

        md = DocumentMetadata(
            date=header.get(\"date\", \"\"),
            time=header.get(\"time\"),
            eventType=eventType,
            eventTypeAna=eventTypeAna,
            chair_name=header.get(\"chair_name\"),
            chair_role=header.get(\"chair_role\"),
            topics=header.get(\"agenda_text\"),
        )

        seg = segment_by_speakers(clean_txt)
        utterances = seg[\"utterances\"]
        if md.chair_name:
            md.speaker_id(md.chair_name)
        for u in utterances:
            md.speaker_id(u.get(\"who_name\", \"UNKNOWN\"))

        session = {
            \"date\": md.date,
            \"time\": md.time,
            \"eventType\": md.eventType,
            \"chair_name\": md.chair_name,
            \"chair_role\": md.chair_role,
            \"utterances\": utterances,
        }
        if session[\"eventType\"]:
            one_line = \" / \".join([ln.strip() for ln in session[\"eventType\"].splitlines() if ln.strip()])
            session[\"title\"] = f\"Kuvendi i Shqipërisë — {one_line}, {md.date}\"
        else:
            session[\"title\"] = f\"Kuvendi i Shqipërisë, Procesverbal, {md.date}\"

        out_path = out_p / \"plain\" / f\"ParlaMint-AL_{md.date or p.stem}.xml\"
        write_plain_day(
            session,
            speakers_idx=md.speakers_idx,
            out_path=str(out_path),
            license_url=md.licence_url,
            eventTypeAna=md.eventTypeAna,
        )
        print(f\"Wrote {out_path}\")

def main():
    ap = argparse.ArgumentParser(description=\"ParlaMint-AL day-file builder (HU-aligned header/body).\" )
    ap.add_argument(\"--inbox\", default=str(REPO_ROOT / \"texts\"), help=\"Folder with cleaned TXT files\")
    ap.add_argument(\"--out\", default=str(REPO_ROOT / \"out\"), help=\"Output folder\")
    ap.add_argument(\"--clean_from\", default=None, help=\"If set, clean raw TXT from this folder into --inbox first\")
    ap.add_argument(\"--urls\", default=None, help=\"Optional: crawl PDFs (requires requests, pdfminer.six)\")
    args = ap.parse_args()

    if args.urls:
        from .crawl import main as crawl_main
        import sys
        sys.argv = [\"crawl.py\", \"--urls\", args.urls, \"--txt_out\", args.inbox]
        crawl_main()

    if args.clean_from:
        raw = Path(args.clean_from)
        inbox = Path(args.inbox)
        from .extract import clean_folder as _clean
        _clean(raw, inbox)

    convert_inbox_to_tei(args.inbox, args.out)

if __name__ == \"__main__\":
    main()
""")

# Write files
for path, content in files.items():
    p = root / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

# Zip the stack
zip_path = "/mnt/data/ParlaMint_AL_HU_aligned_src.zip"
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for path, _ in files.items():
        z.write(root / path, arcname=path)

zip_path
