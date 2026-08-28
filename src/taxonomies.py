# -*- coding: utf-8 -*-
"""
Shared Taxonomies layer for ParlaMint-AL conforming to ParlaMint 5.0.
Generates XML taxonomy files referenced by teiCorpus/encodingDesc/classDecl:
- ParlaMint-taxonomy-speaker_types.xml
- ParlaMint-taxonomy-subcorpus.xml
- ParlaMint-taxonomy-parla.legislature.xml
- ParlaMint-taxonomy-politicalOrientation.xml
- ParlaMint-taxonomy-CHES.xml
"""
from __future__ import annotations
from pathlib import Path
import xml.etree.ElementTree as ET

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"

ET.register_namespace("", TEI_NS)
ET.register_namespace("xml", XML_NS)


def q(tag: str) -> str:
    return f"{{{TEI_NS}}}{tag}"


def xml_attr(local: str) -> str:
    return f"{{{XML_NS}}}{local}"


def make_taxonomy_root(tax_id: str, title_sq: str, title_en: str, desc_sq: str, desc_en: str) -> ET.Element:
    """Build base taxonomy element with header and descriptions."""
    root = ET.Element(q("taxonomy"), {xml_attr("id"): tax_id, xml_attr("lang"): "sq"})
    
    # Title
    t_sq = ET.SubElement(root, q("desc"), {xml_attr("lang"): "sq"})
    ET.SubElement(t_sq, q("term")).text = title_sq
    t_sq.text = desc_sq
    
    t_en = ET.SubElement(root, q("desc"), {xml_attr("lang"): "en"})
    ET.SubElement(t_en, q("term")).text = title_en
    t_en.text = desc_en
    
    return root


def add_category(parent: ET.Element, cat_id: str, term_sq: str, term_en: str, desc_sq: str | None = None, desc_en: str | None = None) -> ET.Element:
    """Add a category with sq/en term and description to a taxonomy or parent category."""
    cat = ET.SubElement(parent, q("category"), {xml_attr("id"): cat_id})
    
    d_sq = ET.SubElement(cat, q("desc"), {xml_attr("lang"): "sq"})
    ET.SubElement(d_sq, q("term")).text = term_sq
    if desc_sq:
        d_sq.text = desc_sq
        
    d_en = ET.SubElement(cat, q("desc"), {xml_attr("lang"): "en"})
    ET.SubElement(d_en, q("term")).text = term_en
    if desc_en:
        d_en.text = desc_en
        
    return cat


def build_speaker_types_taxonomy() -> ET.Element:
    """Build ParlaMint-taxonomy-speaker_types.xml (#chair, #regular, #guest)."""
    tax = make_taxonomy_root(
        "speaker_types",
        "Llojet e folësve",
        "Speaker types",
        "Taksonomia e roleve të folësve në seanca parlamentare",
        "Taxonomy of speaker roles in parliamentary sessions",
    )
    add_category(tax, "chair", "Kryetar / Drejtues", "Chairperson / Moderator", "Drejtuesi i seancës ose komisionit", "The chairperson or moderator of the session or committee")
    add_category(tax, "regular", "Deputet / Folës i rregullt", "Regular speaker / MP", "Deputet me mandat të plotë", "Member of parliament with active mandate")
    add_category(tax, "guest", "I ftuar / Ministër", "Guest speaker / Minister", "Folës i ftuar ose anëtar i qeverisë", "Invited speaker, guest, or government representative")
    return tax


def build_subcorpus_taxonomy() -> ET.Element:
    """Build ParlaMint-taxonomy-subcorpus.xml (#reference, #covid, #war)."""
    tax = make_taxonomy_root(
        "subcorpus",
        "Nënkorpuset",
        "Subcorpora",
        "Taksonomia e nënkorpuseve ParlaMint",
        "Taxonomy of ParlaMint subcorpora",
    )
    add_category(tax, "reference", "Korpusi referencë", "Reference subcorpus", "Pjesa kryesore e seancave parlamentare", "Main body of parliamentary proceedings")
    add_category(tax, "covid", "Periudha COVID-19", "COVID-19 period", "Seanca gjatë pandemisë COVID-19", "Proceedings during the COVID-19 pandemic")
    add_category(tax, "war", "Periudha e Luftës në Ukrainë", "War in Ukraine period", "Seanca gjatë konfliktit në Ukrainë", "Proceedings during the war in Ukraine")
    return tax


def build_legislature_taxonomy() -> ET.Element:
    """Build ParlaMint-taxonomy-parla.legislature.xml (#parla.uni, #parla.sitting, #parla.committee, etc.)."""
    tax = make_taxonomy_root(
        "parla.legislature",
        "Struktura legjislative",
        "Legislative structure",
        "Taksonomia e institucioneve, sesioneve dhe komisioneve",
        "Taxonomy of parliamentary institutions, meetings, and bodies",
    )
    add_category(tax, "parla.uni", "Parlament njëdhomësh", "Unicameral parliament")
    add_category(tax, "parla.national", "Parlament kombëtar", "National parliament")
    add_category(tax, "parla.term", "Legjislatura", "Legislative term")
    add_category(tax, "parla.sitting", "Seancë plenare / mbledhje", "Plenary sitting / meeting")
    add_category(tax, "parla.committee", "Komision parlamentar", "Parliamentary committee")
    add_category(tax, "parla.committee.standing", "Komision i përhershëm", "Standing committee")
    add_category(tax, "parla.meeting.committee", "Mbledhje komisioni", "Committee meeting")
    return tax


def build_political_orientation_taxonomy() -> ET.Element:
    """Build ParlaMint-taxonomy-politicalOrientation.xml."""
    tax = make_taxonomy_root(
        "politicalOrientation",
        "Orientimi politik",
        "Political orientation",
        "Taksonomia e orientimit politik të partive",
        "Taxonomy of political orientations of parties",
    )
    add_category(tax, "left", "E majtë", "Left")
    add_category(tax, "centre-left", "Qendër e majtë", "Centre-left")
    add_category(tax, "centre", "Qendër", "Centre")
    add_category(tax, "centre-right", "Qendër e djathtë", "Centre-right")
    add_category(tax, "right", "E djathtë", "Right")
    return tax


def build_ches_taxonomy() -> ET.Element:
    """Build ParlaMint-taxonomy-CHES.xml."""
    tax = make_taxonomy_root(
        "CHES",
        "Taksonomia CHES",
        "CHES taxonomy",
        "Taksonomia e Chapel Hill Expert Survey",
        "Chapel Hill Expert Survey orientation taxonomy",
    )
    add_category(tax, "CHES.econ_left", "E majtë ekonomike", "Economic left")
    add_category(tax, "CHES.econ_right", "E djathtë ekonomike", "Economic right")
    return tax


def write_all_taxonomies(out_dir: Path | str) -> list[Path]:
    """Write all ParlaMint 5.0 shared taxonomies to out_dir."""
    p = Path(out_dir)
    p.mkdir(parents=True, exist_ok=True)
    
    taxonomies = [
        ("ParlaMint-taxonomy-speaker_types.xml", build_speaker_types_taxonomy()),
        ("ParlaMint-taxonomy-subcorpus.xml", build_subcorpus_taxonomy()),
        ("ParlaMint-taxonomy-parla.legislature.xml", build_legislature_taxonomy()),
        ("ParlaMint-taxonomy-politicalOrientation.xml", build_political_orientation_taxonomy()),
        ("ParlaMint-taxonomy-CHES.xml", build_ches_taxonomy()),
    ]
    
    written_paths: list[Path] = []
    for fname, root_el in taxonomies:
        target = p / fname
        ET.ElementTree(root_el).write(target, encoding="utf-8", xml_declaration=True)
        written_paths.append(target)
        
    return written_paths
