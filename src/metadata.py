# metadata.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict

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
