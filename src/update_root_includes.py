# -*- coding: utf-8 -*-
"""
Root include updater for ParlaMint-AL:
Scans the plain and ana component directories and refreshes <xi:include> tags
in the master ParlaMint-AL.xml and ParlaMint-AL.ana.xml root files.
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, List
import xml.etree.ElementTree as ET

from .build_root import write_root_corpus_file

TEI_NS = "http://www.tei-c.org/ns/1.0"
XI_NS = "http://www.w3.org/2001/XInclude"
XML_NS = "http://www.w3.org/XML/1998/namespace"

ET.register_namespace("", TEI_NS)
ET.register_namespace("xi", XI_NS)
ET.register_namespace("xml", XML_NS)


def q_xi(tag: str) -> str:
    return f"{{{XI_NS}}}{tag}"


def find_components_by_year(components_dir: Path | str) -> Dict[str, List[Path]]:
    """Group component XML files in components_dir by year."""
    p = Path(components_dir)
    grouped: Dict[str, List[Path]] = {}
    if not p.exists():
        return grouped

    for xml_file in sorted(p.glob("*.xml")):
        m = re.search(r"(\d{4})-\d{2}-\d{2}", xml_file.name)
        year = m.group(1) if m else "misc"
        grouped.setdefault(year, []).append(xml_file)

    return grouped


def update_parlamint_root(
    root_path: Path | str,
    components_dir: Path | str,
    href_prefix: str = "plain/",
) -> None:
    """Update or create ParlaMint-AL.xml with includes for all plain component files."""
    r_path = Path(root_path)
    c_dir = Path(components_dir)

    component_files = []
    if c_dir.exists():
        for comp in sorted(c_dir.glob("*.xml")):
            if "listPerson" in comp.name or "listOrg" in comp.name or "taxonomy" in comp.name or comp.name.startswith("ParlaMint-AL.xml"):
                continue
            component_files.append(comp)

    write_root_corpus_file(
        out_file=r_path,
        component_paths=component_files,
        is_ana=False,
    )


def update_parlamint_ana_root(
    root_path: Path | str,
    components_dir: Path | str,
    href_prefix: str = "ana/",
) -> None:
    """Update or create ParlaMint-AL.ana.xml with includes for all annotated component files."""
    r_path = Path(root_path)
    c_dir = Path(components_dir)

    component_files = []
    if c_dir.exists():
        for comp in sorted(c_dir.glob("*.ana.xml")):
            component_files.append(comp)

    write_root_corpus_file(
        out_file=r_path,
        component_paths=component_files,
        is_ana=True,
    )
