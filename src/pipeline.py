# pipeline.py
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Dict

from . import config
from .utils import filename_stem_from_url, guess_date_from_url
from .metadata import DocumentMetadata, metadata_from_url, make_document_id
from .tei import txt_to_tei
# from .annotate import annotate_corpus_stanza


def build_url_index() -> Dict[str, str]:
    """
    Map filename stems to their source URLs so that we can recover
    basic metadata (date, source URL) when building TEI.
    """
    index: Dict[str, str] = {}
    for url in getattr(config, "PDF_URLS", []):
        stem = filename_stem_from_url(url)
        index[stem] = url
    return index


def convert_inbox_to_tei(
    inbox_root: Path,
    out_root: Path,
    country_code: str = "AL",
) -> None:
    """
    Read cleaned TXT files from <inbox_root>/cleaned and write
    TEI components into <out_root>/plain.
    """
    cleaned = inbox_root / "cleaned"
    if not cleaned.exists():
        raise FileNotFoundError(f"Cleaned TXT directory not found: {cleaned}")

    plain_dir = out_root / "plain"
    plain_dir.mkdir(parents=True, exist_ok=True)

    url_index = build_url_index()
    per_date_counter: Dict[str, int] = defaultdict(int)

    for txt_path in sorted(cleaned.glob("*.txt")):
        stem = txt_path.stem
        url = url_index.get(stem)

        if url:
            meta = metadata_from_url(url, country_code=country_code)
        else:
            # Fallback: try to guess date from the stem itself
            date = guess_date_from_url(stem)
            doc_id = make_document_id(country_code, date)
            meta = DocumentMetadata(
                doc_id=doc_id,
                date=date,
                country_code=country_code,
            )

        # If multiple components share the same date, disambiguate
        idx = per_date_counter[meta.date]
        per_date_counter[meta.date] += 1
        if idx:
            meta.doc_id = make_document_id(meta.country_code, meta.date, index=idx)

        out_path = plain_dir / f"{meta.doc_id}.xml"
        txt_to_tei(txt_path, meta, out_path)


def annotate_tei(
    out_root: Path,
    annotator: str = "stanza",
) -> None:
    plain_dir = out_root / "plain"
    ana_dir = out_root / "ana"

    if annotator == "stanza":
        # lazy import – only needed if you actually request annotation
        from .annotate_stanza import annotate_corpus_stanza
        annotate_corpus_stanza(plain_dir, ana_dir)

    elif annotator == "udpipe":
        from .annotate_udpipe import annotate_corpus_udpipe
        from pathlib import Path as _Path
        annotate_corpus_udpipe(plain_dir, ana_dir, _Path(config.UDPIPE_MODEL_PATH))

    else:
        raise ValueError(f"Unknown annotator: {annotator}")

def main(argv=None) -> None:
    import argparse

    ap = argparse.ArgumentParser(
        description="Minimal ParlaMint-AL pipeline: TXT -> TEI -> TEI.ana"
    )
    ap.add_argument(
        "--inbox",
        type=Path,
        default=Path("inbox"),
        help="Root inbox directory containing cleaned/ TXT files.",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("out"),
        help="Output root directory (plain/ and ana/ will be created).",
    )
    ap.add_argument(
        "--country-code",
        default="AL",
        help="ISO 3166 country code used in TEI ids (default: AL).",
    )
    ap.add_argument(
        "--with-ana",
        action="store_true",
        help="Also run linguistic annotation to produce .ana TEI.",
    )
    ap.add_argument(
        "--annotator",
        choices=["stanza", "udpipe"],
        default="stanza",
        help="Annotator to use for .ana files.",
    )

    args = ap.parse_args(argv)

    # Always: TXT -> TEI
    convert_inbox_to_tei(args.inbox, args.out, country_code=args.country_code)

    # Only if requested: TEI -> TEI.ana
    if args.with_ana:
        annotate_tei(args.out, annotator=args.annotator)


if __name__ == "__main__":
    main()
