# -*- coding: utf-8 -*-
"""
TEI Component Encoding layer for ParlaMint-AL:
Transforms segmented sitting objects and metadata into standard ParlaMint TEI component files.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

from .config import PARLIAMENT_NAME, CITY, LICENSE_URL, COUNTRY_CODE, LANGUAGE_CODE
from .metadata import DocumentMetadata
from .resolve_speakers import SpeakerResolution
from .segment import SittingBlock, SpeechBlock, split_into_paragraphs
from .utils import safe_xml_text, squash_ws

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"

ET.register_namespace("", TEI_NS)
ET.register_namespace("xml", XML_NS)


def qname(local: str) -> str:
    """Build a namespaced TEI tag."""
    return f"{{{TEI_NS}}}{local}"


def xml_attr(local: str) -> str:
    """Build a namespaced xml:* attribute name."""
    return f"{{{XML_NS}}}{local}"


def make_tei_root(meta: DocumentMetadata) -> ET.Element:
    """Build the base TEI element for a component day file."""
    return ET.Element(
        qname("TEI"),
        {
            xml_attr("id"): meta.doc_id,
            xml_attr("lang"): meta.language or LANGUAGE_CODE,
            "ana": "#parla.sitting #reference",
        },
    )


def build_tei_header(meta: DocumentMetadata) -> ET.Element:
    """
    Build a standard ParlaMint teiHeader for a single parliamentary day/sitting.
    """
    teiHeader = ET.Element(qname("teiHeader"))

    # fileDesc
    fileDesc = ET.SubElement(teiHeader, qname("fileDesc"))
    titleStmt = ET.SubElement(fileDesc, qname("titleStmt"))

    title_sq = meta.title_sq or f"{PARLIAMENT_NAME}, procesverbal, {meta.date}"
    title_en = meta.title_en or f"Parliament of Albania, minutes, {meta.date}"

    ET.SubElement(titleStmt, qname("title"), {"type": "main", xml_attr("lang"): "sq"}).text = safe_xml_text(title_sq)
    ET.SubElement(titleStmt, qname("title"), {"type": "main", xml_attr("lang"): "en"}).text = safe_xml_text(title_en)

    meeting_el = ET.SubElement(titleStmt, qname("meeting"))
    if meta.meeting_type:
        meeting_el.set("ana", f"#{meta.meeting_type}")
    if meta.date:
        ET.SubElement(meeting_el, qname("date"), {"when": meta.date}).text = meta.date
    if meta.chair_name:
        chair_text = meta.chair_name
        if meta.chair_role:
            chair_text += f" – {meta.chair_role}"
        ET.SubElement(meeting_el, qname("chair")).text = safe_xml_text(chair_text)

    # publicationStmt
    publicationStmt = ET.SubElement(fileDesc, qname("publicationStmt"))
    ET.SubElement(publicationStmt, qname("publisher")).text = f"{PARLIAMENT_NAME}; CLARIN ERIC"
    ET.SubElement(publicationStmt, qname("pubPlace")).text = CITY
    avail = ET.SubElement(publicationStmt, qname("availability"), {"status": "free"})
    ET.SubElement(avail, qname("licence"), {"target": LICENSE_URL}).text = "CC BY 4.0"
    if meta.date:
        ET.SubElement(publicationStmt, qname("date"), {"when": meta.date}).text = meta.date

    # sourceDesc
    sourceDesc = ET.SubElement(fileDesc, qname("sourceDesc"))
    bibl = ET.SubElement(sourceDesc, qname("bibl"))
    ET.SubElement(bibl, qname("title")).text = "Procesverbal i Kuvendit të Shqipërisë"
    if meta.source_url:
        ET.SubElement(bibl, qname("idno"), {"type": "URL"}).text = meta.source_url
    if meta.date:
        ET.SubElement(bibl, qname("date"), {"when": meta.date}).text = meta.date

    # encodingDesc
    encodingDesc = ET.SubElement(teiHeader, qname("encodingDesc"))
    projectDesc = ET.SubElement(encodingDesc, qname("projectDesc"))
    ET.SubElement(projectDesc, qname("p")).text = (
        "ParlaMint-AL: korpus i krahasueshëm i seancave parlamentare, i përputhshëm me ParlaMint v5."
    )

    # profileDesc
    profileDesc = ET.SubElement(teiHeader, qname("profileDesc"))
    settingDesc = ET.SubElement(profileDesc, qname("settingDesc"))
    setting = ET.SubElement(settingDesc, qname("setting"))
    ET.SubElement(setting, qname("name"), {"type": "place"}).text = PARLIAMENT_NAME
    ET.SubElement(setting, qname("name"), {"type": "city"}).text = CITY
    ET.SubElement(setting, qname("name"), {"type": "country", "key": meta.country_code or COUNTRY_CODE}).text = "Albania"
    if meta.date:
        ET.SubElement(setting, qname("date"), {"when": meta.date}).text = meta.date

    langUsage = ET.SubElement(profileDesc, qname("langUsage"))
    ET.SubElement(langUsage, qname("language"), {"ident": "sq", xml_attr("lang"): "sq"}).text = "shqip"
    ET.SubElement(langUsage, qname("language"), {"ident": "en", xml_attr("lang"): "en"}).text = "English"

    # revisionDesc
    revisionDesc = ET.SubElement(teiHeader, qname("revisionDesc"))
    ET.SubElement(revisionDesc, qname("change"), {"when": meta.date or ""}).text = (
        "Initial conversion to ParlaMint TEI XML."
    )

    return teiHeader


def build_text_block_from_segments(
    meta: DocumentMetadata,
    sitting: SittingBlock,
    resolutions: Optional[Dict[str, SpeakerResolution]] = None,
) -> ET.Element:
    """
    Build the <text>/<body>/<div> block containing speech turns (<u>) and segments (<seg>).
    """
    text_el = ET.Element(qname("text"), {xml_attr("lang"): meta.language or LANGUAGE_CODE})
    body = ET.SubElement(text_el, qname("body"))
    div = ET.SubElement(body, qname("div"), {"type": "debateSection"})

    seg_global_idx = 1
    for sp_idx, speech in enumerate(sitting.speeches, start=1):
        res = (resolutions or {}).get(speech.speech_id)
        person_id = res.person_id if res and res.person_id else "AL_PERS_Unknown"
        who_ref = f"#{person_id}" if not person_id.startswith("#") else person_id

        u_attrs = {
            xml_attr("id"): f"{meta.doc_id}.u{sp_idx}",
            "who": who_ref,
            "ana": "#parla.speaker",
        }
        u_el = ET.SubElement(div, qname("u"), u_attrs)

        for p_text in speech.paragraphs:
            clean_p = squash_ws(safe_xml_text(p_text)).strip()
            if not clean_p:
                continue

            # Check if paragraph is an editorial note or interruption
            if clean_p.startswith("(") and clean_p.endswith(")"):
                note_el = ET.SubElement(u_el, qname("note"), {"type": "comment"})
                note_el.text = clean_p
            else:
                seg_attrs = {xml_attr("id"): f"{meta.doc_id}.seg{seg_global_idx}"}
                seg_global_idx += 1
                seg_el = ET.SubElement(u_el, qname("seg"), seg_attrs)
                seg_el.text = clean_p

    return text_el


def build_text_block_from_plain_text(meta: DocumentMetadata, body_text: str) -> ET.Element:
    """Fallback: convert raw plain text with anonymous single utterance."""
    text_el = ET.Element(qname("text"), {xml_attr("lang"): meta.language or LANGUAGE_CODE})
    body = ET.SubElement(text_el, qname("body"))
    div = ET.SubElement(body, qname("div"), {"type": "debateSection"})
    u = ET.SubElement(div, qname("u"), {xml_attr("id"): f"{meta.doc_id}.u1", "who": "#AL_PERS_Unknown"})

    paras = split_into_paragraphs(body_text)
    for i, p in enumerate(paras, start=1):
        seg = ET.SubElement(u, qname("seg"), {xml_attr("id"): f"{meta.doc_id}.seg{i}"})
        seg.text = squash_ws(safe_xml_text(p))

    return text_el


def segmented_to_tei(
    sitting: SittingBlock,
    meta: DocumentMetadata,
    out_path: Path | str,
    resolutions: Optional[Dict[str, SpeakerResolution]] = None,
) -> None:
    """Write a complete segmented sitting to a ParlaMint TEI XML file."""
    root = make_tei_root(meta)
    root.append(build_tei_header(meta))
    root.append(build_text_block_from_segments(meta, sitting, resolutions))

    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(p, encoding="utf-8", xml_declaration=True)


def txt_to_tei(txt_path: Path | str, meta: DocumentMetadata, out_path: Path | str) -> None:
    """Convert a plain text file directly to TEI."""
    text = Path(txt_path).read_text(encoding="utf-8", errors="ignore")
    root = make_tei_root(meta)
    root.append(build_tei_header(meta))
    root.append(build_text_block_from_plain_text(meta, text))

    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(p, encoding="utf-8", xml_declaration=True)


def write_plain_day(
    session: dict,
    speakers_idx: Dict[str, str],
    out_path: str,
    license_url: str = LICENSE_URL,
    eventTypeAna: Optional[str] = "#parla.sitting",
) -> None:
    """
    Backward-compatibility function matching earlier prototype signature.
    """
    date = session.get("date") or "2025-01-01"
    doc_id = f"ParlaMint-AL_{date.replace('/', '-')}"
    meta = DocumentMetadata(
        doc_id=doc_id,
        date=date,
        title_sq=session.get("title"),
        title_en=f"Parliament of Albania, minutes, {date}",
        chair_name=session.get("chair_name"),
        chair_role=session.get("chair_role"),
    )

    speeches = []
    resolutions: Dict[str, SpeakerResolution] = {}
    for i, u in enumerate(session.get("utterances", []), start=1):
        sp_id = f"{doc_id}.u{i}"
        raw_name = u.get("who_name") or "UNKNOWN"
        speeches.append(
            SpeechBlock(
                speech_id=sp_id,
                raw_speaker_label=raw_name,
                paragraphs=u.get("paragraphs", []),
            )
        )
        pid = speakers_idx.get(raw_name.lower()) or "AL_PERS_Unknown"
        resolutions[sp_id] = SpeakerResolution(
            raw_label=raw_name,
            normalized_label=raw_name.lower(),
            person_id=pid,
            confidence="exact" if pid != "AL_PERS_Unknown" else "unresolved",
        )

    sitting = SittingBlock(doc_id=doc_id, date=date, speeches=speeches)
    segmented_to_tei(sitting, meta, out_path, resolutions)
