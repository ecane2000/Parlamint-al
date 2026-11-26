# -*- coding: utf-8 -*-
"""
TEI Component Encoding layer for ParlaMint-AL conforming strictly to ParlaMint 5.0:
Transforms segmented sitting objects and metadata into valid ParlaMint 5.0 TEI component files.
Resolves all 19 component schema diagnostics from the technical audit.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

from .config import (
    PARLIAMENT_NAME,
    PARLIAMENT_NAME_EN,
    PARLAMINT_VERSION,
    CORPUS_RELEASE_DATE,
    HANDLE_URL,
    LICENSE_URL,
    COUNTRY_CODE,
    LANGUAGE_CODE,
    CITY,
)
from .metadata import DocumentMetadata
from .resolve_speakers import SpeakerResolution
from .segment import SittingBlock, SpeechBlock, DiscourseItem
from .utils import safe_xml_text, squash_ws, count_words

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


def _indent_xml(element: ET.Element, level: int = 0) -> None:
    children = list(element)
    if not children:
        return

    for child in children:
        _indent_xml(child, level + 1)

    if (element.text and element.text.strip()) or any(
        child.tail and child.tail.strip() for child in children
    ):
        return

    element.text = "\n" + "  " * (level + 1)
    for child in children[:-1]:
        child.tail = "\n" + "  " * (level + 1)
    children[-1].tail = "\n" + "  " * level


def make_tei_root(meta: DocumentMetadata) -> ET.Element:
    """Build the root TEI element for a component day file with required attributes."""
    ana_type = "#parla.committee.standing #reference" if meta.meeting_type == "parla.committee" else "#parla.sitting #reference"
    return ET.Element(
        qname("TEI"),
        {
            xml_attr("id"): meta.doc_id,
            xml_attr("lang"): meta.language or LANGUAGE_CODE,
            "ana": ana_type,
        },
    )


def build_tei_header(
    meta: DocumentMetadata,
    num_speeches: int = 0,
    num_words: int = 0,
    tag_counts: Optional[Dict[str, int]] = None,
) -> ET.Element:
    """
    Build a strictly compliant ParlaMint 5.0 teiHeader for a component sitting.
    """
    teiHeader = ET.Element(qname("teiHeader"))

    # fileDesc
    fileDesc = ET.SubElement(teiHeader, qname("fileDesc"))
    titleStmt = ET.SubElement(fileDesc, qname("titleStmt"))
    corpus_id = f"ParlaMint-{meta.country_code}"
    title_sq = (
        f"Korpusi parlamentar shqiptar {corpus_id}, "
        f"{meta.date} [ParlaMint SAMPLE]"
    )

    title_en = (
        f"Albanian parliamentary corpus {corpus_id}, "
        f"{meta.date} [ParlaMint SAMPLE]"
    )

    title_sq = meta.title_sq or f"{PARLIAMENT_NAME}, procesverbal, {meta.date}"
    title_en = meta.title_en or f"{PARLIAMENT_NAME_EN}, minutes, {meta.date}"



    ET.SubElement(titleStmt, qname("title"), {"type": "main", xml_attr("lang"): "sq"}).text = safe_xml_text(title_sq)
    ET.SubElement(titleStmt, qname("title"), {"type": "main", xml_attr("lang"): "en"}).text = safe_xml_text(title_en)

    # Valid meeting elements (text content only with corresp, n, ana)
    leg_id = meta.legislature_id or "XI"
    ET.SubElement(
        titleStmt,
        qname("meeting"),
        {
            "corresp": "#AL_ORG_Kuvendi",
            "n": leg_id,
            "ana": f"#parla.uni #parla.term #KUV.{leg_id}",
        },
    ).text = f"Legjislatura {leg_id}"

    session_ana = "#parla.committee.standing #parla.meeting.committee" if meta.meeting_type == "parla.committee" else "#parla.sitting #reference"
    session_label = "Mbledhje komisioni" if meta.meeting_type == "parla.committee" else "Dita e mbledhjes"
    body_refs = " ".join(
        f"#{b.strip()}" if not b.strip().startswith("#") else b.strip()
        for b in (meta.body_org_ids or "AL_ORG_Kuvendi").split(";")
        if b.strip()
    ) or "#AL_ORG_Kuvendi"
    ET.SubElement(
        titleStmt,
        qname("meeting"),
        {
            "corresp": body_refs,
            "ana": session_ana,
        },
    ).text = session_label

    respStmt = ET.SubElement(titleStmt, qname("respStmt"))
    ET.SubElement(respStmt, qname("resp"), {xml_attr("lang"): "sq"}).text = "Përgatitur nga"
    ET.SubElement(respStmt, qname("resp"), {xml_attr("lang"): "en"}).text = "Prepared by"
    ET.SubElement(respStmt, qname("name")).text = "ParlaMint-AL"

    funder = ET.SubElement(titleStmt, qname("funder"))
    ET.SubElement(funder, qname("orgName"), {xml_attr("lang"): "sq"}).text = "CLARIN ERIC"
    ET.SubElement(funder, qname("orgName"), {xml_attr("lang"): "en"}).text = "CLARIN ERIC"

    # editionStmt (Diagnostic 7)
    editionStmt = ET.SubElement(fileDesc, qname("editionStmt"))
    ET.SubElement(editionStmt, qname("edition")).text = PARLAMINT_VERSION

    # extent (Diagnostic 8)
    extent = ET.SubElement(fileDesc, qname("extent"))
    ET.SubElement(
        extent,
        qname("measure"),
        {"unit": "speeches", "quantity": str(num_speeches), xml_attr("lang"): "sq"},
    ).text = f"{num_speeches} fjalime"
    ET.SubElement(
        extent,
        qname("measure"),
        {"unit": "speeches", "quantity": str(num_speeches), xml_attr("lang"): "en"},
    ).text = f"{num_speeches} speeches"
    ET.SubElement(
        extent,
        qname("measure"),
        {"unit": "words", "quantity": str(num_words), xml_attr("lang"): "sq"},
    ).text = f"{num_words} fjalë"
    ET.SubElement(
        extent,
        qname("measure"),
        {"unit": "words", "quantity": str(num_words), xml_attr("lang"): "en"},
    ).text = f"{num_words} words"

    # publicationStmt (Diagnostics 9-12)
    publicationStmt = ET.SubElement(fileDesc, qname("publicationStmt"))
    ET.SubElement(publicationStmt, qname("publisher")).text = f"{PARLIAMENT_NAME}; CLARIN ERIC"
    ET.SubElement(publicationStmt, qname("idno"), {"type": "URI", "subtype": "handle"}).text = HANDLE_URL

    avail = ET.SubElement(publicationStmt, qname("availability"), {"status": "free"})
    ET.SubElement(avail, qname("licence")).text = LICENSE_URL
    ET.SubElement(avail, qname("p"), {xml_attr("lang"): "sq"}).text = (
        "Ky punim publikohet nën licencën Creative Commons Attribution 4.0 International License (CC BY 4.0)."
    )
    ET.SubElement(avail, qname("p"), {xml_attr("lang"): "en"}).text = (
        "This work is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0)."
    )
    ET.SubElement(publicationStmt, qname("date"), {"when": CORPUS_RELEASE_DATE}).text = CORPUS_RELEASE_DATE

    # sourceDesc (Diagnostic 13)
    sourceDesc = ET.SubElement(fileDesc, qname("sourceDesc"))
    bibl = ET.SubElement(sourceDesc, qname("bibl"))
    ET.SubElement(bibl, qname("title"), {"type": "main", xml_attr("lang"): "sq"}).text = (
        "Procesverbal i Kuvendit të Shqipërisë"
    )
    source_url = meta.source_url or "https://www.kuvendi.gov.al/"
    ET.SubElement(bibl, qname("idno"), {"type": "URI"}).text = source_url
    if meta.date:
        ET.SubElement(bibl, qname("date"), {"when": meta.date}).text = meta.date

    # encodingDesc (Diagnostics 14-15)
    encodingDesc = ET.SubElement(teiHeader, qname("encodingDesc"))
    projectDesc = ET.SubElement(encodingDesc, qname("projectDesc"))
    ET.SubElement(projectDesc, qname("p"), {xml_attr("lang"): "sq"}).text = (
        "ParlaMint-AL: korpus i krahasueshëm i seancave parlamentare, i përputhshëm me ParlaMint v5."
    )
    ET.SubElement(projectDesc, qname("p"), {xml_attr("lang"): "en"}).text = (
        "ParlaMint-AL: comparable parliamentary corpus of Albania, conforming to ParlaMint v5."
    )

    tagsDecl = ET.SubElement(encodingDesc, qname("tagsDecl"))
    ns_el = ET.SubElement(tagsDecl, qname("namespace"), {"name": "http://www.tei-c.org/ns/1.0"})
    counts = tag_counts or {
        "text": 1,
        "body": 1,
        "div": 1,
        "u": num_speeches,
        "seg": max(1, num_speeches),
    }
    for tag_name in ("text", "body", "div", "head", "note", "u", "seg", "vocal", "kinesic"):
        if tag_name in counts and counts[tag_name] > 0:
            ET.SubElement(ns_el, qname("tagUsage"), {"gi": tag_name, "occurs": str(counts[tag_name])})

    # profileDesc (Diagnostics 16-17)
    profileDesc = ET.SubElement(teiHeader, qname("profileDesc"))
    settingDesc = ET.SubElement(profileDesc, qname("settingDesc"))
    setting = ET.SubElement(settingDesc, qname("setting"))
    ET.SubElement(setting, qname("name"), {"type": "address"}).text = PARLIAMENT_NAME
    ET.SubElement(setting, qname("name"), {"type": "city"}).text = CITY
    ET.SubElement(setting, qname("name"), {"type": "country", "key": meta.country_code or COUNTRY_CODE}).text = "Albania"
    if meta.date:
        ET.SubElement(setting, qname("date"), {"when": meta.date}).text = meta.date

    langUsage = ET.SubElement(profileDesc, qname("langUsage"))
    ET.SubElement(langUsage, qname("language"), {"ident": "sq", xml_attr("lang"): "sq"}).text = "shqip"
    ET.SubElement(langUsage, qname("language"), {"ident": "en", xml_attr("lang"): "en"}).text = "English"

    # revisionDesc
    revisionDesc = ET.SubElement(teiHeader, qname("revisionDesc"))
    change = ET.SubElement(revisionDesc, qname("change"), {"when": CORPUS_RELEASE_DATE})
    ET.SubElement(change, qname("name")).text = "ParlaMint-AL"
    change.text = ": Initial conversion to ParlaMint 5.0 TEI XML."

    return teiHeader


def build_text_block_from_segments(
    meta: DocumentMetadata,
    sitting: SittingBlock,
    resolutions: Optional[Dict[str, SpeakerResolution]] = None,
) -> tuple[ET.Element, int, Dict[str, int]]:
    """
    Build the <text>/<body>/<div> block containing speech turns (<u>), segments (<seg>),
    and discourse events (<vocal>, <kinesic>, <note>).
    Returns (text_element, total_words, tag_counts).
    """
    text_el = ET.Element(qname("text"), {"ana": "#reference"})
    body = ET.SubElement(text_el, qname("body"))
    div = ET.SubElement(body, qname("div"), {"type": "debateSection"})

    tag_counts = {
        "text": 1,
        "body": 1,
        "div": 1,
        "u": 0,
        "seg": 0,
        "vocal": 0,
        "kinesic": 0,
        "note": 0,
    }
    total_words = 0
    seg_global_idx = 1

    for sp_idx, speech in enumerate(sitting.speeches, start=1):
        res = (resolutions or {}).get(speech.speech_id)
        role = res.role if res and res.role else "#regular"

        u_attrs = {
            xml_attr("id"): f"{meta.doc_id}.u{sp_idx}",
            "ana": role,
        }
        # ParlaMint 5.0: Only add @who if speaker is resolved; omit @who if genuinely unknown
        if res and res.person_id:
            person_ref = f"#{res.person_id}" if not res.person_id.startswith("#") else res.person_id
            u_attrs["who"] = person_ref

        u_el = ET.SubElement(div, qname("u"), u_attrs)
        tag_counts["u"] += 1

        for item in speech.items:
            clean_item_text = squash_ws(safe_xml_text(item.text)).strip()
            if not clean_item_text:
                continue

            if item.kind == "vocal":
                tag_counts["vocal"] += 1
                v_el = ET.SubElement(u_el, qname("vocal"), {"type": item.type_attr or "interruption"})
                ET.SubElement(v_el, qname("desc")).text = clean_item_text

            elif item.kind == "kinesic":
                tag_counts["kinesic"] += 1
                k_el = ET.SubElement(u_el, qname("kinesic"), {"type": item.type_attr or "applause"})
                ET.SubElement(k_el, qname("desc")).text = clean_item_text

            elif item.kind == "note":
                tag_counts["note"] += 1
                n_el = ET.SubElement(u_el, qname("note"), {"type": item.type_attr or "comment"})
                n_el.text = clean_item_text

            else:  # kind == "seg"
                tag_counts["seg"] += 1
                seg_attrs = {xml_attr("id"): f"{meta.doc_id}.seg{seg_global_idx}"}
                seg_global_idx += 1
                seg_el = ET.SubElement(u_el, qname("seg"), seg_attrs)
                seg_el.text = clean_item_text
                total_words += count_words(clean_item_text)

    return text_el, total_words, tag_counts


def segmented_to_tei(
    sitting: SittingBlock,
    meta: DocumentMetadata,
    out_path: Path | str,
    resolutions: Optional[Dict[str, SpeakerResolution]] = None,
) -> None:
    """Write a complete segmented sitting to a ParlaMint 5.0 TEI XML file."""
    text_el, total_words, tag_counts = build_text_block_from_segments(meta, sitting, resolutions)
    num_speeches = len(sitting.speeches)

    root = make_tei_root(meta)
    root.append(build_tei_header(meta, num_speeches=num_speeches, num_words=total_words, tag_counts=tag_counts))
    root.append(text_el)

    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    _indent_xml(root)
    ET.ElementTree(root).write(p, encoding="utf-8", xml_declaration=True)


def txt_to_tei(txt_path: Path | str, meta: DocumentMetadata, out_path: Path | str) -> None:
    """Fallback plain text converter."""
    from .segment import segment_document
    text = Path(txt_path).read_text(encoding="utf-8", errors="ignore")
    sitting = segment_document(text, doc_id=meta.doc_id, date=meta.date)
    segmented_to_tei(sitting, meta, out_path)
