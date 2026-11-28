# -*- coding: utf-8 -*-
"""
Person and Organisation metadata layer for ParlaMint-AL:
Loads speaker/MP data, party/group affiliations, organisations, and organisation relations
from CSV files (with reliability and review_status filtering per Section 6 & 11 of the Guide)
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


def _indent_xml(element: ET.Element, level: int = 0) -> None:
    """Recursively pretty-print an ElementTree XML node with 2-space indentation."""
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


def q(tag: str) -> str:
    return f"{{{TEI_NS}}}{tag}"


def xml_attr(local: str) -> str:
    return f"{{{XML_NS}}}{local}"


@dataclass
class Affiliation:
    """Represents a temporal affiliation or office assertion linking a person to an organization."""
    org_id: str
    role: Optional[str] = None  # Canonical: head, deputyHead, member, minister, mayor, guest
    role_en: Optional[str] = None
    role_sq: Optional[str] = None
    description: Optional[str] = None
    description_sq: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    role_name_sq: Optional[str] = None
    role_name_en: Optional[str] = None
    assertion_id: Optional[str] = None
    roster_class: Optional[str] = None
    from_precision: Optional[str] = None
    to_precision: Optional[str] = None
    observation_date: Optional[str] = None
    basis: str = "direct"  # "direct" or "inferred"
    rule_version: Optional[str] = None
    input_assertion_ids: Optional[str] = None
    source_id: Optional[str] = None
    source_locator: Optional[str] = None
    review_status: str = "confirmed"
    value_state: str = "stated"
    reliability: str = "Verified"


@dataclass
class PersonMetadata:
    """Metadata for a verified speaker / Member of Parliament."""
    person_id: str
    forename: str
    surname: str
    patronymic_raw: Optional[str] = None  # Restricted matching field; never exported to TEI (Section 2)
    sex: Optional[str] = None
    birth_date: Optional[str] = None
    birth_place: Optional[str] = None
    death_date: Optional[str] = None
    education: Optional[str] = None
    occupation: Optional[str] = None
    wikidata_id: Optional[str] = None
    wikipedia: Optional[str] = None
    source_id: Optional[str] = None
    source_locator: Optional[str] = None
    review_status: str = "confirmed"
    value_state: str = "stated"
    reliability: str = "Verified"
    affiliations: List[Affiliation] = field(default_factory=list)


@dataclass
class OrgMetadata:
    """Metadata for a parliamentary body, political party, parliamentary group, committee, or government body."""
    org_id: str
    org_type: str
    org_type_en: Optional[str] = None
    org_type_sq: Optional[str] = None
    name_short: Optional[str] = None
    name_full: Optional[str] = None
    name_en: Optional[str] = None
    orientation: Optional[str] = None
    parent_org_id: Optional[str] = None
    remit: Optional[str] = None
    remit_sq: Optional[str] = None
    country: str = "AL"
    source_id: Optional[str] = None
    source_locator: Optional[str] = None
    review_status: str = "confirmed"
    reliability: str = "Verified"


@dataclass
class OrgRelation:
    """Typed, dated relation between organizations (Section 8, 9, 10)."""
    relation_id: str
    relation_type: str
    active_org_id: Optional[str] = None
    passive_org_id: Optional[str] = None
    mutual_org_ids: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    requires_mandate: bool = False
    is_party_entailing: bool = False
    rule_version: Optional[str] = None
    source_id: Optional[str] = None
    source_locator: Optional[str] = None
    review_status: str = "confirmed"
    reliability: str = "Verified"


def normalize_affiliation_role(raw_role: Optional[str]) -> Optional[str]:
    """Normalize raw role strings to ParlaMint canonical affiliation roles."""
    if not raw_role:
        return None
    r = raw_role.strip().lower()
    if r in ("mayor", "kryetar bashkie", "kryetare bashkie"):
        return "mayor"
    if r in ("head", "chair", "chairperson", "groupleader", "leader", "kryetar", "kryetare", "bashkëkryetar", "bashkëkryetare", "president"):
        return "head"
    if r in ("deputyhead", "deputychair", "deputychairperson", "deputyleader", "vicechair", "nënkryetar", "nënkryetare", "zëvendëskryetar", "zëvendëskryetare", "deputy"):
        return "deputyHead"
    if r in ("member", "mp", "anëtar", "anëtare", "deputet", "deputete", "regular", "sekretar", "sekretare"):
        return "member"
    if r in ("minister", "ministër", "ministre", "zëvendësministër", "zëvendësministre"):
        return "minister"
    if r in ("guest", "i ftuar", "e ftuar"):
        return "guest"
    return raw_role.strip()


def infer_role_names(role: Optional[str], org_id: str, sex: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
    """Generate default Albanian and English roleName when not explicitly supplied in CSV."""
    if not role or role == "member":
        return None, None

    is_female = bool(sex and sex.upper() in ("F", "FEMALE", "FEMËR"))
    org_lower = org_id.lower()

    if role == "mayor":
        sq = "Kryetare e Bashkisë" if is_female else "Kryetar i Bashkisë"
        en = "Mayor"
        return sq, en

    if role == "head":
        if org_id == "AL_ORG_PARL" or "kuvend" in org_lower or "parliament" in org_lower:
            sq = "Kryetare e Kuvendit" if is_female else "Kryetar i Kuvendit"
            en = "Speaker of the Parliament"
        elif "gp_" in org_lower or "group" in org_lower or "grupi" in org_lower:
            sq = "Kryetare e Grupit Parlamentar" if is_female else "Kryetar i Grupit Parlamentar"
            en = "Chair of Parliamentary Group"
        elif "_com_" in org_lower or any(k in org_lower for k in ("clap", "kepf", "kcbm", "kess", "ksms", "kbnizhq", "kbuzhr", "kepj", "knqbmi", "kdnjmip", "kktd", "kprat", "kkie", "committee")):
            sq = "Kryetare e Komisionit" if is_female else "Kryetar i Komisionit"
            en = "Chair of Parliamentary Committee"
        else:
            sq = "Kryetare" if is_female else "Kryetar"
            en = "Chairperson"
        return sq, en

    if role == "deputyHead":
        if org_id == "AL_ORG_PARL" or "kuvend" in org_lower or "parliament" in org_lower:
            sq = "Nënkryetare e Kuvendit" if is_female else "Nënkryetar i Kuvendit"
            en = "Deputy Speaker of the Parliament"
        elif "gp_" in org_lower or "group" in org_lower or "grupi" in org_lower:
            sq = "Nënkryetare e Grupit Parlamentar" if is_female else "Nënkryetar i Grupit Parlamentar"
            en = "Deputy Chair of Parliamentary Group"
        elif "_com_" in org_lower or any(k in org_lower for k in ("clap", "kepf", "kcbm", "kess", "ksms", "kbnizhq", "kbuzhr", "kepj", "knqbmi", "kdnjmip", "kktd", "kprat", "kkie", "committee")):
            sq = "Nënkryetare e Komisionit" if is_female else "Nënkryetar i Komisionit"
            en = "Vice Chair of Parliamentary Committee"
        else:
            sq = "Nënkryetare" if is_female else "Nënkryetar"
            en = "Deputy Chairperson"
        return sq, en

    if role == "minister":
        sq = "Ministre" if is_female else "Ministër"
        en = "Minister"
        return sq, en

    return None, None


def is_export_eligible(review_status: Optional[str], reliability: Optional[str]) -> bool:
    """
    Section 6 Publication Rule:
    'Export a claim only when it is confirmed or corrected and rated Verified or Reliable.'
    """
    rs = (review_status or "confirmed").strip().lower()
    rel = (reliability or "Verified").strip()
    return rs in ("confirmed", "corrected") and rel in ("Verified", "Reliable")


def load_persons_csv(path: Path | str) -> Dict[str, PersonMetadata]:
    """
    Load metadata/persons.csv into a dictionary of PersonMetadata keyed by person_id.
    Only export-eligible records (confirmed/corrected and Verified/Reliable) are loaded.
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
            review_status = (row.get("review_status") or "confirmed").strip()
            reliability = (row.get("reliability") or "Verified").strip()
            if not is_export_eligible(review_status, reliability):
                continue

            forename = (row.get("forename") or "").strip()
            surname = (row.get("surname") or "").strip()
            patronymic = (row.get("patronymic_raw") or "").strip() or None
            sex = (row.get("sex") or row.get("gender") or "").strip() or None
            birth = (row.get("birth_date") or row.get("birth") or "").strip() or None
            birth_place = (row.get("birth_place") or "").strip() or None
            death = (row.get("death_date") or row.get("death") or "").strip() or None
            edu = (row.get("education") or "").strip() or None
            occ = (row.get("occupation") or "").strip() or None
            wikidata = (row.get("wikidata_id") or row.get("wikidata") or "").strip() or None
            wiki = (row.get("wikipedia") or "").strip() or None

            persons[pid] = PersonMetadata(
                person_id=pid,
                forename=forename,
                surname=surname,
                patronymic_raw=patronymic,
                sex=sex,
                birth_date=birth,
                birth_place=birth_place,
                death_date=death,
                education=edu,
                occupation=occ,
                wikidata_id=wikidata,
                wikipedia=wiki,
                source_id=(row.get("source_id") or "").strip() or None,
                source_locator=(row.get("source_locator") or "").strip() or None,
                review_status=review_status,
                value_state=(row.get("value_state") or "stated").strip(),
                reliability=reliability,
            )

    return persons


def load_affiliations_csv(path: Path | str, persons: Dict[str, PersonMetadata]) -> None:
    """
    Load metadata/affiliations.csv and attach export-eligible Affiliation objects to PersonMetadata entries.
    """
    p = Path(path)
    if not p.exists():
        return

    with p.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = (row.get("person_id") or row.get("id") or "").strip()
            org_id = (row.get("org_id") or "").strip()
            if not pid or not org_id:
                continue

            review_status = (row.get("review_status") or "confirmed").strip()
            reliability = (row.get("reliability") or "Verified").strip()
            if not is_export_eligible(review_status, reliability):
                continue

            pers = persons.get(pid)
            if not pers:
                continue

            raw_role = (row.get("role") or "").strip() or None
            role = normalize_affiliation_role(raw_role)
            from_d = (row.get("from_date") or row.get("from") or "").strip() or None
            to_d = (row.get("to_date") or row.get("to") or "").strip() or None

            desc_en = (row.get("description") or row.get("role_name_en") or "").strip() or None
            desc_sq = (row.get("description_sq") or row.get("role_name_sq") or row.get("source_role") or "").strip() or None

            role_name_sq = (row.get("role_name_sq") or desc_sq or row.get("role_sq") or "").strip() or None
            role_name_en = (row.get("role_name_en") or desc_en or row.get("role_en") or "").strip() or None

            if not role_name_sq and not role_name_en:
                inferred_sq, inferred_en = infer_role_names(role, org_id, pers.sex)
                role_name_sq = role_name_sq or inferred_sq
                role_name_en = role_name_en or inferred_en

            pers.affiliations.append(
                Affiliation(
                    org_id=org_id,
                    role=role,
                    role_en=(row.get("role_en") or "").strip() or None,
                    role_sq=(row.get("role_sq") or "").strip() or None,
                    description=desc_en,
                    description_sq=desc_sq,
                    from_date=from_d,
                    to_date=to_d,
                    role_name_sq=role_name_sq,
                    role_name_en=role_name_en,
                    assertion_id=(row.get("assertion_id") or "").strip() or None,
                    roster_class=(row.get("roster_class") or "").strip() or None,
                    from_precision=(row.get("from_precision") or "").strip() or None,
                    to_precision=(row.get("to_precision") or "").strip() or None,
                    observation_date=(row.get("observation_date") or "").strip() or None,
                    basis=(row.get("basis") or "direct").strip(),
                    rule_version=(row.get("rule_version") or "").strip() or None,
                    input_assertion_ids=(row.get("input_assertion_ids") or "").strip() or None,
                    source_id=(row.get("source_id") or "").strip() or None,
                    source_locator=(row.get("source_locator") or "").strip() or None,
                    review_status=review_status,
                    value_state=(row.get("value_state") or "stated").strip(),
                    reliability=reliability,
                )
            )


def load_orgs_csv(path: Path | str) -> Dict[str, OrgMetadata]:
    """Load metadata/orgs.csv into a dictionary of OrgMetadata keyed by org_id."""
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
            review_status = (row.get("review_status") or "confirmed").strip()
            reliability = (row.get("reliability") or "Verified").strip()
            if not is_export_eligible(review_status, reliability):
                continue

            otype = (row.get("org_type") or row.get("type") or "politicalParty").strip()
            short_n = (row.get("name_short") or row.get("abbrev") or "").strip() or None
            full_n = (row.get("name_full") or row.get("name") or "").strip() or None
            en_n = (row.get("name_en") or "").strip() or None
            orient = (row.get("orientation") or "").strip() or None
            parent = (row.get("parent_org_id") or "").strip() or None
            remit = (row.get("remit") or "").strip() or None
            country = (row.get("country") or "AL").strip()

            orgs[oid] = OrgMetadata(
                org_id=oid,
                org_type=otype,
                org_type_en=(row.get("org_type_en") or "").strip() or None,
                org_type_sq=(row.get("org_type_sq") or "").strip() or None,
                name_short=short_n,
                name_full=full_n,
                name_en=en_n,
                orientation=orient,
                parent_org_id=parent,
                remit=remit,
                remit_sq=(row.get("remit_sq") or "").strip() or None,
                country=country,
                source_id=(row.get("source_id") or "").strip() or None,
                source_locator=(row.get("source_locator") or "").strip() or None,
                review_status=review_status,
                reliability=reliability,
            )

    return orgs


def load_org_relations_csv(path: Path | str) -> List[OrgRelation]:
    """Load metadata/org_relations.csv into a list of export-eligible OrgRelation records."""
    p = Path(path)
    rels: List[OrgRelation] = []
    if not p.exists():
        return rels

    with p.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rid = (row.get("relation_id") or "").strip()
            rtype = (row.get("relation_type") or "").strip()
            if not rid or not rtype:
                continue
            review_status = (row.get("review_status") or "confirmed").strip()
            reliability = (row.get("reliability") or "Verified").strip()
            if not is_export_eligible(review_status, reliability):
                continue

            rels.append(
                OrgRelation(
                    relation_id=rid,
                    relation_type=rtype,
                    active_org_id=(row.get("active_org_id") or "").strip() or None,
                    passive_org_id=(row.get("passive_org_id") or "").strip() or None,
                    mutual_org_ids=(row.get("mutual_org_ids") or "").strip() or None,
                    from_date=(row.get("from_date") or "").strip() or None,
                    to_date=(row.get("to_date") or "").strip() or None,
                    requires_mandate=(row.get("requires_mandate") or "").strip().lower() == "true",
                    is_party_entailing=(row.get("is_party_entailing") or "").strip().lower() == "true",
                    rule_version=(row.get("rule_version") or "").strip() or None,
                    source_id=(row.get("source_id") or "").strip() or None,
                    source_locator=(row.get("source_locator") or "").strip() or None,
                    review_status=review_status,
                    reliability=reliability,
                )
            )
    return rels


def build_listPerson(persons: Iterable[PersonMetadata]) -> ET.Element:
    """
    Build a TEI <listPerson> element conforming to ParlaMint 5.0 (Section 11):
    - Maps forename and surname to <persName> (never exports patronymic_raw).
    - Exports only explicitly supported sex and birth_date/birth_place values.
    - Exports both direct and approved M1/M2 inferred affiliations.
    - Never emits empty IDs or empty date attributes.
    """
    root = ET.Element(q("listPerson"), {xml_attr("id"): "ParlaMint-AL-listPerson", xml_attr("lang"): "sq"})

    for pers in sorted(persons, key=lambda x: (x.surname, x.forename, x.person_id)):
        if not pers.person_id:
            continue
        p_el = ET.SubElement(root, q("person"), {xml_attr("id"): pers.person_id})

        persName = ET.SubElement(p_el, q("persName"), {xml_attr("lang"): "sq"})
        if pers.forename:
            ET.SubElement(persName, q("forename")).text = pers.forename
        if pers.surname:
            ET.SubElement(persName, q("surname")).text = pers.surname

        if pers.sex:
            sex_val = "M" if pers.sex.upper() in ("M", "MALE", "MASHKULL") else "F" if pers.sex.upper() in ("F", "FEMALE", "FEMËR") else pers.sex
            ET.SubElement(p_el, q("sex"), {"value": sex_val})

        if pers.birth_date:
            b_el = ET.SubElement(p_el, q("birth"), {"when": pers.birth_date})
            if pers.birth_place:
                pn = ET.SubElement(b_el, q("placeName"))
                pn.text = pers.birth_place
        if pers.death_date:
            ET.SubElement(p_el, q("death"), {"when": pers.death_date})

        for aff in pers.affiliations:
            if not aff.org_id:
                continue
            org_ref = aff.org_id if aff.org_id.startswith("#") else f"#{aff.org_id}"
            aff_attrs = {"ref": org_ref}
            if aff.role:
                aff_attrs["role"] = aff.role
            if aff.from_date:
                aff_attrs["from"] = aff.from_date
            if aff.to_date:
                aff_attrs["to"] = aff.to_date
            aff_el = ET.SubElement(p_el, q("affiliation"), aff_attrs)
            if aff.role_name_sq:
                ET.SubElement(aff_el, q("roleName"), {xml_attr("lang"): "sq"}).text = aff.role_name_sq
            if aff.role_name_en:
                ET.SubElement(aff_el, q("roleName"), {xml_attr("lang"): "en"}).text = aff.role_name_en

        if pers.wikidata_id:
            idno = ET.SubElement(p_el, q("idno"), {"type": "URI", "subtype": "wikidata"})
            idno.text = f"https://www.wikidata.org/wiki/{pers.wikidata_id}" if not pers.wikidata_id.startswith("http") else pers.wikidata_id

    return root


def write_listPerson(persons: Iterable[PersonMetadata], out_path: Path | str) -> None:
    """Serialize <listPerson> to a pretty-printed XML file."""
    root = build_listPerson(persons)
    _indent_xml(root)
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(p, encoding="utf-8", xml_declaration=True)


def build_listOrg(
    orgs: Iterable[OrgMetadata],
    org_relations: Optional[Iterable[OrgRelation]] = None,
) -> ET.Element:
    """
    Build a TEI <listOrg> element conforming to ParlaMint 5.0 (Section 10 & 11):
    Includes all reviewed organization records plus a corpus-level <listRelation>
    encoding coalition (@mutual), opposition (@active/@passive), and representing relations.
    """
    root = ET.Element(q("listOrg"), {xml_attr("id"): "ParlaMint-AL-listOrg", xml_attr("lang"): "sq"})
    org_list = sorted(orgs, key=lambda x: x.org_id)
    valid_org_ids = {o.org_id for o in org_list}

    for org in org_list:
        if not org.org_id:
            continue
        o_attrs = {
            xml_attr("id"): org.org_id,
            "role": org.org_type,
        }
        if org.orientation:
            o_attrs["ana"] = f"#orientation.{org.orientation}"
        o_el = ET.SubElement(root, q("org"), o_attrs)

        if org.name_full:
            ET.SubElement(o_el, q("orgName"), {"full": "yes", xml_attr("lang"): "sq"}).text = org.name_full
        if org.name_en:
            ET.SubElement(o_el, q("orgName"), {"full": "yes", xml_attr("lang"): "en"}).text = org.name_en
        if org.name_short:
            ET.SubElement(o_el, q("orgName"), {"full": "abb"}).text = org.name_short

        if org.org_id == "AL_ORG_PARL":
            ev = ET.SubElement(o_el, q("event"), {"from": "2025-09-10", xml_attr("id"): "KUV.XI"})
            ET.SubElement(ev, q("label"), {xml_attr("lang"): "sq"}).text = "Legjislatura XI e Kuvendit të Shqipërisë"
            ET.SubElement(ev, q("label"), {xml_attr("lang"): "en"}).text = "Legislature XI of the Parliament of Albania"

        if org.parent_org_id and org.parent_org_id in valid_org_ids:
            lr = ET.SubElement(o_el, q("listRelation"))
            ET.SubElement(lr, q("relation"), {
                "name": "subpart",
                "active": f"#{org.org_id}",
                "passive": f"#{org.parent_org_id}",
            })

    # Encode corpus-level organization relations (coalition, opposition, representing) per Section 10
    if org_relations:
        tei_rels = [r for r in org_relations if r.relation_type in ("coalition", "opposition", "representing")]
        if tei_rels:
            lr_root = ET.SubElement(root, q("listRelation"))
            for rel in tei_rels:
                r_attrs: Dict[str, str] = {"name": rel.relation_type}
                if rel.relation_type == "coalition" and rel.mutual_org_ids:
                    refs = [f"#{oid}" if not oid.startswith("#") else oid for oid in rel.mutual_org_ids.split() if oid in valid_org_ids]
                    if len(refs) >= 2:
                        r_attrs["mutual"] = " ".join(refs)
                else:
                    if rel.active_org_id:
                        act_refs = [f"#{oid}" if not oid.startswith("#") else oid for oid in rel.active_org_id.split() if oid in valid_org_ids]
                        if act_refs:
                            r_attrs["active"] = " ".join(act_refs)
                    if rel.passive_org_id and rel.passive_org_id in valid_org_ids:
                        r_attrs["passive"] = f"#{rel.passive_org_id}" if not rel.passive_org_id.startswith("#") else rel.passive_org_id

                if rel.from_date:
                    r_attrs["from"] = rel.from_date
                if rel.to_date:
                    r_attrs["to"] = rel.to_date

                if "mutual" in r_attrs or ("active" in r_attrs and "passive" in r_attrs):
                    ET.SubElement(lr_root, q("relation"), r_attrs)

    return root


def write_listOrg(
    orgs: Iterable[OrgMetadata],
    out_path: Path | str,
    org_relations: Optional[Iterable[OrgRelation]] = None,
) -> None:
    """Serialize <listOrg> to a pretty-printed XML file."""
    root = build_listOrg(orgs, org_relations=org_relations)
    _indent_xml(root)
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(p, encoding="utf-8", xml_declaration=True)
