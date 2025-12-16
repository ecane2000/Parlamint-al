from __future__ import annotations
from collections import defaultdict
from typing import Dict
from . import config
from pathlib import Path
import glob
from .segment import segment_by_speakers, reinsert_breaks_before_speakers
from .metadata import ensure_speakers_csv, ensure_orgs_csv
from .tei import write_plain_day
from .utils import filename_stem_from_url, guess_date_from_url, normalize_text, normalize_for_segmentation


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


def convert_inbox_to_tei(inbox_root: Path, out_root: Path) -> None:
    """
    Read cleaned TXT files from <inbox_root>/cleaned, detect speakers/utterances,
    and write ParlaMint plain day-files into <out_root>/plain.
    """
    cleaned = Path(inbox_root) / "cleaned"
    if not cleaned.exists():
        raise FileNotFoundError(f"Cleaned TXT directory not found: {cleaned}")
    plain_dir = Path(out_root) / "plain"
    (plain_dir).mkdir(parents=True, exist_ok=True)

    for f in sorted(glob.glob(str(cleaned / "*.txt"))):
        stem = Path(f).stem
        raw_txt = Path(f).read_text(encoding="utf-8")
        txt = normalize_text(raw_txt)
        text = normalize_for_segmentation(text)
        text = reinsert_breaks_before_speakers(text)
        session = segment_by_speakers(stem, text)
        
        
        # (i) accumulate speakers -> meta/speakers.csv
        people_map = ensure_speakers_csv(session["speakers_found"], meta_root=Path("meta"))
        ensure_orgs_csv(meta_root=Path("meta"))  # (iv) ensure meta/orgs.csv exists

        # build name->id (lowercased full name)
        name_to_pid = {}
        for pid, row in people_map.items():
            key = f'{row.get("forename","")} {row.get("surname","")}'.strip().lower()
            if key:
                name_to_pid[key] = pid

        out_path = plain_dir / f"ParlaMint-AL_{session['date']}.xml"
        write_plain_day(session, speakers_idx=name_to_pid, out_path=out_path,
                        license_url="https://creativecommons.org/licenses/by/4.0/")


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
    convert_inbox_to_tei(args.inbox, args.out)
    # Only if requested: TEI -> TEI.ana
    if args.with_ana:
        annotate_tei(args.out, annotator=args.annotator)


if __name__ == "__main__":
    main()