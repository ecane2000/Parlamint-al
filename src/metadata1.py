# metadata.py
from __future__ import annotations
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Iterable

from .config import PARLIAMENT_NAME, CITY, LICENSE_URL
from .utils import guess_date_from_url, filename_stem_from_url

XML_NS = "http://www.w3.org/XML/1998/namespace"
TEI_NS = "http://www.tei-c.org/ns/1.0"


@dataclass
class DocumentMetadata:
    """
    Minimal per-component metadata needed to build a ParlaMint-compliant
    TEI header for one day/sitting.

    This is intentionally small; richer metadata (legislature, session,
    meeting, chair, etc.) can be added later without breaking callers.
    """
    doc_id: str           # e.g. "ParlaMint-AL_2025-10-08-0"
    date: str             # ISO date "YYYY-MM-DD"
    country_code: str     # "AL"
    language: str = "sq"  # ISO 639-1
    title_sq: Optional[str] = None
    title_en: Optional[str] = None
    source_url: Optional[str] = None


def make_document_id(country_code: str, date: str, index: int = 0) -> str:
    """
    Build a ParlaMint-like TEI xml:id for one component
    (here we treat each PDF / txt as one component).
    """
    idx = f"-{index}" if index else ""
    return f"ParlaMint-{country_code}_{date}{idx}"


def metadata_from_url(
    url: str,
    country_code: str = "AL",
    index: int = 0,
    language: str = "sq",
) -> DocumentMetadata:
    """
    Convenience helper for the current Albanian pilot:

    * infers the date from the URL (dd.mm.yyyy in filename)
    * builds a reasonable Albanian + English title
    * inserts parliament/city information from config.py
    """
    date = guess_date_from_url(url)
    doc_id = make_document_id(country_code, date, index=index)
    stem = filename_stem_from_url(url)

    title_sq = f"{PARLIAMENT_NAME}, procesverbal, {date}"
    title_en = f"{PARLIAMENT_NAME} minutes, {date}"

    return DocumentMetadata(
        doc_id=doc_id,
        date=date,
        country_code=country_code,
        language=language,
        title_sq=title_sq,
        title_en=title_en,
        source_url=url,
    )


def load_metadata_table(path: Path) -> Dict[str, DocumentMetadata]:
    """
    Optional helper: read a CSV with richer metadata and
    return a mapping from TXT / TEI stem -> DocumentMetadata.

    Expected CSV columns (header row):

        stem,date,country_code,title_sq,title_en,source_url

    Only 'stem' and 'date' are strictly required.
    """
    import csv

    table: Dict[str, DocumentMetadata] = {}
    if not path.exists():
        return table

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stem = (row.get("stem") or "").strip()
            if not stem:
                continue
            date = (row.get("date") or "").strip()
            if not date:
                # fall back on guessing from the source_url or stem
                url = row.get("source_url") or ""
                if url:
                    date = guess_date_from_url(url)
            country_code = (row.get("country_code") or "AL").strip()
            title_sq = (row.get("title_sq") or "").strip() or None
            title_en = (row.get("title_en") or "").strip() or None
            source_url = (row.get("source_url") or "").strip() or None

            doc_id = make_document_id(country_code, date)
            table[stem] = DocumentMetadata(
                doc_id=doc_id,
                date=date,
                country_code=country_code,
                title_sq=title_sq,
                title_en=title_en,
                source_url=source_url,
            )

    return table

def read_csv(path: Path):
    with path.open(encoding="utf-8") as f:
         return list(csv.DictReader(f))
 
    
    ev  = {r["date"]: r for r in read_csv(root/"events.csv")}
    return sp, org, ev
 
def resolve_person_id(name: str, speakers: dict) -> str | None:
     # naive resolver; replace with a better alias table if needed
     nm = name.strip().lower()
     for pid, row in speakers.items():
         cand = f'{row["forename"]} {row["surname"]}'.strip().lower()
         if cand == nm:
             return pid
     return None

# --- NEW: accumulate speakers into meta/speakers.csv (id,forename,surname,party_id empty,role empty)
def _split_name(name: str) -> tuple[str, str]:
    parts = name.strip().split()
    if len(parts) >= 2:
        return " ".join(parts[:-1]), parts[-1]
    return name.strip(), ""

def _mint_person_id(forename: str, surname: str) -> str:
    base = f"{forename} {surname}".strip().lower()
    base = "".join(ch for ch in base if ch.isalnum())
    return f"pAL_{base[:24]}" if base else "pAL_unknown"

def ensure_speakers_csv(speakers_iter: Iterable[str], meta_root: Path = Path("meta")) -> Dict[str, Dict]:
    """
    Merge a set of full names into meta/speakers.csv.
    Returns dict {person_id: rowdict}.
    """
    meta_root.mkdir(parents=True, exist_ok=True)
    speakers_csv = meta_root / "speakers.csv"
    existing = {}
    if speakers_csv.exists():
        for r in read_csv(speakers_csv):
            existing[r["id"]] = r

    # reverse index for quick check
    by_name = {f"{r.get('forename','')} {r.get('surname','')}".strip().lower(): pid for pid, r in existing.items()}
    added = 0
    for full in sorted(set(speakers_iter)):
        fs = full.strip()
        if not fs:
            continue
        if fs.lower() in by_name:
            continue
        forename, surname = _split_name(fs)
        pid = _mint_person_id(forename, surname)
        # avoid collision
        i = 2
        pid0 = pid
        while pid in existing:
            pid = f"{pid0}_{i}"; i += 1
        existing[pid] = {
            "id": pid,
            "forename": forename,
            "surname": surname,
            "gender": "",
            "party_id": "",
            "role": "",
            "wikidata": "",
        }
        by_name[fs.lower()] = pid
        added += 1

    # write back
    with speakers_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["id","forename","surname","gender","party_id","role","wikidata"])
        w.writeheader()
        for pid, row in sorted(existing.items()):
            w.writerow(row)
    return existing

def ensure_orgs_csv(meta_root: Path = Path("meta")) -> None:
    orgs_csv = meta_root / "orgs.csv"
    if not orgs_csv.exists():
        with orgs_csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id","name","type","abbrev","wikidata"])
            w.writeheader()
