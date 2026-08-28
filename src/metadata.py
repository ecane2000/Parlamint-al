# -*- coding: utf-8 -*-
"""
Document-level metadata construction layer for ParlaMint-AL:
Handles creation, loading, and querying of DocumentMetadata for individual sitting components.
"""
from __future__ import annotations
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict

from .config import PARLIAMENT_NAME, COUNTRY_CODE, LANGUAGE_CODE
from .utils import guess_date_from_url, filename_stem_from_url


@dataclass
class DocumentMetadata:
    """Document-level metadata for a single parliamentary sitting."""
    doc_id: str
    date: str
    country_code: str = COUNTRY_CODE
    language: str = LANGUAGE_CODE
    title_sq: Optional[str] = None
    title_en: Optional[str] = None
    source_url: Optional[str] = None
    legislature_id: Optional[str] = None
    session_id: Optional[str] = None
    meeting_id: Optional[str] = None
    meeting_type: Optional[str] = None
    chair_name: Optional[str] = None
    chair_role: Optional[str] = None


def make_document_id(country_code: str = COUNTRY_CODE, date: str = "", index: int = 0) -> str:
    """Build a standard ParlaMint document ID e.g. ParlaMint-AL_2025-10-17."""
    clean_date = (date or "0000-00-00").replace("/", "-")
    idx = f"-{index}" if index > 0 else ""
    return f"ParlaMint-{country_code}_{clean_date}{idx}"


def metadata_from_url(
    url: str,
    country_code: str = COUNTRY_CODE,
    index: int = 0,
    language: str = LANGUAGE_CODE,
) -> DocumentMetadata:
    """Create a default DocumentMetadata object inferred from a source URL."""
    date = guess_date_from_url(url) or "2025-01-01"
    doc_id = make_document_id(country_code, date, index=index)
    title_sq = f"{PARLIAMENT_NAME}, procesverbal, {date}"
    title_en = f"Parliament of Albania, minutes, {date}"

    return DocumentMetadata(
        doc_id=doc_id,
        date=date,
        country_code=country_code,
        language=language,
        title_sq=title_sq,
        title_en=title_en,
        source_url=url,
    )


def metadata_from_stem(
    stem: str,
    country_code: str = COUNTRY_CODE,
    index: int = 0,
    language: str = LANGUAGE_CODE,
) -> DocumentMetadata:
    """Create a default DocumentMetadata object inferred from a filename stem."""
    date = guess_date_from_url(stem) or "2025-01-01"
    doc_id = make_document_id(country_code, date, index=index)
    title_sq = f"{PARLIAMENT_NAME}, procesverbal, {date}"
    title_en = f"Parliament of Albania, minutes, {date}"

    return DocumentMetadata(
        doc_id=doc_id,
        date=date,
        country_code=country_code,
        language=language,
        title_sq=title_sq,
        title_en=title_en,
        source_url=None,
    )


def load_metadata_table(path: Path | str) -> Dict[str, DocumentMetadata]:
    """
    Read metadata/documents.csv and return a dict mapping stem -> DocumentMetadata.
    Expected CSV header:
      stem,date,title_sq,title_en,source_url,legislature_id,session_id,meeting_id,meeting_type
    """
    p = Path(path)
    table: Dict[str, DocumentMetadata] = {}
    if not p.exists():
        return table

    with p.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stem = (row.get("stem") or "").strip()
            if not stem:
                continue
            date = (row.get("date") or "").strip() or guess_date_from_url(row.get("source_url") or stem) or "2025-01-01"
            country_code = (row.get("country_code") or COUNTRY_CODE).strip()
            doc_id = row.get("doc_id") or make_document_id(country_code, date)
            title_sq = (row.get("title_sq") or "").strip() or f"{PARLIAMENT_NAME}, procesverbal, {date}"
            title_en = (row.get("title_en") or "").strip() or f"Parliament of Albania, minutes, {date}"
            source_url = (row.get("source_url") or "").strip() or None
            legislature_id = (row.get("legislature_id") or "").strip() or None
            session_id = (row.get("session_id") or "").strip() or None
            meeting_id = (row.get("meeting_id") or "").strip() or None
            meeting_type = (row.get("meeting_type") or "").strip() or None

            table[stem] = DocumentMetadata(
                doc_id=doc_id,
                date=date,
                country_code=country_code,
                language=LANGUAGE_CODE,
                title_sq=title_sq,
                title_en=title_en,
                source_url=source_url,
                legislature_id=legislature_id,
                session_id=session_id,
                meeting_id=meeting_id,
                meeting_type=meeting_type,
            )

    return table


def save_documents_csv(docs: list[DocumentMetadata] | dict[str, DocumentMetadata], path: Path | str) -> None:
    """Save document metadata records to CSV."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    items = docs.values() if isinstance(docs, dict) else docs
    fieldnames = [
        "stem",
        "doc_id",
        "date",
        "country_code",
        "title_sq",
        "title_en",
        "source_url",
        "legislature_id",
        "session_id",
        "meeting_id",
        "meeting_type",
    ]

    with p.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for doc in items:
            stem = filename_stem_from_url(doc.source_url or doc.doc_id)
            writer.writerow({
                "stem": stem,
                "doc_id": doc.doc_id,
                "date": doc.date,
                "country_code": doc.country_code,
                "title_sq": doc.title_sq or "",
                "title_en": doc.title_en or "",
                "source_url": doc.source_url or "",
                "legislature_id": doc.legislature_id or "",
                "session_id": doc.session_id or "",
                "meeting_id": doc.meeting_id or "",
                "meeting_type": doc.meeting_type or "",
            })


def get_document_metadata(
    stem: str,
    url_index: dict[str, str] | None = None,
    metadata_table: dict[str, DocumentMetadata] | None = None,
) -> DocumentMetadata:
    """
    Lookup DocumentMetadata for a file stem, checking the metadata table first,
    then falling back to the URL index, and finally inferring from the stem itself.
    """
    if metadata_table and stem in metadata_table:
        return metadata_table[stem]

    url = (url_index or {}).get(stem)
    if url:
        return metadata_from_url(url)

    return metadata_from_stem(stem)
