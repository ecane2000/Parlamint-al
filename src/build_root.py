# -*- coding: utf-8 -*-
"""
Master teiCorpus Root Builder for ParlaMint-AL conforming to ParlaMint 5.0:
Constructs ParlaMint-AL.xml with corpus-level headers, editionStmt 5.0, total extents,
editorialDecl, classDecl with shared taxonomy XIncludes, particDesc with authority XIncludes,
and component file XIncludes.
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional
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

TEI_NS = "http://www.tei-c.org/ns/1.0"
XI_NS = "http://www.w3.org/2001/XInclude"
XML_NS = "http://www.w3.org/XML/1998/namespace"

ET.register_namespace("", TEI_NS)
ET.register_namespace("xi", XI_NS)
ET.register_namespace("xml", XML_NS)


def q(tag: str) -> str:
    return f"{{{TEI_NS}}}{tag}"


def xi(tag: str) -> str:
    return f"{{{XI_NS}}}{tag}"


def xml_attr(local: str) -> str:
    return f"{{{XML_NS}}}{local}"


def calculate_corpus_extents(component_paths: List[Path]) -> tuple[int, int]:
    """Calculate total speeches and word counts from component files."""
    total_speeches = 0
    total_words = 0
    for cp in component_paths:
        if not cp.exists():
            continue
        try:
            tree = ET.parse(cp)
            root = tree.getroot()
            u_els = root.findall(f".//{q('u')}")
            total_speeches += len(u_els)
            for seg in root.findall(f".//{q('seg')}"):
                if seg.text:
                    total_words += len(seg.text.split())
        except Exception:
            pass
    return total_speeches, total_words


def build_root_corpus_tei(
    corpus_id: str = "ParlaMint-AL",
    language: str = "sq",
    component_paths: Optional[List[Path | str]] = None,
    total_speeches: int = 0,
    total_words: int = 0,
) -> ET.Element:
    """Build the master teiCorpus root element according to ParlaMint 5.0 specifications."""
    teiCorpus = ET.Element(
        q("teiCorpus"),
        {
            xml_attr("id"): corpus_id,
            xml_attr("lang"): language,
        },
    )

    # teiHeader
    teiHeader = ET.SubElement(teiCorpus, q("teiHeader"))

    # fileDesc
    fileDesc = ET.SubElement(teiHeader, q("fileDesc"))
    titleStmt = ET.SubElement(fileDesc, q("titleStmt"))
    ET.SubElement(titleStmt, q("title"), {"type": "main", xml_attr("lang"): "sq"}).text = (
        "Korpusi parlamentar shqiptar ParlaMint-AL"
    )
    ET.SubElement(titleStmt, q("title"), {"type": "main", xml_attr("lang"): "en"}).text = (
        "Albanian parliamentary corpus ParlaMint-AL"
    )
    respStmt = ET.SubElement(titleStmt, q("respStmt"))
    ET.SubElement(respStmt, q("resp"), {xml_attr("lang"): "sq"}).text = "Përgatitur nga"
    ET.SubElement(respStmt, q("resp"), {xml_attr("lang"): "en"}).text = "Prepared by"
    ET.SubElement(respStmt, q("name")).text = "ParlaMint-AL"
    funder = ET.SubElement(titleStmt, q("funder"))
    ET.SubElement(funder, q("orgName"), {xml_attr("lang"): "sq"}).text = "CLARIN ERIC"
    ET.SubElement(funder, q("orgName"), {xml_attr("lang"): "en"}).text = "CLARIN ERIC"

    # editionStmt
    editionStmt = ET.SubElement(fileDesc, q("editionStmt"))
    ET.SubElement(editionStmt, q("edition")).text = PARLAMINT_VERSION

    # extent
    extent = ET.SubElement(fileDesc, q("extent"))
    ET.SubElement(
        extent,
        q("measure"),
        {"unit": "speeches", "quantity": str(total_speeches), xml_attr("lang"): "sq"},
    ).text = f"{total_speeches} fjalime"
    ET.SubElement(
        extent,
        q("measure"),
        {"unit": "speeches", "quantity": str(total_speeches), xml_attr("lang"): "en"},
    ).text = f"{total_speeches} speeches"
    ET.SubElement(
        extent,
        q("measure"),
        {"unit": "words", "quantity": str(total_words), xml_attr("lang"): "sq"},
    ).text = f"{total_words} fjalë"
    ET.SubElement(
        extent,
        q("measure"),
        {"unit": "words", "quantity": str(total_words), xml_attr("lang"): "en"},
    ).text = f"{total_words} words"

    # publicationStmt
    publicationStmt = ET.SubElement(fileDesc, q("publicationStmt"))
    ET.SubElement(publicationStmt, q("publisher")).text = f"{PARLIAMENT_NAME}; CLARIN ERIC"
    ET.SubElement(publicationStmt, q("idno"), {"type": "URI", "subtype": "handle"}).text = HANDLE_URL
    avail = ET.SubElement(publicationStmt, q("availability"), {"status": "free"})
    ET.SubElement(avail, q("licence")).text = LICENSE_URL
    ET.SubElement(avail, q("p"), {xml_attr("lang"): "sq"}).text = (
        "Ky punim publikohet nën licencën Creative Commons Attribution 4.0 International License (CC BY 4.0)."
    )
    ET.SubElement(avail, q("p"), {xml_attr("lang"): "en"}).text = (
        "This work is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0)."
    )
    ET.SubElement(publicationStmt, q("date"), {"when": CORPUS_RELEASE_DATE}).text = CORPUS_RELEASE_DATE

    # sourceDesc
    sourceDesc = ET.SubElement(fileDesc, q("sourceDesc"))
    bibl = ET.SubElement(sourceDesc, q("bibl"))
    ET.SubElement(bibl, q("title"), {"type": "main", xml_attr("lang"): "sq"}).text = (
        "Procesverbalet e Kuvendit të Shqipërisë"
    )
    ET.SubElement(bibl, q("idno"), {"type": "URI"}).text = "https://www.kuvendi.gov.al/"

    # encodingDesc
    encodingDesc = ET.SubElement(teiHeader, q("encodingDesc"))
    projectDesc = ET.SubElement(encodingDesc, q("projectDesc"))
    ET.SubElement(projectDesc, q("p"), {xml_attr("lang"): "sq"}).text = (
        "ParlaMint: Drejt korpuseve të krahasueshme parlamentare për gjuhët europiane."
    )
    ET.SubElement(projectDesc, q("p"), {xml_attr("lang"): "en"}).text = (
        "ParlaMint: Towards comparable parliamentary corpora for European languages."
    )

    editorialDecl = ET.SubElement(encodingDesc, q("editorialDecl"))
    ET.SubElement(editorialDecl, q("correction")).append(
        ET.Element(q("p"), {xml_attr("lang"): "en"})
    )
    editorialDecl.find(f".//{q('correction')}/{q('p')}").text = "No automatic correction applied except normalization of OCR characters."
    ET.SubElement(editorialDecl, q("normalization")).append(
        ET.Element(q("p"), {xml_attr("lang"): "en"})
    )
    editorialDecl.find(f".//{q('normalization')}/{q('p')}").text = "Standard typography and space normalization."
    ET.SubElement(editorialDecl, q("segmentation")).append(
        ET.Element(q("p"), {xml_attr("lang"): "en"})
    )
    editorialDecl.find(f".//{q('segmentation')}/{q('p')}").text = "Speeches are segmented into paragraphs corresponding to transcript blocks."

    # Shared Taxonomies in classDecl
    classDecl = ET.SubElement(encodingDesc, q("classDecl"))
    for tax_file in (
        "ParlaMint-taxonomy-speaker_types.xml",
        "ParlaMint-taxonomy-subcorpus.xml",
        "ParlaMint-taxonomy-parla.legislature.xml",
        "ParlaMint-taxonomy-politicalOrientation.xml",
        "ParlaMint-taxonomy-CHES.xml",
    ):
        classDecl.append(ET.Element(xi("include"), {"href": tax_file}))

    # profileDesc
    profileDesc = ET.SubElement(teiHeader, q("profileDesc"))
    settingDesc = ET.SubElement(profileDesc, q("settingDesc"))
    setting = ET.SubElement(settingDesc, q("setting"))
    ET.SubElement(setting, q("name"), {"type": "address"}).text = PARLIAMENT_NAME
    ET.SubElement(setting, q("name"), {"type": "city"}).text = CITY
    ET.SubElement(setting, q("name"), {"type": "country", "key": COUNTRY_CODE}).text = "Albania"

    # particDesc with XIncludes
    particDesc = ET.SubElement(profileDesc, q("particDesc"))
    particDesc.append(ET.Element(xi("include"), {"href": "ParlaMint-AL-listOrg.xml"}))
    particDesc.append(ET.Element(xi("include"), {"href": "ParlaMint-AL-listPerson.xml"}))

    langUsage = ET.SubElement(profileDesc, q("langUsage"))
    ET.SubElement(langUsage, q("language"), {"ident": "sq", xml_attr("lang"): "sq"}).text = "shqip"
    ET.SubElement(langUsage, q("language"), {"ident": "en", xml_attr("lang"): "en"}).text = "English"

    # revisionDesc
    revisionDesc = ET.SubElement(teiHeader, q("revisionDesc"))
    change = ET.SubElement(revisionDesc, q("change"), {"when": CORPUS_RELEASE_DATE})
    ET.SubElement(change, q("name")).text = "ParlaMint-AL"
    change.text = ": ParlaMint 5.0 teiCorpus master root."

    # Component XIncludes
    if component_paths:
        for cpath in sorted(component_paths, key=lambda x: str(x)):
            href = Path(cpath).as_posix()
            teiCorpus.append(ET.Element(xi("include"), {"href": href}))

    return teiCorpus


def write_root_corpus_file(
    out_file: Path | str,
    component_paths: Optional[List[Path | str]] = None,
    is_ana: bool = False,
) -> Path:
    """Build and write ParlaMint-AL.xml or ParlaMint-AL.ana.xml."""
    out_p = Path(out_file)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    c_paths = [Path(c) for c in (component_paths or [])]
    total_speeches, total_words = calculate_corpus_extents(c_paths)

    cid = "ParlaMint-AL.ana" if is_ana else "ParlaMint-AL"
    # Format component href relative to out_p directory
    rel_paths = []
    for cp in c_paths:
        try:
            rel = cp.relative_to(out_p.parent).as_posix()
        except ValueError:
            rel = cp.as_posix()
        rel_paths.append(rel)

    root = build_root_corpus_tei(
        corpus_id=cid,
        component_paths=rel_paths,
        total_speeches=total_speeches,
        total_words=total_words,
    )

    ET.ElementTree(root).write(out_p, encoding="utf-8", xml_declaration=True)
    return out_p
