# -*- coding: utf-8 -*-
"""
ParlaMint-AL pipeline:
- Optional crawl: download PDFs and extract raw TXT (if --urls or config.PDF_URLS)
- Clean raw TXT -> texts/
- Segment speakers and write TEI day files -> out/plain/
"""

import argparse
from pathlib import Path
from typing import List, Dict

# --- Local imports (these modules should be in src/) ---
try:
    from .root import repo_root_for  # optional, used if present
except Exception:  # pragma: no cover
    def repo_root_for(_p: Path) -> Path:
        return Path.cwd()

from . import crawl as crawl_mod
from .extract import clean_folder, extract_header_block
from .segment import segment_by_speakers
from .tei import write_plain_day
from .utils import (
    read_text,
    ensure_dir,
    normalize_name,
    mint_person_id,
)
from .config import PDF_URLS as CONFIG_PDF_URLS

# ---- Defaults / constants ----------------------------------------------------

DEFAULT_LICENSE = "https://creativecommons.org/licenses/by/4.0/"
REPO_ROOT = repo_root_for(Path(__file__).resolve())
DEFAULT_INBOX = REPO_ROOT / "texts"
DEFAULT_RAW_TXT = REPO_ROOT / "raw_txt"
DEFAULT_OUT = REPO_ROOT / "out"
DEFAULT_PDFS = REPO_ROOT / "pdfs"


# ---- Helpers -----------------------------------------------------------------

def _load_urls_from_file(path: Path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(f"URLs file not found: {path}")
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip() and not ln.strip().startswith("#")]


def _crawl_if_requested(urls_file: Path = None) -> None:
    """
    Crawl when:
      - --urls file is provided, OR
      - config.PDF_URLS is non-empty.
    Saves PDFs under pdfs/ and raw text under raw_txt/.
    """
    urls: List[str] = []
    if urls_file:
        urls = _load_urls_from_file(urls_file)
    elif CONFIG_PDF_URLS:
        urls = [u for u in CONFIG_PDF_URLS if u and not u.strip().startswith("#")]

    if not urls:
        return  # nothing to crawl

    # Ensure directories
    ensure_dir(DEFAULT_PDFS)
    ensure_dir(DEFAULT_RAW_TXT)

    # Use the helper that accepts a Python list of URLs
    if hasattr(crawl_mod, "crawl_urls"):
        crawl_mod.crawl_urls(urls, pdf_out=str(DEFAULT_PDFS), txt_out=str(DEFAULT_RAW_TXT))
    else:
        # Fallback: emulate crawl.py --urls path by writing a temp file
        tmp = REPO_ROOT / ".tmp_urls.txt"
        tmp.write_text("\n".join(urls), encoding="utf-8")
        try:
            # If your crawl.py exposes a main(), call it with argparse-like globals,
            # otherwise adapt to whatever API you have there.
            crawl_mod.main()  # assumes crawl.py reads --urls itself (only if wired)
        finally:
            try:
                tmp.unlink()
            except Exception:
                pass


def _build_speakers_index(utterances: List[Dict[str, str]]) -> Dict[str, str]:
    """
    Map normalized speaker names -> stable ParlaMint-style person ids.
    """
    idx: Dict[str, str] = {}
    for u in utterances:
        nm = (u.get("who_name") or "").strip()
        if not nm:
            continue
        key = normalize_name(nm)
        if key not in idx:
            idx[key] = mint_person_id(nm)
    return idx


def _session_title(meta: dict) -> str:
    date = meta.get("date") or ""
    et = (meta.get("eventType") or "").splitlines()
    et_head = f" – {et[0]}" if et else ""
    return f"Kuvendi i Shqipërisë – Procesverbal{et_head} – {date}" if date else f"Kuvendi i Shqipërisë – Procesverbal{et_head}"


def _convert_inbox_to_tei(inbox: Path, out_root: Path) -> None:
    """
    For every *.txt in inbox/, produce a TEI file under out/plain/.
    """
    out_plain = out_root / "plain"
    ensure_dir(out_plain)

    for p in sorted(inbox.glob("*.txt")):
        txt = read_text(p)

        # 1) extract header metadata from the cleaned text (date, time, chair, eventType, agenda)
        header = extract_header_block(txt)

        # 2) segment speakers (only after "HAPET MBLEDHJA")
        seg = segment_by_speakers(txt)
        utterances = seg.get("utterances", [])

        # 3) person index for @who
        speakers_idx = _build_speakers_index(utterances)

        # 4) build session dictionary for TEI writer
        session = {
            "title": _session_title(header),
            "date": header.get("date", ""),
            "time": header.get("time", ""),
            "eventType": header.get("eventType", ""),
            "chair_name": header.get("chair_name", ""),
            "chair_role": header.get("chair_role", ""),
            "agenda_text": header.get("agenda_text", ""),
            "utterances": utterances,
        }

        # 5) output filename
        date_part = (header.get("date") or p.stem).replace("/", "-")
        out_path = out_plain / f"ParlaMint-AL_{date_part}.xml"

        # 6) write TEI
        write_plain_day(
            session=session,
            speakers_idx=speakers_idx,
            out_path=str(out_path),
            license_url=DEFAULT_LICENSE,
            eventTypeAna="#parla.sitting",
        )

        print(f"[OK] {p.name} -> {out_path.relative_to(REPO_ROOT)}")


# ---- CLI ---------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="ParlaMint-AL pipeline")
    ap.add_argument("--urls", type=str, default=None,
                    help="Path to urls.txt (one PDF URL per line). If omitted, falls back to config.PDF_URLS.")
    ap.add_argument("--clean_from", type=str, default=None,
                    help="If set, clean raw TXT from this folder into --inbox before building TEI (e.g., raw_txt).")
    ap.add_argument("--inbox", type=str, default=str(DEFAULT_INBOX),
                    help="Folder with cleaned TXT ready for TEI (default: ./texts)")
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT),
                    help="Output root folder (TEI goes to out/plain/)")
    return ap


def main():
    args = build_arg_parser().parse_args()

    urls_file = Path(args.urls) if args.urls else None
    inbox = Path(args.inbox)
    out_root = Path(args.out)

    # 0) Optional crawl if --urls given or config.PDF_URLS non-empty
    _crawl_if_requested(urls_file)

    # 1) Optional clean stage (raw_txt -> texts/)
    if args.clean_from:
        src_raw = Path(args.clean_from)
        if not src_raw.exists():
            raise FileNotFoundError(f"--clean_from points to a missing folder: {src_raw}")
        ensure_dir(inbox)
        clean_folder(src_raw, inbox)

    # 2) Convert cleaned inbox -> TEI day files under out/plain
    ensure_dir(out_root)
    _convert_inbox_to_tei(inbox, out_root)


if __name__ == "__main__":
    main()
