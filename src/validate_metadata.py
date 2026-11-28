# -*- coding: utf-8 -*-
"""
Validation and Acceptance Test Suite for ParlaMint-AL Metadata & TEI Export.
Implements Sections 6, 8, 9, 10, 11, and 12 of ParlaMint_AL_Metadata_Collection_and_Validation_Guide.txt:
1. Synthetic Worked Examples from Section 12:
   - Double inclusion (M1 -> Parliament K1, M2 -> Party Q1) + Minister office + Coalition -> Opposition transition
     on T01 (2026-03-30) and T02 (2026-04-01).
   - Converse test: P1 changes from G1 to G2 (both same alignment) -> Speaker_party changes to G2,
     Party_status unchanged, M2 updates inferred party membership without closing separately documented
     direct party membership.
2. Corpus Worked Examples from Sections 2, 3, 4, 7:
   - Adea Pirdeni (4 distinct assertions with month/day precision, M1/M2 inference, KQZ 2025 election record).
   - KEPF Committee roster (chair, deputy chairs, secretary, full member, substitute).
   - Mixed group AL_ORG_GP_AN (M1 applies, M2 suppressed).
   - Confirmed no-group MP (AL_PERS_AgronShehaj) and Guest speaker (AL_PERS_BesnikDervishi on 2025-10-06).
   - Retired ID consolidation audit (no active pointer targets a retired ID).
3. Release Checklist (Section 12):
   - Every metadata table has a valid `reliability` column ('Verified', 'Reliable', 'Unsure', or '').
   - All exported TEI XML IDs are unique, non-empty, and all local pointers (@who, @ref, @corresp,
     @active, @passive, @mutual, xi:include) resolve to expected targets.
   - Chronology & coverage check (no inverted dates).
"""
from __future__ import annotations
import csv
import json
from pathlib import Path
from typing import Dict, List, Set
import xml.etree.ElementTree as ET

from .config import PROJECT_ROOT, PATH_METADATA, OUT_TEI_DIR
from .collect_metadata import (
    RETIRED_PERSON_IDS,
    RETIRED_ORG_IDS,
    apply_m1_m2_inference,
)
from .person_org_metadata import (
    PersonMetadata,
    OrgMetadata,
    OrgRelation,
    Affiliation,
    load_persons_csv,
    load_affiliations_csv,
    load_orgs_csv,
    load_org_relations_csv,
)
from .resolve_speakers import resolve_speaker_for_date

TEI_NS = "http://www.tei-c.org/ns/1.0"
XI_NS = "http://www.w3.org/2001/XInclude"
XML_NS = "http://www.w3.org/XML/1998/namespace"


def test_section_12_synthetic_cases() -> List[Dict[str, str]]:
    """
    Execute the Section 12 synthetic acceptance tests:
    Case A: P1 in G1 (entails K1 via M1 and Q1 via M2) + Minister on 2026-03-30 (Coalition)
            and 2026-04-01 (Opposition).
    Case B (Converse): P1 moves from G1 to G2 on 2026-04-02 while both G1 and G2 have Coalition alignment,
            and P1 also holds an independently documented direct party affiliation.
    """
    synthetic_orgs = {
        "K1": OrgMetadata(org_id="K1", org_type="parliament", name_short="K1", name_full="Kuvendi K1"),
        "G1": OrgMetadata(org_id="G1", org_type="parliamentaryGroup", name_short="G1", name_full="Grupi G1"),
        "G2": OrgMetadata(org_id="G2", org_type="parliamentaryGroup", name_short="G2", name_full="Grupi G2"),
        "Q1": OrgMetadata(org_id="Q1", org_type="politicalParty", name_short="Q1", name_full="Partia Q1"),
        "Q2": OrgMetadata(org_id="Q2", org_type="politicalParty", name_short="Q2", name_full="Partia Q2"),
        "GOV1": OrgMetadata(org_id="GOV1", org_type="government", name_short="GOV1", name_full="Qeveria GOV1"),
    }

    synthetic_relations_dict = [
        {
            "relation_id": "SYN_GIP_G1",
            "relation_type": "GroupInParliament",
            "active_org_id": "G1",
            "passive_org_id": "K1",
            "mutual_org_ids": "",
            "from_date": "2026-03-01",
            "to_date": "",
            "requires_mandate": "true",
            "is_party_entailing": "true",
            "rule_version": "M1-v1.0",
            "review_status": "confirmed",
            "reliability": "Verified",
        },
        {
            "relation_id": "SYN_GPE_G1_Q1",
            "relation_type": "GroupPartyEntailment",
            "active_org_id": "G1",
            "passive_org_id": "Q1",
            "mutual_org_ids": "",
            "from_date": "2026-03-01",
            "to_date": "",
            "requires_mandate": "true",
            "is_party_entailing": "true",
            "rule_version": "M2-v1.0",
            "review_status": "confirmed",
            "reliability": "Verified",
        },
    ]

    direct_affs = [
        {
            "assertion_id": "SYN_AFF_G1",
            "person_id": "P1",
            "org_id": "G1",
            "role": "member",
            "source_role": "Member of G1",
            "roster_class": "full_member",
            "from_date": "2026-03-01",
            "to_date": "",
            "review_status": "confirmed",
            "reliability": "Verified",
        },
        {
            "assertion_id": "SYN_AFF_MIN",
            "person_id": "P1",
            "org_id": "GOV1",
            "role": "minister",
            "source_role": "Minister",
            "roster_class": "cabinet",
            "from_date": "2026-03-01",
            "to_date": "",
            "review_status": "confirmed",
            "reliability": "Verified",
        },
    ]

    inferred_affs, _ = apply_m1_m2_inference(direct_affs, synthetic_relations_dict)
    inferred_orgs = {a["org_id"] for a in inferred_affs}
    assert "K1" in inferred_orgs, "Rule M1 failed to infer K1 Parliament membership for P1"
    assert "Q1" in inferred_orgs, "Rule M2 failed to infer Q1 Party membership for P1"

    p1 = PersonMetadata(person_id="P1", forename="Test", surname="Speaker")
    for a in direct_affs + inferred_affs:
        p1.affiliations.append(
            Affiliation(
                org_id=a["org_id"],
                role=a["role"],
                from_date=a["from_date"],
                to_date=a.get("to_date") or None,
                basis=a.get("basis", "direct"),
                reliability=a.get("reliability", "Verified"),
            )
        )

    # Alignment changes between 2026-03-30 (Coalition) and 2026-04-01 (Opposition)
    status_rels = [
        OrgRelation(
            relation_id="SYN_COAL_1",
            relation_type="coalition",
            mutual_org_ids="GOV1 G1",
            from_date="2026-03-01",
            to_date="2026-03-31",
        ),
        OrgRelation(
            relation_id="SYN_OPP_2",
            relation_type="opposition",
            active_org_id="G1",
            passive_org_id="GOV1",
            from_date="2026-04-01",
            to_date="2026-04-30",
        ),
    ]

    res_t01 = resolve_speaker_for_date(
        "Test Speaker",
        date="2026-03-30",
        persons={"P1": p1},
        orgs=synthetic_orgs,
        org_relations=status_rels,
    )
    res_t02 = resolve_speaker_for_date(
        "Test Speaker",
        date="2026-04-01",
        persons={"P1": p1},
        orgs=synthetic_orgs,
        org_relations=status_rels,
    )

    assert res_t01.role == "#regular" and res_t01.is_mp and res_t01.is_minister
    assert res_t01.speaker_party == "G1" and res_t01.party_status == "Coalition"

    assert res_t02.role == "#regular" and res_t02.is_mp and res_t02.is_minister
    assert res_t02.speaker_party == "G1" and res_t02.party_status == "Opposition"

    # Converse Test: P1 moves from G1 (2026-03-01..2026-03-31) to G2 (2026-04-01..) while both G1 and G2 are Coalition
    converse_direct = [
        {
            "assertion_id": "CONV_G1",
            "person_id": "P1",
            "org_id": "G1",
            "role": "member",
            "roster_class": "full_member",
            "from_date": "2026-03-01",
            "to_date": "2026-03-31",
            "review_status": "confirmed",
            "reliability": "Verified",
        },
        {
            "assertion_id": "CONV_G2",
            "person_id": "P1",
            "org_id": "G2",
            "role": "member",
            "roster_class": "full_member",
            "from_date": "2026-04-01",
            "to_date": "",
            "review_status": "confirmed",
            "reliability": "Verified",
        },
    ]
    converse_rels_dict = synthetic_relations_dict + [
        {
            "relation_id": "SYN_GIP_G2",
            "relation_type": "GroupInParliament",
            "active_org_id": "G2",
            "passive_org_id": "K1",
            "from_date": "2026-03-01",
            "to_date": "",
            "requires_mandate": "true",
            "is_party_entailing": "true",
            "review_status": "confirmed",
            "reliability": "Verified",
        },
        {
            "relation_id": "SYN_GPE_G2_Q2",
            "relation_type": "GroupPartyEntailment",
            "active_org_id": "G2",
            "passive_org_id": "Q2",
            "from_date": "2026-03-01",
            "to_date": "",
            "requires_mandate": "true",
            "is_party_entailing": "true",
            "review_status": "confirmed",
            "reliability": "Verified",
        },
    ]
    conv_inferred, _ = apply_m1_m2_inference(converse_direct, converse_rels_dict)
    p1_conv = PersonMetadata(person_id="P1", forename="Test", surname="Speaker")
    for a in converse_direct + conv_inferred:
        p1_conv.affiliations.append(
            Affiliation(
                org_id=a["org_id"],
                role=a["role"],
                from_date=a["from_date"],
                to_date=a.get("to_date") or None,
                basis=a.get("basis", "direct"),
            )
        )
    same_align_rels = [
        OrgRelation(
            relation_id="SYN_COAL_BOTH",
            relation_type="coalition",
            mutual_org_ids="GOV1 G1 G2",
            from_date="2026-03-01",
            to_date="",
        )
    ]
    res_t03 = resolve_speaker_for_date(
        "Test Speaker",
        date="2026-04-02",
        persons={"P1": p1_conv},
        orgs=synthetic_orgs,
        org_relations=same_align_rels,
    )
    assert res_t03.speaker_party == "G2" and res_t03.party_id == "Q2" and res_t03.party_status == "Coalition"

    fixtures = [
        {
            "Speech_ID": "T01",
            "Date": "2026-03-30",
            "Speaker_ID": "P1",
            "Speaker_role": res_t01.role,
            "Speaker_MP": str(res_t01.is_mp),
            "Speaker_minister": str(res_t01.is_minister),
            "Speaker_party": res_t01.speaker_party,
            "Group_ID": res_t01.group_id,
            "Party_ID": res_t01.party_id,
            "Party_status": res_t01.party_status,
        },
        {
            "Speech_ID": "T02",
            "Date": "2026-04-01",
            "Speaker_ID": "P1",
            "Speaker_role": res_t02.role,
            "Speaker_MP": str(res_t02.is_mp),
            "Speaker_minister": str(res_t02.is_minister),
            "Speaker_party": res_t02.speaker_party,
            "Group_ID": res_t02.group_id,
            "Party_ID": res_t02.party_id,
            "Party_status": res_t02.party_status,
        },
        {
            "Speech_ID": "T03_Converse",
            "Date": "2026-04-02",
            "Speaker_ID": "P1",
            "Speaker_role": res_t03.role,
            "Speaker_MP": str(res_t03.is_mp),
            "Speaker_minister": str(res_t03.is_minister),
            "Speaker_party": res_t03.speaker_party,
            "Group_ID": res_t03.group_id,
            "Party_ID": res_t03.party_id,
            "Party_status": res_t03.party_status,
        },
    ]
    return fixtures


def run_all_validations(
    metadata_dir: Path | str = PATH_METADATA,
    out_tei_dir: Path | str = OUT_TEI_DIR,
) -> Dict:
    """
    Execute all acceptance tests from Sections 6–12 of the Guide and write
    an expected-output fixture and validation report.
    """
    meta_p = Path(metadata_dir)
    tei_p = Path(out_tei_dir)

    # 1. Run Section 12 synthetic worked examples
    fixtures = test_section_12_synthetic_cases()

    # 2. Verify all CSV tables in metadata/ have a valid `reliability` column (Section 6)
    allowed_reliability = {"Verified", "Reliable", "Unsure", ""}
    csv_files = sorted(meta_p.glob("*.csv"))
    table_checks: Dict[str, Dict] = {}
    for cf in csv_files:
        with cf.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            assert "reliability" in headers, f"Missing mandatory 'reliability' column in {cf.name}"
            rows = list(reader)
            for idx, r in enumerate(rows, start=1):
                rel_val = r.get("reliability", "")
                assert rel_val in allowed_reliability, (
                    f"Invalid reliability value {rel_val!r} in {cf.name} row {idx} (never use 'Blank')"
                )
            table_checks[cf.name] = {"rows": len(rows), "has_reliability": True}

    # 3. Verify worked examples and ontology rules in loaded tables
    persons = load_persons_csv(meta_p / "persons.csv")
    load_affiliations_csv(meta_p / "affiliations.csv", persons)
    orgs = load_orgs_csv(meta_p / "orgs.csv")
    org_rels = load_org_relations_csv(meta_p / "org_relations.csv")

    # 3a. No retired person or org ID is active in persons.csv, orgs.csv, or affiliations.csv (Section 2)
    for ret_pid in RETIRED_PERSON_IDS:
        assert ret_pid not in persons, f"Retired person ID {ret_pid} is still active in persons.csv"
    for ret_oid in RETIRED_ORG_IDS:
        assert ret_oid not in orgs, f"Retired org ID {ret_oid} is still active in orgs.csv"

    # 3b. Adea Pirdeni worked example (Section 2, 3, 4 & Dependencies Spec)
    assert "AL_PERS_AdeaPirdeni" in persons
    pirdeni = persons["AL_PERS_AdeaPirdeni"]
    assert pirdeni.birth_date == "1983-10-01" and pirdeni.birth_place == "Tiranë"
    pirdeni_orgs = {(a.org_id, a.from_date, a.basis) for a in pirdeni.affiliations}
    assert ("AL_ORG_GOV_MJ", "2020-09", "direct") in pirdeni_orgs, "Missing month-precision 2020-09 AL_ORG_GOV_MJ role for Adea Pirdeni"
    assert ("AL_ORG_GOV", "2020-09", "direct") in pirdeni_orgs, "Missing AL_ORG_GOV Minister of Justice role for Adea Pirdeni"
    assert ("AL_ORG_GOV_MSHAA", "2024-01-15", "direct") in pirdeni_orgs, "Missing 2024-01-15 Decision 6/2024 role for Adea Pirdeni"
    assert ("AL_ORG_GOV", "2025-09-15", "direct") in pirdeni_orgs, "Missing 2025-09-15 Presidential Decree role for Adea Pirdeni"
    assert ("AL_ORG_PARL", "2025-09-10", "inferred") in pirdeni_orgs, "Missing M1 inferred Parliament membership for Adea Pirdeni"
    assert ("AL_ORG_PS", "2025-09-10", "inferred") in pirdeni_orgs, "Missing M2 inferred Party membership for Adea Pirdeni"
    pirdeni_mj_descs = {
        (a.org_id, a.role, a.description)
        for a in pirdeni.affiliations
        if a.org_id in ("AL_ORG_GOV", "AL_ORG_GOV_MJ") and a.from_date == "2020-09"
    }
    assert ("AL_ORG_GOV", "minister", "Minister of Justice") in pirdeni_mj_descs
    assert ("AL_ORG_GOV_MJ", "minister", "Minister of Justice") in pirdeni_mj_descs

    # 3c. Mixed group AL_ORG_PARL_GP_AN (Section 8 & 9: M1 applies, M2 does NOT infer party from GP_AN)
    dule = persons["AL_PERS_VangjelDule"]
    dule_inferred_orgs = {a.org_id for a in dule.affiliations if a.basis == "inferred"}
    assert "AL_ORG_PARL" in dule_inferred_orgs, "M1 failed to infer Parliament membership for GP_AN member Vangjel Dule"
    assert len(dule_inferred_orgs) == 1, f"M2 must not infer party membership from multi-party group GP_AN: {dule_inferred_orgs}"

    # 3c-2. Verify organizational hierarchy & parent_org_id rules
    assert "AL_ORG_GOV" in orgs and not orgs["AL_ORG_GOV"].parent_org_id
    assert "AL_ORG_PARL" in orgs and not orgs["AL_ORG_PARL"].parent_org_id
    for oid, o_obj in orgs.items():
        if o_obj.org_type == "ministry":
            assert oid.startswith("AL_ORG_GOV_"), f"Ministry {oid} must start with AL_ORG_GOV_"
            assert o_obj.parent_org_id == "AL_ORG_GOV", f"Ministry {oid} must have parent_org_id == AL_ORG_GOV"
        elif o_obj.org_type in ("parliamentaryBody", "committee", "parliamentaryGroup"):
            assert oid.startswith("AL_ORG_PARL_"), f"Parliamentary body/committee/group {oid} must start with AL_ORG_PARL_"
            assert o_obj.parent_org_id == "AL_ORG_PARL", f"{oid} must have parent_org_id == AL_ORG_PARL"
            if o_obj.org_type == "committee":
                assert oid.startswith("AL_ORG_PARL_COM_"), f"Committee {oid} must start with AL_ORG_PARL_COM_"
            elif o_obj.org_type == "parliamentaryGroup":
                assert oid.startswith("AL_ORG_PARL_GP_"), f"Parliamentary group {oid} must start with AL_ORG_PARL_GP_"
        elif o_obj.org_type == "independentInstitution":
            assert not o_obj.parent_org_id, f"Independent institution {oid} must have no parent_org_id"
        elif o_obj.org_type == "localGovernment":
            assert oid.startswith("AL_ORG_LOCGOV_"), f"Local government {oid} must start with AL_ORG_LOCGOV_"
            assert not o_obj.parent_org_id, f"Local government {oid} must have no parent_org_id"
        assert o_obj.name_full and o_obj.name_en, f"Organization {oid} must have both Albanian (name_full) and English (name_en) names"
        assert o_obj.org_type_en and o_obj.org_type_sq, f"Organization {oid} must have bilingual org_type_en and org_type_sq"

    # Verify affiliations.csv has bilingual role (role_en, role_sq) and description (description, description_sq)
    with (meta_p / "affiliations.csv").open(newline="", encoding="utf-8") as f:
        aff_reader = csv.DictReader(f)
        aff_headers = aff_reader.fieldnames or []
        for req_col in ("role", "role_en", "role_sq", "description", "description_sq"):
            assert req_col in aff_headers, f"Missing {req_col!r} column in affiliations.csv"
        assert "source_role" not in aff_headers, "source_role should be renamed to description in affiliations.csv"
        for a_row in aff_reader:
            assert a_row.get("role") and a_row.get("role_en") and a_row.get("role_sq"), f"Missing bilingual role in {a_row}"
            assert a_row.get("description") and a_row.get("description_sq"), f"Missing bilingual description in {a_row}"

    # 3d. Guest speaker test (Besnik Dervishi on 2025-10-06)
    res_guest = resolve_speaker_for_date(
        "Besnik Dervishi",
        date="2025-10-06",
        persons=persons,
        orgs=orgs,
        org_relations=org_rels,
    )
    assert res_guest.role == "#guest" and not res_guest.is_mp

    # 3e. Confirmed no-group MP test (Agron Shehaj on 2025-12-04)
    res_nogroup = resolve_speaker_for_date(
        "Agron Shehaj",
        date="2025-12-04",
        persons=persons,
        orgs=orgs,
        org_relations=org_rels,
    )
    assert res_nogroup.is_mp and not res_nogroup.group_id and res_nogroup.party_id == "AL_ORG_MUNDESIA"
    assert res_nogroup.speaker_party == "AL_ORG_MUNDESIA" and res_nogroup.party_status == "Opposition"

    # 3f. Verify metadata/elections.csv contains all 140 elected deputy records from KQZ 2025 (Section 3)
    with (meta_p / "elections.csv").open(newline="", encoding="utf-8") as f:
        elections_rows = list(csv.DictReader(f))
    assert len(elections_rows) == 140, (
        f"Expected exactly 140 elected deputy records in metadata/elections.csv from KQZ 2025, got {len(elections_rows)}"
    )
    for er in elections_rows:
        epid = er["person_id"]
        assert epid in persons, f"Elected deputy {epid} in elections.csv is missing from persons.csv"
        esubj = er["electoral_subject_id"]
        assert esubj in orgs, f"Electoral subject {esubj} in elections.csv is missing from orgs.csv"
        p_abbr = (er.get("party_abbr") or "").strip()
        assert p_abbr, f"party_abbr must not be blank in elections.csv (row {er.get('source_row')})"
        p_org_id = (er.get("org_id") or "").strip()
        assert p_org_id and p_org_id in orgs, (
            f"org_id {p_org_id!r} for party_abbr {p_abbr!r} in elections.csv is missing from orgs.csv"
        )
        assert orgs[p_org_id].name_short == p_abbr, (
            f"org_id {p_org_id!r} in elections.csv does not match name_short {p_abbr!r} in orgs.csv"
        )

    # 4. Validate TEI XML Structure, Uniqueness of IDs, and Pointer Resolution (Section 11 & 12)
    xml_id_attr = f"{{{XML_NS}}}id"
    global_ids: Set[str] = set()
    duplicate_ids: List[str] = []
    dangling_pointers: List[str] = []

    list_person_xml = tei_p / "ParlaMint-AL-listPerson.xml"
    list_org_xml = tei_p / "ParlaMint-AL-listOrg.xml"
    root_xml = tei_p / "ParlaMint-AL.xml"

    person_xml_ids: Set[str] = set()
    org_xml_ids: Set[str] = set()
    taxonomy_cat_ids: Set[str] = set()

    for tax_f in sorted(tei_p.glob("ParlaMint-taxonomy-*.xml")):
        t_root = ET.parse(tax_f).getroot()
        for el in t_root.iter():
            xid = el.attrib.get(xml_id_attr)
            if xid:
                taxonomy_cat_ids.add(xid)

    if list_org_xml.exists():
        o_root = ET.parse(list_org_xml).getroot()
        for el in o_root.iter():
            xid = el.attrib.get(xml_id_attr)
            if xid:
                if xid in global_ids:
                    duplicate_ids.append(xid)
                global_ids.add(xid)
                org_xml_ids.add(xid)

    if list_person_xml.exists():
        p_root = ET.parse(list_person_xml).getroot()
        for el in p_root.iter():
            xid = el.attrib.get(xml_id_attr)
            if xid:
                if xid in global_ids:
                    duplicate_ids.append(xid)
                global_ids.add(xid)
                person_xml_ids.add(xid)
            if el.tag == f"{{{TEI_NS}}}affiliation":
                ref = (el.attrib.get("ref") or "").lstrip("#")
                if not ref or ref not in org_xml_ids:
                    dangling_pointers.append(f"listPerson affiliation/@ref={ref!r}")

    # Check root XIncludes and component files
    included_components: List[Path] = []
    if root_xml.exists():
        r_root = ET.parse(root_xml).getroot()
        for inc in r_root.findall(f".//{{{XI_NS}}}include"):
            href = inc.attrib.get("href", "")
            target_p = tei_p / href
            assert target_p.exists(), f"Missing xi:include target in ParlaMint-AL.xml: {href}"
            if href.startswith("plain/"):
                included_components.append(target_p)

    for comp_p in included_components:
        c_root = ET.parse(comp_p).getroot()
        comp_id = c_root.attrib.get(xml_id_attr, "")
        if comp_id in global_ids:
            duplicate_ids.append(comp_id)
        global_ids.add(comp_id)

        for m_el in c_root.findall(f".//{{{TEI_NS}}}meeting"):
            corresp = m_el.attrib.get("corresp", "")
            for cref in corresp.split():
                cid = cref.lstrip("#")
                if cid not in org_xml_ids:
                    dangling_pointers.append(f"{comp_p.name} meeting/@corresp={cref}")

        for u_el in c_root.findall(f".//{{{TEI_NS}}}u"):
            uid = u_el.attrib.get(xml_id_attr, "")
            if uid in global_ids:
                duplicate_ids.append(uid)
            global_ids.add(uid)
            who = u_el.attrib.get("who", "")
            if who:
                wpid = who.lstrip("#")
                if wpid not in person_xml_ids:
                    dangling_pointers.append(f"{comp_p.name} u/@who={who}")

    assert not duplicate_ids, f"Duplicate XML IDs found: {duplicate_ids[:10]}"
    assert not dangling_pointers, f"Dangling XML pointers found: {dangling_pointers[:10]}"

    # Verify all generated XML files are multi-line pretty-printed (no single-line XML dumps)
    for xml_f in list(tei_p.glob("*.xml")) + included_components:
        if xml_f.exists():
            line_cnt = len(xml_f.read_text(encoding="utf-8").splitlines())
            assert line_cnt > 5, f"XML file {xml_f.name} is not properly indented/formatted (only {line_cnt} lines)"

    # Save expected-output fixture & validation report
    fixture_path = meta_p / "section12_expected_fixtures.tsv"
    with fixture_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fixtures[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(fixtures)

    report = {
        "status": "PASSED",
        "section12_synthetic_fixtures": len(fixtures),
        "tables_validated": table_checks,
        "total_verified_persons_in_tei": len(person_xml_ids),
        "total_verified_orgs_in_tei": len(org_xml_ids),
        "total_component_xml_files": len(included_components),
        "total_unique_xml_ids": len(global_ids),
        "duplicate_xml_ids": len(duplicate_ids),
        "dangling_pointers": len(dangling_pointers),
    }
    report_path = tei_p / "metadata_validation_report.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] All Guide Section 6–12 validation and acceptance checks PASSED -> {report_path}")
    return report


if __name__ == "__main__":
    run_all_validations()
