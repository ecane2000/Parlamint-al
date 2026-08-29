# -*- coding: utf-8 -*-
"""
End-to-End Orchestration Pipeline for ParlaMint-AL conforming to ParlaMint 5.0:
Coordinates source acquisition, cleaning, segmentation, metadata building,
taxonomies generation, TEI encoding, root corpus generation, and linguistic annotation.

Stages:
  --stage tei    : Clean text -> Segment -> Resolve speakers -> out/TEI/plain/*.xml
  --stage lists  : metadata/*.csv -> out/TEI/ParlaMint-AL-listPerson.xml & listOrg.xml & taxonomies
  --stage root   : Generate/refresh out/TEI/ParlaMint-AL.xml master corpus file
  --stage ana    : Annotate out/TEI/plain/*.xml -> out/TEI/ana/*.ana.xml & ParlaMint-AL.ana.xml
  --stage all    : Run lists -> tei -> root -> (optional) ana
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .config import (
    PROJECT_ROOT,
    RAW_DIR,
    CLEANED_DIR,
    OUT_TEI_DIR,
    PLAIN_DIR,
    ANA_DIR,
    METADATA_DIR,
    DOCUMENTS_CSV,
    PERSONS_CSV,
    AFFILIATIONS_CSV,
    ORGS_CSV,
    PATH_INBOX_RAW,
    PATH_INBOX_CLEANED,
    PDF_URLS,
    COUNTRY_CODE,
    LANGUAGE_CODE,
)
from .utils import (
    ensure_dir,
    read_text,
    guess_date_from_url,
    filename_stem_from_url,
)
from .crawl import crawl_urls, crawl_to_txt
from .extract import clean_folder, extract_header_block
from .segment import segment_document
from .metadata import (
    DocumentMetadata,
    load_metadata_table,
    get_document_metadata,
    make_document_id,
)
from .person_org_metadata import (
    load_persons_csv,
    load_affiliations_csv,
    load_orgs_csv,
    write_listPerson,
    write_listOrg,
)
from .taxonomies import write_all_taxonomies
from .resolve_speakers import resolve_speeches, write_unresolved_report
from .tei import segmented_to_tei
from .build_root import write_root_corpus_file
from .update_root_includes import update_parlamint_root, update_parlamint_ana_root


def build_url_index(urls: Optional[List[str]] = None) -> Dict[str, str]:
    """Build a mapping from filename stem to source URL."""
    target_urls = urls if urls is not None else PDF_URLS
    index: Dict[str, str] = {}
    for u in target_urls:
        if u and not u.startswith("#"):
            stem = filename_stem_from_url(u)
            index[stem] = u
    return index


def convert_inbox_to_tei(
    inbox_root: Path | str,
    out_root: Path | str,
    metadata_dir: Path | str = METADATA_DIR,
    country_code: str = COUNTRY_CODE,
) -> List[Path]:
    """
    Stage 'tei':
    Read cleaned transcripts in inbox_root, segment into sitting and speech turns,
    resolve speaker entities against persons.csv, and serialize to out_root/plain/*.xml.
    """
    inbox_path = Path(inbox_root)
    out_plain = Path(out_root) / "plain" if not str(out_root).endswith("plain") else Path(out_root)
    ensure_dir(out_plain)

    meta_path = Path(metadata_dir)
    docs_csv = meta_path / "documents.csv" if not meta_path.is_file() else meta_path
    persons_csv = meta_path / "persons.csv"
    affs_csv = meta_path / "affiliations.csv"

    # Load metadata layers
    doc_table = load_metadata_table(docs_csv) if docs_csv.exists() else {}
    url_index = build_url_index()
    persons = load_persons_csv(persons_csv) if persons_csv.exists() else {}
    if affs_csv.exists() and persons:
        load_affiliations_csv(affs_csv, persons)

    generated_files: List[Path] = []
    unresolved_all = {}

    txt_files = sorted(inbox_path.glob("*.txt"))
    if not txt_files:
        print(f"[WARN] No .txt files found in {inbox_path}")
        return generated_files

    for txt_file in txt_files:
        text = read_text(txt_file)
        if not text.strip():
            continue

        # Extract header cues
        hdr_info = extract_header_block(text)
        stem = txt_file.stem
        date = hdr_info.get("date") or guess_date_from_url(stem) or "2025-01-01"

        # Lookup document metadata
        meta = get_document_metadata(stem, url_index=url_index, metadata_table=doc_table)
        if not meta.date or meta.date == "2025-01-01":
            meta.date = date
        if not meta.doc_id or "0000" in meta.doc_id:
            meta.doc_id = make_document_id(country_code, date)
        if hdr_info.get("chair_name"):
            meta.chair_name = hdr_info["chair_name"]
            meta.chair_role = hdr_info.get("chair_role")

        # Segment document
        sitting = segment_document(text, doc_id=meta.doc_id, date=meta.date)

        # Resolve speakers
        resolutions = resolve_speeches(
            sitting.speeches,
            date=meta.date,
            persons=persons,
            sitting_chair_name=meta.chair_name or sitting.chair_name,
        )
        unresolved_all.update(resolutions)

        # Write plain TEI component file
        out_file = out_plain / f"{meta.doc_id}.xml"
        segmented_to_tei(sitting, meta, out_file, resolutions=resolutions)
        generated_files.append(out_file)
        print(f"[OK] TEI component: {txt_file.name} -> {out_file.relative_to(PROJECT_ROOT) if out_file.is_relative_to(PROJECT_ROOT) else out_file}")

    # Write unresolved speakers audit report
    audit_report = Path(out_root) / "unresolved_speakers_report.csv"
    write_unresolved_report(unresolved_all, audit_report)

    return generated_files


def build_lists(
    metadata_dir: Path | str = METADATA_DIR,
    out_root: Path | str = OUT_TEI_DIR,
) -> tuple[Path, Path]:
    """
    Stage 'lists':
    Load persons, affiliations, and orgs from metadata/ and write:
    - out_root/ParlaMint-AL-listPerson.xml
    - out_root/ParlaMint-AL-listOrg.xml
    - Shared ParlaMint 5.0 taxonomies
    """
    meta_path = Path(metadata_dir)
    out_dir = Path(out_root)
    ensure_dir(out_dir)

    persons_csv = meta_path / "persons.csv"
    affs_csv = meta_path / "affiliations.csv"
    orgs_csv = meta_path / "orgs.csv"

    # Fallback to meta/ if metadata/ doesn't exist yet
    if not persons_csv.exists() and (PROJECT_ROOT / "meta" / "speakers.csv").exists():
        persons_csv = PROJECT_ROOT / "meta" / "speakers.csv"
    if not orgs_csv.exists() and (PROJECT_ROOT / "meta" / "orgs.csv").exists():
        orgs_csv = PROJECT_ROOT / "meta" / "orgs.csv"

    persons = load_persons_csv(persons_csv)
    if affs_csv.exists() and persons:
        load_affiliations_csv(affs_csv, persons)

    orgs = load_orgs_csv(orgs_csv)

    list_person_path = out_dir / f"ParlaMint-{COUNTRY_CODE}-listPerson.xml"
    list_org_path = out_dir / f"ParlaMint-{COUNTRY_CODE}-listOrg.xml"

    write_listPerson(persons.values(), list_person_path)
    write_listOrg(orgs.values(), list_org_path)

    # Write shared taxonomies
    written_tax = write_all_taxonomies(out_dir)

    print(f"[OK] Wrote listPerson ({len(persons)} entries) -> {list_person_path}")
    print(f"[OK] Wrote listOrg    ({len(orgs)} entries) -> {list_org_path}")
    print(f"[OK] Wrote {len(written_tax)} shared taxonomies -> {out_dir}")

    return list_person_path, list_org_path


def build_roots(out_root: Path | str = OUT_TEI_DIR) -> Path:
    """
    Stage 'root':
    Create or refresh the master corpus root out_root/ParlaMint-AL.xml.
    """
    out_dir = Path(out_root)
    plain_dir = out_dir / "plain"
    root_xml = out_dir / f"ParlaMint-{COUNTRY_CODE}.xml"

    update_parlamint_root(root_xml, plain_dir, href_prefix="plain/")
    print(f"[OK] Master TEI root refreshed -> {root_xml}")
    return root_xml


def annotate_tei(
    out_root: Path | str = OUT_TEI_DIR,
    annotator: str = "stanza",
) -> None:
    """
    Stage 'ana':
    Linguistically annotate plain TEI files into out_root/ana/*.ana.xml
    and update out_root/ParlaMint-AL.ana.xml.
    """
    out_dir = Path(out_root)
    plain_dir = out_dir / "plain"
    ana_dir = out_dir / "ana"
    ensure_dir(ana_dir)

    print(f"[*] Running linguistic annotation with annotator='{annotator}'...")
    plain_files = sorted(plain_dir.glob("*.xml"))
    if not plain_files:
        print(f"[WARN] No plain TEI files found in {plain_dir} to annotate.")
        return

    if annotator == "udpipe":
        from .annotate_udpipe import annotate_component_udpipe
        for pf in plain_files:
            out_ana_file = ana_dir / f"{pf.stem}.ana.xml"
            annotate_component_udpipe(pf, out_ana_file)
            print(f"[OK] UDPipe annotated: {pf.name} -> {out_ana_file.name}")
    else:
        from .annotate_stanza import annotate_component_stanza
        for pf in plain_files:
            out_ana_file = ana_dir / f"{pf.stem}.ana.xml"
            annotate_component_stanza(pf, out_ana_file)
            print(f"[OK] Stanza annotated: {pf.name} -> {out_ana_file.name}")

    ana_root = out_dir / f"ParlaMint-{COUNTRY_CODE}.ana.xml"
    update_parlamint_ana_root(ana_root, ana_dir, href_prefix="ana/")
    print(f"[OK] Master annotated TEI root refreshed -> {ana_root}")


def run_pipeline(
    stage: str = "all",
    inbox_dir: Path | str = CLEANED_DIR,
    out_dir: Path | str = OUT_TEI_DIR,
    metadata_dir: Path | str = METADATA_DIR,
    crawl_first: bool = False,
    clean_first: bool = False,
    annotator: str = "stanza",
    with_ana: bool = False,
    limit: Optional[int] = 10,
) -> None:
    """Run the pipeline end-to-end or execute a single stage."""
    inbox_p = Path(inbox_dir)
    out_p = Path(out_dir)
    meta_p = Path(metadata_dir)

    # Optional pre-processing
    if crawl_first:
        print(f"[*] Stage: Crawling and downloading fresh PDFs (limit={limit or 10}) to {RAW_DIR}...")
        crawl_to_txt(limit=limit or 10)
        print(f"[*] Stage: Cleaning raw text files from {PATH_INBOX_RAW} -> {inbox_p}...")
        clean_folder(PATH_INBOX_RAW, inbox_p)

    elif clean_first:
        print(f"[*] Stage: Cleaning raw text files from {PATH_INBOX_RAW} -> {inbox_p}...")
        clean_folder(PATH_INBOX_RAW, inbox_p)

    print(f"[*] Executing pipeline stage: '{stage}'")

    if stage in ("lists", "all"):
        if stage == "all":
            print("[*] --- Step 1/3: Building listPerson, listOrg XML & Taxonomies ---")
        build_lists(metadata_dir=meta_p, out_root=out_p)

    if stage in ("tei", "all"):
        if stage == "all":
            print("[*] --- Step 2/3: Generating component TEI plain files ---")
        convert_inbox_to_tei(inbox_root=inbox_p, out_root=out_p, metadata_dir=meta_p)

    if stage in ("root", "all"):
        if stage == "all":
            print("[*] --- Step 3/3: Building master ParlaMint-AL.xml root ---")
        build_roots(out_root=out_p)

    if stage == "ana" or (stage == "all" and with_ana):
        if stage == "all":
            print("[*] --- Step 4/4: Performing linguistic annotation (.ana) ---")
        annotate_tei(out_root=out_p, annotator=annotator)

    print("\n[SUCCESS] Pipeline stage completed successfully.")


def main(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(
        description="ParlaMint-AL Parliamentary Pipeline CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--stage",
        choices=["tei", "lists", "root", "ana", "all"],
        default="all",
        help="Pipeline stage to execute",
    )
    parser.add_argument("--crawl", action="store_true", help="Crawl PDFs before running stages")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of fresh PDFs to crawl")
    parser.add_argument("--clean", action="store_true", help="Clean raw transcripts before running stages")
    parser.add_argument("--inbox", type=str, default=CLEANED_DIR, help="Directory containing cleaned transcripts")
    parser.add_argument("--out", type=str, default=OUT_TEI_DIR, help="Output directory for TEI XML files")
    parser.add_argument("--metadata_dir", type=str, default=METADATA_DIR, help="Directory containing metadata CSV files")
    parser.add_argument("--annotator", choices=["stanza", "udpipe"], default="stanza", help="Annotator for stage 'ana'")
    parser.add_argument("--with_ana", action="store_true", help="Include .ana linguistic annotation when running stage all")

    args = parser.parse_args(argv)

    run_pipeline(
        stage=args.stage,
        inbox_dir=args.inbox,
        out_dir=args.out,
        metadata_dir=args.metadata_dir,
        crawl_first=args.crawl,
        clean_first=args.clean,
        annotator=args.annotator,
        with_ana=args.with_ana,
        limit=args.limit,
    )


if __name__ == "__main__":
    main()
