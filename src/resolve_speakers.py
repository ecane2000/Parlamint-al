# -*- coding: utf-8 -*-
"""
Speaker resolution, disambiguation, and ParlaMint v5 speech metadata computation layer.
Implements Sections 2, 8, 9, 10, 11, and 12 of the ParlaMint-AL Metadata Collection and Validation Guide:
- Maps raw speaker cues in parliamentary transcripts to canonical person IDs (AL_PERS_...),
  resolving retired IDs and spelling variants via SPEAKER_VARIANT_MAP and RETIRED_PERSON_IDS.
- Evaluates date-valid memberships and offices on the proceeding date (`date_active_on`).
- Computes expected ParlaMint v5 speech metadata fields for every utterance:
  * Speaker_role (#chair, #regular, #guest)
  * Speaker_MP (applicable Parliament membership in AL_ORG_Kuvendi)
  * Speaker_minister (applicable qualifying minister affiliation)
  * Speaker_party (prefers applicable parliamentary group, falls back to political party)
  * Group_ID and Party_ID (kept separate for research per Section 11)
  * Party_status (Coalition vs Opposition evaluated from date-valid relations in org_relations.csv)
"""
from __future__ import annotations
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .collect_metadata import (
    SPEAKER_VARIANT_MAP,
    RETIRED_PERSON_IDS,
    date_active_on,
)
from .person_org_metadata import PersonMetadata, OrgMetadata, OrgRelation
from .segment import SpeechBlock
from .utils import normalize_name, mint_person_id

# Titles and honorifics commonly found in Albanian transcripts
TITLES_RE = re.compile(
    r"^(?:Z\.|Znj\.|Zoti|Zonja|Kryetari|Kryetarja|Bashkëkryetari|Bashkëkryetarja|"
    r"Ministri|Ministrja|Zëvendësministri|Zëvendësministrja|Deputeti|Deputetja|"
    r"Zëvendëskryetari|Zëvendëskryetarja|Komisioneri|Komisionerja|Guvernatori|Guvernatorja|"
    r"Avokati|Avokatja|Doktor|Prof\.|Prof\.\s*Dr\.|Dr\.|Akad\.)\s+",
    flags=re.I | re.UNICODE,
)

# Build flat alias map from SPEAKER_VARIANT_MAP
SPEAKER_ALIASES: Dict[str, str] = {
    k: f"{v[1]} {v[2]}".lower() for k, v in SPEAKER_VARIANT_MAP.items()
}


@dataclass
class SpeakerResolution:
    """Outcome of resolving a raw speaker string and evaluating date-sensitive v5 metadata."""
    raw_label: str
    normalized_label: str
    person_id: Optional[str]  # None if genuinely unknown (no @who attribute emitted)
    confidence: str  # "exact", "alias", "fuzzy", "heuristic", "unresolved"
    role: str = "#regular"  # "#chair", "#regular", or "#guest"
    org_id: Optional[str] = None
    group_id: Optional[str] = None
    party_id: Optional[str] = None
    speaker_party: Optional[str] = None  # v5 prefers group_id, falls back to party_id
    party_status: Optional[str] = None   # "Coalition", "Opposition", or ""
    is_mp: bool = False
    is_minister: bool = False
    speaker_name: Optional[str] = None
    speaker_gender: Optional[str] = None
    speaker_birth: Optional[str] = None
    reliability: str = "Verified"
    provenance_basis: str = "direct"
    notes: Optional[str] = None


def strip_titles(label: str) -> str:
    """Remove Albanian parliamentary honorifics and titles from speaker strings."""
    if not label:
        return ""
    cleaned = label.strip()
    while True:
        m = TITLES_RE.match(cleaned)
        if not m:
            break
        cleaned = cleaned[m.end() :].strip()
    return cleaned


def normalize_person_name(label: str) -> str:
    """Strip titles, apply alias corrections, and normalize whitespace."""
    cleaned = strip_titles(label)
    norm = normalize_name(cleaned)
    return SPEAKER_ALIASES.get(norm, norm)


def _build_name_index(persons: Dict[str, PersonMetadata]) -> tuple[Dict[str, str], Dict[str, List[str]]]:
    """
    Build fast lookup maps:
    1. full_name (normalized) -> canonical person_id
    2. surname (normalized) -> list of canonical person_ids
    """
    full_map: Dict[str, str] = {}
    surname_map: Dict[str, List[str]] = {}

    for pid, p in persons.items():
        f_norm = normalize_name(f"{p.forename} {p.surname}")
        if f_norm:
            full_map[f_norm] = pid

        r_norm = normalize_name(f"{p.surname} {p.forename}")
        if r_norm:
            full_map[r_norm] = pid

        p_base = normalize_name(pid.replace("AL_PERS_", "").replace("pAL_", ""))
        full_map[p_base] = pid

        s_norm = normalize_name(p.surname)
        if s_norm:
            surname_map.setdefault(s_norm, []).append(pid)

    # Also index all known spelling variants in SPEAKER_VARIANT_MAP
    for var_norm, (can_pid, _, _, _) in SPEAKER_VARIANT_MAP.items():
        if can_pid in persons:
            full_map[var_norm] = can_pid

    return full_map, surname_map


def match_speaker_label(label: str, persons: Dict[str, PersonMetadata]) -> SpeakerResolution:
    """Match a raw speaker label against the known persons registry."""
    if not label or label.upper() in ("UNKNOWN", "NONE", "E PANJOHUR", "I PANJOHUR"):
        return SpeakerResolution(
            raw_label=label or "",
            normalized_label="",
            person_id=None,
            confidence="unresolved",
            role="#regular",
            reliability="Unsure",
            notes="Unknown speaker without identification (no @who emitted)",
        )

    raw_norm = normalize_name(strip_titles(label))
    norm = normalize_person_name(label)
    full_map, surname_map = _build_name_index(persons)

    # 1. Exact or alias match on normalized full name
    if norm in full_map:
        pid = full_map[norm]
        if pid in RETIRED_PERSON_IDS:
            pid = RETIRED_PERSON_IDS[pid][0]
        pers = persons.get(pid)
        conf = "alias" if raw_norm != norm else "exact"
        return SpeakerResolution(
            raw_label=label,
            normalized_label=norm,
            person_id=pid,
            confidence=conf,
            role="#regular",
            speaker_name=f"{pers.forename} {pers.surname}" if pers else label,
            speaker_gender=pers.sex if pers else None,
            speaker_birth=pers.birth_date if pers else None,
            reliability=pers.reliability if pers else "Verified",
        )

    # 2. Match on surname if unique
    if norm in surname_map:
        candidates = surname_map[norm]
        if len(candidates) == 1:
            pid = candidates[0]
            pers = persons.get(pid)
            return SpeakerResolution(
                raw_label=label,
                normalized_label=norm,
                person_id=pid,
                confidence="alias",
                role="#regular",
                speaker_name=f"{pers.forename} {pers.surname}" if pers else label,
                speaker_gender=pers.sex if pers else None,
                speaker_birth=pers.birth_date if pers else None,
                reliability="Reliable",
                notes=f"Single candidate matching surname '{norm}'",
            )

    # 3. Mint a canonical person_id if name appears to be a valid person
    minted_id = mint_person_id(strip_titles(label))
    if minted_id in RETIRED_PERSON_IDS:
        minted_id = RETIRED_PERSON_IDS[minted_id][0]
    return SpeakerResolution(
        raw_label=label,
        normalized_label=norm,
        person_id=minted_id,
        confidence="heuristic",
        role="#regular",
        speaker_name=strip_titles(label),
        reliability="Unsure",
        notes="Heuristically minted ID (not in persons.csv)",
    )


def evaluate_party_status_on_date(
    group_id: Optional[str],
    party_id: Optional[str],
    date: str,
    org_relations: Optional[List[OrgRelation]] = None,
) -> str:
    """
    Evaluate Party_status ('Coalition', 'Opposition', or '') on `date`
    against date-valid coalition and opposition relations (Sections 10, 11, 12).
    """
    if not org_relations:
        return ""
    target_ids = [oid for oid in (group_id, party_id) if oid]
    if not target_ids:
        return ""

    in_coalition = False
    in_opposition = False

    for rel in org_relations:
        if not date_active_on(date, rel.from_date or "", rel.to_date or ""):
            continue
        if rel.relation_type == "coalition" and rel.mutual_org_ids:
            mutuals = set(rel.mutual_org_ids.split())
            if any(tid in mutuals for tid in target_ids):
                in_coalition = True
        elif rel.relation_type == "opposition" and rel.active_org_id:
            actives = set(rel.active_org_id.split())
            if any(tid in actives for tid in target_ids):
                in_opposition = True

    # Section 11: "Resolve conflicting statuses or flag the record for review; do not publish a guess"
    if in_coalition and in_opposition:
        return "Conflict"
    if in_coalition:
        return "Coalition"
    if in_opposition:
        return "Opposition"
    return ""


def resolve_speaker_for_date(
    label: str,
    date: str,
    persons: Dict[str, PersonMetadata],
    sitting_chair_name: Optional[str] = None,
    orgs: Optional[Dict[str, OrgMetadata]] = None,
    org_relations: Optional[List[OrgRelation]] = None,
) -> SpeakerResolution:
    """
    Resolve a speaker label on `date` and determine:
    - Utterance role (#chair, #regular, #guest)
    - Applicable Parliament membership (is_mp) and ministerial office (is_minister)
    - Applicable ParliamentaryGroup (group_id) and PoliticalParty (party_id)
    - v5 Speaker_party (prefers group_id, falls back to party_id)
    - Date-valid Party_status (Coalition vs Opposition)
    """
    res = match_speaker_label(label, persons)
    if not res.person_id:
        return res

    is_session_chair = False
    if sitting_chair_name:
        norm_chair = normalize_person_name(sitting_chair_name)
        if norm_chair and (
            res.normalized_label == norm_chair
            or norm_chair in res.normalized_label
            or res.normalized_label in norm_chair
            or (res.person_id and norm_chair.replace(" ", "") in res.person_id.lower())
        ):
            res.role = "#chair"
            is_session_chair = True

    if res.person_id not in persons:
        return res

    pers = persons[res.person_id]
    active_bases = set()
    has_guest_aff = False

    for aff in pers.affiliations:
        if not date_active_on(date, aff.from_date or "", aff.to_date or ""):
            continue
        active_bases.add(aff.basis or "direct")
        oid = aff.org_id
        org_obj = (orgs or {}).get(oid)
        otype = org_obj.org_type if org_obj else ""

        if oid == "AL_ORG_PARL" or otype == "parliament":
            if aff.role in ("member", "head", "deputyHead"):
                res.is_mp = True

        if aff.role == "minister" or otype in ("government", "ministry"):
            if aff.role == "minister":
                res.is_minister = True

        if otype == "parliamentaryGroup" or oid.startswith("AL_ORG_PARL_GP_"):
            if aff.role in ("member", "head", "deputyHead") and not res.group_id:
                res.group_id = oid

        if otype == "politicalParty" or oid in (
            "AL_ORG_PS", "AL_ORG_PD", "AL_ORG_PL", "AL_ORG_PR", "AL_ORG_PBDNJ",
            "AL_ORG_PDIU", "AL_ORG_PAA", "AL_ORG_PSD", "AL_ORG_MUNDESIA", "AL_ORG_BASHKE",
            "AL_ORG_FRD", "AL_ORG_PBKD", "AL_ORG_PLL", "AL_ORG_SHB",
        ):
            if aff.role in ("member", "head", "deputyHead") and not res.party_id:
                res.party_id = oid

        if aff.role in ("guest", "mayor") or otype in ("independentInstitution", "localGovernment"):
            has_guest_aff = True

        if not res.org_id:
            res.org_id = oid

    if not is_session_chair:
        if not res.is_mp and (has_guest_aff or res.is_minister):
            res.role = "#guest"
        else:
            res.role = "#regular"

    # ParlaMint v5 rule (Section 11): "The v5 export prefers an applicable parliamentary group and falls back to a party."
    res.speaker_party = res.group_id or res.party_id or ""
    if res.speaker_party:
        res.org_id = res.speaker_party

    res.party_status = evaluate_party_status_on_date(
        group_id=res.group_id,
        party_id=res.party_id,
        date=date,
        org_relations=org_relations,
    )

    if "inferred" in active_bases and "direct" in active_bases:
        res.provenance_basis = "direct+inferred"
    elif "inferred" in active_bases:
        res.provenance_basis = "inferred"
    else:
        res.provenance_basis = "direct"

    return res


def resolve_speeches(
    speeches: List[SpeechBlock],
    date: str,
    persons: Dict[str, PersonMetadata],
    sitting_chair_name: Optional[str] = None,
    orgs: Optional[Dict[str, OrgMetadata]] = None,
    org_relations: Optional[List[OrgRelation]] = None,
) -> Dict[str, SpeakerResolution]:
    """
    Resolve all speech turns in a sitting to speaker resolutions.
    Returns mapping: speech_id -> SpeakerResolution
    """
    resolutions: Dict[str, SpeakerResolution] = {}
    for sp in speeches:
        if sp.raw_speaker_label:
            res = resolve_speaker_for_date(
                sp.raw_speaker_label,
                date=date,
                persons=persons,
                sitting_chair_name=sitting_chair_name,
                orgs=orgs,
                org_relations=org_relations,
            )
        else:
            res = SpeakerResolution(
                raw_label="",
                normalized_label="",
                person_id=None,
                confidence="unresolved",
                role="#regular",
                reliability="Unsure",
                notes="Narrative or chair transition without explicit speaker cue",
            )
        resolutions[sp.speech_id] = res

    return resolutions


def write_unresolved_report(resolutions: Dict[str, SpeakerResolution], out_path: Path | str) -> None:
    """Save an audit report of unresolved or heuristic speaker matches."""
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)

    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["speech_id", "raw_label", "normalized_label", "person_id", "role", "confidence", "reliability", "notes"],
        )
        writer.writeheader()
        for speech_id, res in resolutions.items():
            if res.confidence in ("unresolved", "heuristic") or not res.person_id:
                writer.writerow({
                    "speech_id": speech_id,
                    "raw_label": res.raw_label,
                    "normalized_label": res.normalized_label,
                    "person_id": res.person_id or "",
                    "role": res.role,
                    "confidence": res.confidence,
                    "reliability": res.reliability,
                    "notes": res.notes or "",
                })


def write_speech_metadata_tsv(
    speech_rows: List[Dict[str, str]],
    out_path: Path | str,
) -> None:
    """
    Export the ParlaMint v5 speech-level metadata research & validation table (Section 11 & 12):
    Includes Speaker_role, Speaker_MP, Speaker_minister, Speaker_party, Group_ID, Party_ID,
    Party_status, Reliability, and Provenance_basis.
    """
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "Speech_ID",
        "Doc_ID",
        "Date",
        "Speaker_ID",
        "Speaker_name",
        "Speaker_role",
        "Speaker_MP",
        "Speaker_minister",
        "Speaker_party",
        "Group_ID",
        "Party_ID",
        "Party_status",
        "Speaker_gender",
        "Speaker_birth",
        "Provenance_basis",
        "Reliability",
    ]
    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for r in speech_rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})
