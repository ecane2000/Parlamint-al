# tei.py
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import xml.etree.ElementTree as ET

from .metadata import DocumentMetadata
from .config import PARLIAMENT_NAME, CITY, LICENSE_URL

from .utils import (
    extract_meeting_title_from_cleaned,
    strip_detected_header_block,
    normalize_text,
)

XML_NS = "http://www.w3.org/XML/1998/namespace"
TEI_NS = "http://www.tei-c.org/ns/1.0"

ET.register_namespace("", TEI_NS)
ET.register_namespace("xml", XML_NS)

# --- NEW: minimal TEI header/root builder used by write_plain_day ---
def tei_root(title: str, when_iso: str, license_url: str):
    """
    Build a lightweight ParlaMint-style TEI root with a sane header.
    write_plain_day(...) will append <text>/<body>/<u> afterwards.
    """
    # NOTE: relies on a module-level helper q(tag) -> '{TEI_NS}tag'
    TEI = ET.Element(q("TEI"), {
        "{http://www.w3.org/XML/1998/namespace}lang": "sq"
    })
    teiHeader = ET.SubElement(TEI, q("teiHeader"))
    fileDesc = ET.SubElement(teiHeader, q("fileDesc"))
    titleStmt = ET.SubElement(fileDesc, q("titleStmt"))
    ET.SubElement(titleStmt, q("title"), {
        "type": "main",
        "{http://www.w3.org/XML/1998/namespace}lang": "sq"
    }).text = title

    publicationStmt = ET.SubElement(fileDesc, q("publicationStmt"))
    availability = ET.SubElement(publicationStmt, q("availability"), {"status": "free"})
    ET.SubElement(availability, q("licence")).text = license_url
    ET.SubElement(publicationStmt, q("date"), {"when": when_iso}).text = when_iso

    sourceDesc = ET.SubElement(fileDesc, q("sourceDesc"))
    ET.SubElement(sourceDesc, q("p")).text = "Source: Parliament of Albania."

    # Do NOT create <text> here; write_plain_day() will add it.
    return TEI

def qname(local: str) -> str:
    """Build a TEI QName."""
    return f"{{{TEI_NS}}}{local}"

TEI_NS = "http://www.tei-c.org/ns/1.0"
def q(tag: str) -> str:
    return f"{{{TEI_NS}}}{tag}"


def make_tei_root(meta: DocumentMetadata, body_text: str) -> ET.Element:
    """
    Build a minimal ParlaMint-style TEI component for a single day.

    For now we treat the whole TXT as one 'sitting' with a single
    generic utterance. You will later replace this with proper
    division into <div>, <u>, <seg> according to the Albanian
    parliament layout.
    """
    tei = ET.Element(
        qname("TEI"),
        {
            f"{{{XML_NS}}}id": meta.doc_id,
            f"{{{XML_NS}}}lang": meta.language,
            # By default, everything goes into the reference subcorpus
            "ana": "#parla.sitting #reference",
        },
    )

    tei.append(build_tei_header(meta))
    tei.append(build_text_block(meta, body_text))
    return tei


def build_tei_header(meta: DocumentMetadata) -> ET.Element:
    """
    Very small teiHeader that still follows the ParlaMint guidelines
    in spirit. It covers:

    * fileDesc (titleStmt, publicationStmt, sourceDesc)
    * encodingDesc (projectDesc stub)
    * profileDesc (settingDesc + langUsage)
    * revisionDesc (single 'built' change)
    """
    teiHeader = ET.Element(qname("teiHeader"))

    fileDesc = ET.SubElement(teiHeader, qname("fileDesc"))
    titleStmt = ET.SubElement(fileDesc, qname("titleStmt"))

    title_sq = meta.title_sq or f"{PARLIAMENT_NAME}, seancë plenare, {meta.date}"
    title_en = meta.title_en or f"Parliamentary sitting, {PARLIAMENT_NAME}, {meta.date}"

    t1 = ET.SubElement(titleStmt, qname("title"), {"type": "main", f"{{{XML_NS}}}lang": "sq"})
    t1.text = title_sq

    t2 = ET.SubElement(titleStmt, qname("title"), {"type": "main", f"{{{XML_NS}}}lang": "en"})
    t2.text = title_en

    respStmt = ET.SubElement(titleStmt, qname("respStmt"))
    resp = ET.SubElement(respStmt, qname("resp"))
    resp.text = "Compilation and TEI conversion"
    name = ET.SubElement(respStmt, qname("name"))
    name.text = PARLIAMENT_NAME

    publicationStmt = ET.SubElement(fileDesc, qname("publicationStmt"))
    publisher = ET.SubElement(publicationStmt, qname("publisher"))
    publisher.text = PARLIAMENT_NAME
    pubPlace = ET.SubElement(publicationStmt, qname("pubPlace"))
    pubPlace.text = CITY
    availability = ET.SubElement(publicationStmt, qname("availability"))
    licence = ET.SubElement(
        availability,
        qname("licence"),
        {"target": LICENSE_URL},
    )
    licence.text = "Creative Commons Attribution 4.0 International (CC BY 4.0)"

    sourceDesc = ET.SubElement(fileDesc, qname("sourceDesc"))
    bibl = ET.SubElement(sourceDesc, qname("bibl"))
    if meta.source_url:
        ref = ET.SubElement(bibl, qname("ref"), {"target": meta.source_url})
        ref.text = meta.source_url
    else:
        bibl.text = "Official transcript from the Parliament of Albania website."

    # encodingDesc stub
    encodingDesc = ET.SubElement(teiHeader, qname("encodingDesc"))
    projectDesc = ET.SubElement(encodingDesc, qname("projectDesc"))
    p = ET.SubElement(projectDesc, qname("p"))
    p.text = (
        "Pilot conversion of Albanian parliamentary proceedings to the "
        "ParlaMint/Parla-CLARIN TEI format. Header is intentionally minimal "
        "and will be enriched in later iterations."
    )

    # profileDesc
    profileDesc = ET.SubElement(teiHeader, qname("profileDesc"))
    settingDesc = ET.SubElement(profileDesc, qname("settingDesc"))
    setting = ET.SubElement(settingDesc, qname("setting"))
    place = ET.SubElement(setting, qname("name"), {"type": "place"})
    place.text = PARLIAMENT_NAME
    city = ET.SubElement(setting, qname("name"), {"type": "city"})
    city.text = CITY
    country = ET.SubElement(
        setting,
        qname("name"),
        {"type": "country", "key": meta.country_code},
    )
    country.text = "Albania"
    date_el = ET.SubElement(setting, qname("date"), {"when": meta.date})
    date_el.text = meta.date

    langUsage = ET.SubElement(profileDesc, qname("langUsage"))
    l1 = ET.SubElement(langUsage, qname("language"), {"ident": "sq", f"{{{XML_NS}}}lang": "sq"})
    l1.text = "shqip"
    l2 = ET.SubElement(langUsage, qname("language"), {"ident": "en", f"{{{XML_NS}}}lang": "en"})
    l2.text = "English"

    # revisionDesc
    revisionDesc = ET.SubElement(teiHeader, qname("revisionDesc"))
    change = ET.SubElement(
        revisionDesc,
        qname("change"),
        {"when": meta.date},
    )
    who = ET.SubElement(change, qname("name"))
    who.text = "Automatic pipeline"
    change.text = (change.text or "") + ": initial TEI conversion."

    return teiHeader


def split_into_paragraphs(text: str) -> Iterable[str]:
    """
    Simple heuristic: split on double newlines; fall back to single
    lines if there's no blank lines in the file.
    """
    text = text.strip()
    if "\n\n" in text:
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
    else:
        parts = [line.strip() for line in text.splitlines() if line.strip()]
    return parts

def write_plain_day(session, speakers_idx, out_path, license_url):
    root = tei_root(session["title"], session["date"], license_url)

    # --- Attach extra metadata into teiHeader/fileDesc/notesStmt ---
    header = root.find(q("teiHeader"))
    if header is not None:
        fileDesc = header.find(q("fileDesc"))
        if fileDesc is None:
            fileDesc = ET.SubElement(header, q("fileDesc"))
        notesStmt = fileDesc.find(q("notesStmt"))
        if notesStmt is None:
            notesStmt = ET.SubElement(fileDesc, q("notesStmt"))

        # Chair note
        chair_name = session.get("chair_name")
        chair_role = session.get("chair_role")
        if chair_name or chair_role:
            note = ET.SubElement(notesStmt, q("note"), {"type": "chair"})
            parts = []
            if chair_name:
                parts.append(chair_name)
            if chair_role:
                parts.append(" – " + chair_role if chair_name else chair_role)
            note.text = "".join(parts)

        # Agenda / topics
        topics = session.get("topics") or []
        if topics:
            note_ag = ET.SubElement(notesStmt, q("note"), {"type": "agenda"})
            lst = ET.SubElement(note_ag, q("list"))
            for t in topics:
                n = t.get("n")
                it_attrib = {"n": str(n)} if n else {}
                it = ET.SubElement(lst, q("item"), it_attrib)
                it.text = t.get("text")

        # Participants: present / absent / guests
        for key, ntype in [
            ("participants_present", "participants-present"),
            ("participants_absent", "participants-absent"),
            ("participants_guests", "participants-guests"),
        ]:
            val = session.get(key)
            if val:
                note = ET.SubElement(notesStmt, q("note"), {"type": ntype})
                note.text = val

    # --- Body / utterances as before ---
    text = ET.SubElement(root, q("text"))
    body = ET.SubElement(text, q("body"))
    div  = ET.SubElement(body, q("div"), {"type": "session", "when": session["date"]})

    for i, u in enumerate(session["utterances"], 1):
        who_name = u.get("who_name") or u.get("who") or "UNKNOWN"
        pid = speakers_idx.get((who_name or "").lower()) if isinstance(speakers_idx, dict) else None

        who = f"#{pid}" if pid else "#pAL_UNKNOWN"
        u_el = ET.SubElement(div, q("u"), {"xml:id": f"spAL_{i:04d}", "who": who})

        # Preserve paragraph breaks inside the utterance: split on blank lines -> <seg>
        utext = normalize_text(u["text"], preserve_paragraphs=True)
        paras = [p for p in utext.split("\n\n") if p.strip()]
        for para in paras:
            seg = ET.SubElement(u_el, q("seg"))
            seg.text = para



    ET.ElementTree(root).write(out_path, encoding="utf-8", xml_declaration=True)

def build_text_block(meta: DocumentMetadata, body_text: str) -> ET.Element:
    """
    Very simple TEI <text>/<body> with a single <div> and anonymous
    utterances. This is enough for running the ParlaMint validation
    scripts and the linguistic annotators; later you can replace it
    with a richer structure (<u>, speaker IDs, etc.).
    """
    text_el = ET.Element(qname("text"), {"ana": "#reference"})
    body = ET.SubElement(text_el, qname("body"))

    div = ET.SubElement(
        body,
        qname("div"),
        {
            "type": "sitting",
            f"{{{XML_NS}}}id": meta.doc_id + ".sitting",
        },
    )

    # We use a single anonymous utterance; paragraphs become <seg>
    u = ET.SubElement(div, qname("u"), {"who": "#unknown"})
    for i, para in enumerate(split_into_paragraphs(body_text), start=1):
        seg = ET.SubElement(
            u,
            qname("seg"),
            {f"{{{XML_NS}}}id": f"{meta.doc_id}.seg{i}"},
        )
        seg.text = para

    return text_el


def txt_to_tei(txt_path: Path, meta: DocumentMetadata, out_path: Path) -> None:
    """
    Convert a cleaned TXT file to a TEI XML component.
    """
    text = txt_path.read_text(encoding="utf-8")
    # Try to detect the header block: REPUBLIKA… / KUVENDI / <TITLE LINES> / PROCESVERBAL
    detected = extract_meeting_title_from_cleaned(text)
    if detected:
        title, used_idx = detected
        # Put the detected (possibly multi-line) title into the SQ header.
        # If there is no explicit English title, mirror the same string for now.
        meta.title_sq = title
        if not getattr(meta, "title_en", None):
            meta.title_en = title
        body_text = strip_detected_header_block(text, used_idx)
    else:
        body_text = text

    tei_root = make_tei_root(meta, body_text)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    tree = ET.ElementTree(tei_root)
    tree.write(out_path, encoding="utf-8", xml_declaration=True)
