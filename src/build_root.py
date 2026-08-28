# -*- coding: utf-8 -*-
"""
Corpus root generator for ParlaMint-AL:
Generates the master teiCorpus files:
- out/TEI/ParlaMint-AL.xml (plain root)
- out/TEI/ParlaMint-AL.ana.xml (annotated root)
Including corpus-level header, listPerson, listOrg, and component <xi:include> tags.
"""
from __future__ import annotations
from pathlib import Path
from typing import List, Optional
import xml.etree.ElementTree as ET

from .config import PARLIAMENT_NAME, CITY, LICENSE_URL, COUNTRY_CODE, LANGUAGE_CODE

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"
XI_NS = "http://www.w3.org/2001/XInclude"

ET.register_namespace("", TEI_NS)
ET.register_namespace("xml", XML_NS)
ET.register_namespace("xi", XI_NS)


def q(tag: str) -> str:
    return f"{{{TEI_NS}}}{tag}"


def q_xi(tag: str) -> str:
    return f"{{{XI_NS}}}{tag}"


def xml_attr(local: str) -> str:
    return f"{{{XML_NS}}}{local}"


def build_parlamint_root(
    title_sq: Optional[str] = None,
    title_en: Optional[str] = None,
    include_paths: Optional[List[str]] = None,
    is_ana: bool = False,
) -> ET.Element:
    """
    Build the master <teiCorpus> element for ParlaMint-AL.
    """
    corpus_id = f"ParlaMint-{COUNTRY_CODE}.ana" if is_ana else f"ParlaMint-{COUNTRY_CODE}"
    root = ET.Element(
        q("teiCorpus"),
        {
            xml_attr("id"): corpus_id,
            xml_attr("lang"): LANGUAGE_CODE,
        },
    )

    teiHeader = ET.SubElement(root, q("teiHeader"))

    # fileDesc
    fileDesc = ET.SubElement(teiHeader, q("fileDesc"))
    titleStmt = ET.SubElement(fileDesc, q("titleStmt"))
    sq_t = title_sq or f"Korpusi parlamentar shqiptar ParlaMint-AL{'.ana' if is_ana else ''}"
    en_t = title_en or f"Albanian parliamentary corpus ParlaMint-AL{'.ana' if is_ana else ''}"
    ET.SubElement(titleStmt, q("title"), {"type": "main", xml_attr("lang"): "sq"}).text = sq_t
    ET.SubElement(titleStmt, q("title"), {"type": "main", xml_attr("lang"): "en"}).text = en_t

    publicationStmt = ET.SubElement(fileDesc, q("publicationStmt"))
    ET.SubElement(publicationStmt, q("publisher")).text = f"{PARLIAMENT_NAME}; CLARIN ERIC"
    ET.SubElement(publicationStmt, q("pubPlace")).text = CITY
    avail = ET.SubElement(publicationStmt, q("availability"), {"status": "free"})
    ET.SubElement(avail, q("licence"), {"target": LICENSE_URL}).text = "CC BY 4.0"

    sourceDesc = ET.SubElement(fileDesc, q("sourceDesc"))
    bibl = ET.SubElement(sourceDesc, q("bibl"))
    ET.SubElement(bibl, q("title")).text = "Procesverbalet e Kuvendit të Shqipërisë"
    ET.SubElement(bibl, q("idno"), {"type": "URI"}).text = "https://www.kuvendi.gov.al/"

    # encodingDesc
    encodingDesc = ET.SubElement(teiHeader, q("encodingDesc"))
    projectDesc = ET.SubElement(encodingDesc, q("projectDesc"))
    ET.SubElement(projectDesc, q("p")).text = (
        "ParlaMint: Towards comparable parliamentary corpora for European languages."
    )

    # profileDesc with listOrg and listPerson XIncludes
    profileDesc = ET.SubElement(teiHeader, q("profileDesc"))
    settingDesc = ET.SubElement(profileDesc, q("settingDesc"))
    setting = ET.SubElement(settingDesc, q("setting"))
    ET.SubElement(setting, q("name"), {"type": "place"}).text = PARLIAMENT_NAME
    ET.SubElement(setting, q("name"), {"type": "city"}).text = CITY
    ET.SubElement(setting, q("name"), {"type": "country", "key": COUNTRY_CODE}).text = "Albania"

    particDesc = ET.SubElement(profileDesc, q("particDesc"))
    ET.SubElement(particDesc, q_xi("include"), {"href": "ParlaMint-AL-listOrg.xml"})
    ET.SubElement(particDesc, q_xi("include"), {"href": "ParlaMint-AL-listPerson.xml"})

    langUsage = ET.SubElement(profileDesc, q("langUsage"))
    ET.SubElement(langUsage, q("language"), {"ident": "sq", xml_attr("lang"): "sq"}).text = "shqip"
    ET.SubElement(langUsage, q("language"), {"ident": "en", xml_attr("lang"): "en"}).text = "English"

    # XIncludes for component sitting files
    if include_paths:
        for inc_path in sorted(include_paths):
            ET.SubElement(root, q_xi("include"), {"href": inc_path})

    return root


def write_parlamint_root(
    out_path: Path | str,
    include_paths: Optional[List[str]] = None,
    title_sq: Optional[str] = None,
    title_en: Optional[str] = None,
) -> None:
    """Write the plain ParlaMint-AL.xml root file."""
    root = build_parlamint_root(
        title_sq=title_sq,
        title_en=title_en,
        include_paths=include_paths,
        is_ana=False,
    )
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(p, encoding="utf-8", xml_declaration=True)


def build_parlamint_ana_root(
    out_path: Path | str,
    include_paths: Optional[List[str]] = None,
    title_sq: Optional[str] = None,
    title_en: Optional[str] = None,
) -> None:
    """Write the annotated ParlaMint-AL.ana.xml root file."""
    root = build_parlamint_root(
        title_sq=title_sq,
        title_en=title_en,
        include_paths=include_paths,
        is_ana=True,
    )
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(p, encoding="utf-8", xml_declaration=True)
