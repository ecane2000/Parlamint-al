# -*- coding: utf-8 -*-
"""
Speaker resolution and disambiguation layer for ParlaMint-AL conforming to ParlaMint 5.0:
Maps raw speaker cues in parliamentary transcripts to stable person IDs (AL_PERS_...)
and determines date-sensitive roles (#chair, #regular, #guest) and organisation affiliations.
"""
from __future__ import annotations
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from .person_org_metadata import PersonMetadata
from .segment import SpeechBlock
from .utils import normalize_name, mint_person_id

# Titles and honorifics commonly found in Albanian transcripts
TITLES_RE = re.compile(
    r"^(?:Z\.|Znj\.|Zoti|Zonja|Kryetari|Kryetarja|Ministri|Ministrja|Deputeti|Deputetja|Zëvendëskryetari|Zëvendëskryetarja|Doktor|Prof\.|Prof\. Dr\.)\s+",
    flags=re.I | re.UNICODE,
)

# Common aliases and OCR typographical corrections
SPEAKER_ALIASES: Dict[str, str] = {
    "gent strazimri": "gent strazimiri",
    "ulsi mnja": "ulsi manja",
    "bardh spahiu": "bardh spahia",
    "erinda ballanca": "erinda balanca",
    "agron shehaj": "agron shehaj",
    "agron shahaj": "agron shehaj",
}


@dataclass
class SpeakerResolution:
    """Outcome of resolving a raw speaker string."""
    raw_label: str
    normalized_label: str
    person_id: Optional[str]  # None if genuinely unknown (no @who attribute emitted)
    confidence: str  # "exact", "alias", "fuzzy", "heuristic", "unresolved"
    role: str = "#regular"  # "#chair", "#regular", or "#guest"
    org_id: Optional[str] = None
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
    1. full_name (normalized) -> person_id
    2. surname (normalized) -> list of person_ids
    """
    full_map: Dict[str, str] = {}
    surname_map: Dict[str, List[str]] = {}

    for pid, p in persons.items():
        # Full name: Forename Surname
        f_norm = normalize_name(f"{p.forename} {p.surname}")
        if f_norm:
            full_map[f_norm] = pid

        # Reverse: Surname Forename
        r_norm = normalize_name(f"{p.surname} {p.forename}")
        if r_norm:
            full_map[r_norm] = pid

        # Direct person_id match
        p_base = normalize_name(pid.replace("AL_PERS_", "").replace("pAL_", ""))
        full_map[p_base] = pid

        # Surname only index
        s_norm = normalize_name(p.surname)
        if s_norm:
            surname_map.setdefault(s_norm, []).append(pid)

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
            notes="Unknown speaker without identification (no @who emitted)",
        )

    norm = normalize_person_name(label)
    full_map, surname_map = _build_name_index(persons)

    # 1. Exact match on normalized full name
    if norm in full_map:
        pid = full_map[norm]
        return SpeakerResolution(
            raw_label=label,
            normalized_label=norm,
            person_id=pid,
            confidence="exact",
            role="#regular",
        )

    # 2. Match on surname if unique
    if norm in surname_map:
        candidates = surname_map[norm]
        if len(candidates) == 1:
            return SpeakerResolution(
                raw_label=label,
                normalized_label=norm,
                person_id=candidates[0],
                confidence="alias",
                role="#regular",
                notes=f"Single candidate matching surname '{norm}'",
            )

    # 3. Mint a canonical person_id if name appears to be a valid person
    minted_id = mint_person_id(strip_titles(label))
    return SpeakerResolution(
        raw_label=label,
        normalized_label=norm,
        person_id=minted_id,
        confidence="heuristic",
        role="#regular",
        notes="Heuristically minted ID (not in persons.csv)",
    )


def resolve_speaker_for_date(
    label: str,
    date: str,
    persons: Dict[str, PersonMetadata],
    sitting_chair_name: Optional[str] = None,
) -> SpeakerResolution:
    """
    Resolve a speaker label and determine date-sensitive role (#chair, #regular, #guest) & org affiliation.
    """
    res = match_speaker_label(label, persons)
    if not res.person_id:
        return res

    # Determine if speaker is the sitting / meeting chair
    if sitting_chair_name:
        norm_chair = normalize_person_name(sitting_chair_name)
        if res.normalized_label == norm_chair or (res.person_id and norm_chair in res.person_id.lower()):
            res.role = "#chair"

    if res.person_id not in persons:
        return res

    pers = persons[res.person_id]
    for aff in pers.affiliations:
        # Check if date is within affiliation range
        from_ok = (not aff.from_date) or (not date) or (date >= aff.from_date)
        to_ok = (not aff.to_date) or (not date) or (date <= aff.to_date)
        if from_ok and to_ok:
            if aff.role and aff.role in ("chairperson", "head", "chair"):
                res.role = "#chair"
            elif aff.role and aff.role in ("minister", "guest"):
                res.role = "#guest"
            res.org_id = aff.org_id
            break

    return res


def resolve_speeches(
    speeches: List[SpeechBlock],
    date: str,
    persons: Dict[str, PersonMetadata],
    sitting_chair_name: Optional[str] = None,
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
            )
        else:
            res = SpeakerResolution(
                raw_label="",
                normalized_label="",
                person_id=None,
                confidence="unresolved",
                role="#regular",
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
            fieldnames=["speech_id", "raw_label", "normalized_label", "person_id", "role", "confidence", "notes"],
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
                    "notes": res.notes or "",
                })
