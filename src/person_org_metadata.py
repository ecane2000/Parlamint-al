# -*- coding: utf-8 -*-
"""
Person and Organisation metadata layer for ParlaMint-AL:
Loads speaker/MP data, party affiliations, and organisations from CSV files
and generates ParlaMint-AL-listPerson.xml and ParlaMint-AL-listOrg.xml.
"""
from __future__ import annotations
import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional
import xml.etree.ElementTree as ET

TEI_NS = "http://www.tei-c.org/ns/1.0"
XML_NS = "http://www.w3.org/XML/1998/namespace"

ET.register_namespace("", TEI_NS)
ET.register_namespace("xml", XML_NS)


def q(tag: str) -> str:
    return f"{{{TEI_NS}}}{tag}"


def xml_attr(local: str) -> str:
    return f"{{{XML_NS}}}{local}"


@dataclass
class Affiliation:
    """Represents a temporal affiliation of a person with an organization."""
    org_id: str
    role: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None


@dataclass
class PersonMetadata:
    """Metadata for a speaker / Member of Parliament."""
    person_id: str
    forename: str
    surname: str
    sex: Optional[str] = None
    birth_date: Optional[str] = None
    death_date: Optional[str] = None
    education: Optional[str] = None
    occupation: Optional[str] = None
    wikidata_id: Optional[str] = None
    wikipedia: Optional[str] = None
    affiliations: List[Affiliation] = field(default_factory=list)


@dataclass
class OrgMetadata:
    """Metadata for a parliamentary body, political party, or committee."""
    org_id: str
    org_type: str  # e.g., parliament, politicalParty, parliamentaryGroup, committee, government
    name_short: Optional[str] = None
    name_full: Optional[str] = None
    orientation: Optional[str] = None
    parent_org_id: Optional[str] = None
    country: str = "AL"


def load_persons_csv(path: Path | str) -> Dict[str, PersonMetadata]:
    """
    Load metadata/persons.csv into a dictionary of PersonMetadata keyed by person_id.
    Expected headers: person_id,forename,surname,sex,birth_date,education,occupation,wikidata_id,wikipedia
    """
    p = Path(path)
    persons: Dict[str, PersonMetadata] = {}
    if not p.exists():
        return persons

    with p.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = (row.get("person_id") or row.get("id") or "").strip()
            if not pid:
                continue
            forename = (row.get("forename") or "").strip()
            surname = (row.get("surname") or "").strip()
            sex = (row.get("sex") or row.get("gender") or "").strip() or None
            birth = (row.get("birth_date") or row.get("birth") or "").strip() or None
            death = (row.get("death_date") or row.get("death") or "").strip() or None
            edu = (row.get("education") or "").strip() or None
            occ = (row.get("occupation") or "").strip() or None
            wikidata = (row.get("wikidata_id") or row.get("wikidata") or "").strip() or None
            wiki = (row.get("wikipedia") or "").strip() or None

            persons[pid] = PersonMetadata(
                person_id=pid,
                forename=forename,
                surname=surname,
                sex=sex,
                birth_date=birth,
                death_date=death,
                education=edu,
                occupation=occ,
                wikidata_id=wikidata,
                wikipedia=wiki,
            )

    return persons


def load_affiliations_csv(path: Path | str, persons: Dict[str, PersonMetadata]) -> None:
    """
    Load metadata/affiliations.csv and attach Affiliation objects to PersonMetadata entries.
    Expected headers: person_id,org_id,role,from_date,to_date
    """
    p = Path(path)
    if not p.exists():
        return

    with p.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = (row.get("person_id") or "").strip()
            org_id = (row.get("org_id") or "").strip()
            if not pid or not org_id or pid not in persons:
                continue
            role = (row.get("role") or "").strip() or None
            from_d = (row.get("from_date") or "").strip() or None
            to_d = (row.get("to_date") or "").strip() or None

            persons[pid].affiliations.append(
                Affiliation(
                    org_id=org_id,
                    role=role,
                    from_date=from_d,
                    to_date=to_d,
                )
            )


def load_orgs_csv(path: Path | str) -> Dict[str, OrgMetadata]:
    """
    Load metadata/orgs.csv into a dictionary of OrgMetadata keyed by org_id.
    Expected headers: org_id,org_type,name_short,name_full,orientation,parent_org_id,country
    """
    p = Path(path)
    orgs: Dict[str, OrgMetadata] = {}
    if not p.exists():
        return orgs

    with p.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            oid = (row.get("org_id") or row.get("id") or "").strip()
            if not oid:
                continue
            otype = (row.get("org_type") or row.get("type") or "politicalParty").strip()
            short_n = (row.get("name_short") or row.get("abbrev") or "").strip() or None
            full_n = (row.get("name_full") or row.get("name") or "").strip() or None
            orient = (row.get("orientation") or "").strip() or None
            parent = (row.get("parent_org_id") or "").strip() or None
            country = (row.get("country") or "AL").strip()

            orgs[oid] = OrgMetadata(
                org_id=oid,
                org_type=otype,
                name_short=short_n,
                name_full=full_n,
                orientation=orient,
                parent_org_id=parent,
                country=country,
            )

    return orgs


def build_listPerson(persons: Iterable[PersonMetadata]) -> ET.Element:
    """Build a TEI <listPerson> element conforming to ParlaMint format."""
    root = ET.Element(q("listPerson"), {xml_attr("id"): "ParlaMint-AL-listPerson"})
    
    for pers in sorted(persons, key=lambda x: (x.surname, x.forename)):
        p_el = ET.SubElement(root, q("person"), {xml_attr("id"): pers.person_id})
        
        # persName
        persName = ET.SubElement(p_el, q("persName"), {xml_attr("lang"): "sq"})
        if pers.surname:
            ET.SubElement(persName, q("surname")).text = pers.surname
        if pers.forename:
            ET.SubElement(persName, q("forename")).text = pers.forename
            
        # sex
        if pers.sex:
            sex_val = "M" if pers.sex.upper() in ("M", "MALE", "MASHKULL") else "F" if pers.sex.upper() in ("F", "FEMALE", "FEMËR") else pers.sex
            ET.SubElement(p_el, q("sex"), {"value": sex_val})
            
        # birth / death
        if pers.birth_date:
            ET.SubElement(p_el, q("birth"), {"when": pers.birth_date})
        if pers.death_date:
            ET.SubElement(p_el, q("death"), {"when": pers.death_date})
            
        # affiliations
        for aff in pers.affiliations:
            aff_attrs = {"ref": f"#{aff.org_id}"}
            if aff.role:
                aff_attrs["role"] = aff.role
            if aff.from_date:
                aff_attrs["from"] = aff.from_date
            if aff.to_date:
                aff_attrs["to"] = aff.to_date
            ET.SubElement(p_el, q("affiliation"), aff_attrs)
            
        # identifiers
        if pers.wikidata_id:
            idno = ET.SubElement(p_el, q("idno"), {"type": "URI", "subtype": "wikidata"})
            idno.text = f"https://www.wikidata.org/wiki/{pers.wikidata_id}" if not pers.wikidata_id.startswith("http") else pers.wikidata_id

    return root


def write_listPerson(persons: Iterable[PersonMetadata], out_path: Path | str) -> None:
    """Serialize <listPerson> to an XML file."""
    root = build_listPerson(persons)
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(p, encoding="utf-8", xml_declaration=True)


def build_listOrg(orgs: Iterable[OrgMetadata]) -> ET.Element:
    """Build a TEI <listOrg> element conforming to ParlaMint format."""
    root = ET.Element(q("listOrg"), {xml_attr("id"): "ParlaMint-AL-listOrg"})
    
    for org in sorted(orgs, key=lambda x: x.org_id):
        o_el = ET.SubElement(root, q("org"), {
            xml_attr("id"): org.org_id,
            "role": org.org_type,
        })
        
        if org.name_short:
            ET.SubElement(o_el, q("orgName"), {"full": "init"}).text = org.name_short
        if org.name_full:
            ET.SubElement(o_el, q("orgName"), {"full": "yes", xml_attr("lang"): "sq"}).text = org.name_full
            
        if org.parent_org_id:
            ET.SubElement(o_el, q("listRelation")).append(
                ET.Element(q("relation"), {"name": "subpart", "active": f"#{org.org_id}", "passive": f"#{org.parent_org_id}"})
            )

    return root


def write_listOrg(orgs: Iterable[OrgMetadata], out_path: Path | str) -> None:
    """Serialize <listOrg> to an XML file."""
    root = build_listOrg(orgs)
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(p, encoding="utf-8", xml_declaration=True)
