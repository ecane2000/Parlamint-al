# -*- coding: utf-8 -*-
import argparse
from pathlib import Path
from .root import repo_root_for
from .utils import ensure_dir, read_text, write_text, looks_like_committee
from .extract import clean_folder, extract_header_block
from .segment import segment_by_speakers
from .metadata import DocumentMetadata
from .tei import write_plain_day

REPO_ROOT = repo_root_for(__file__)

def convert_inbox_to_tei(inbox: str, out_dir: str):
    inbox_p = Path(inbox)
    out_p = Path(out_dir)
    ensure_dir(out_p)

    for p in sorted(inbox_p.glob("*.txt")):
        clean_txt = read_text(p)  # already cleaned if you run extract.clean_folder; OK if not
        # Header
        header = extract_header_block(clean_txt)
        eventType = header.get("eventType", "")
        eventTypeAna = "#parla.sitting"
        if looks_like_committee(eventType):
            eventTypeAna += " #parla.committee"

        md = DocumentMetadata(
            date=header.get("date", ""),
            time=header.get("time"),
            eventType=eventType,
            eventTypeAna=eventTypeAna,
            chair_name=header.get("chair_name"),
            chair_role=header.get("chair_role"),
            topics=header.get("agenda_text"),
        )

        # Segment body into utterances
        seg = segment_by_speakers(clean_txt)
        utterances = seg["utterances"]

        # Build speaker index on the fly (chair + utterers)
        if md.chair_name:
            md.speaker_id(md.chair_name)
        for u in utterances:
            md.speaker_id(u.get("who_name", "UNKNOWN"))

        # Assemble session dict for TEI writer
        session = {
            "date": md.date,
            "time": md.time,
            "eventType": md.eventType,
            "chair_name": md.chair_name,
            "chair_role": md.chair_role,
            "utterances": utterances,
        }
        # Title (HU-like)
        if session["eventType"]:
            one_line = " / ".join([ln.strip() for ln in session["eventType"].splitlines() if ln.strip()])
            session["title"] = f"Kuvendi i Shqipërisë — {one_line}, {md.date}"
        else:
            session["title"] = f"Kuvendi i Shqipërisë, Procesverbal, {md.date}"

        out_path = out_p / "plain" / f"ParlaMint-AL_{md.date or p.stem}.xml"
        write_plain_day(
            session,
            speakers_idx=md.speakers_idx,
            out_path=str(out_path),
            license_url=md.licence_url,
            eventTypeAna=md.eventTypeAna,
        )
        print(f"Wrote {out_path}")

def main():
    ap = argparse.ArgumentParser(description="ParlaMint-AL end-to-end day-file builder (HU-style).")
    ap.add_argument("--inbox", default=str(REPO_ROOT / "texts"), help="Folder with cleaned TXT files")
    ap.add_argument("--out", default=str(REPO_ROOT / "out"), help="Output folder")
    ap.add_argument("--clean_from", default=None, help="If set, clean raw TXT from this folder into --inbox first")
    ap.add_argument("--urls", default=None, help="Optional: crawl PDFs listed in this file (requires requests, pdfminer.six)")
    args = ap.parse_args()

    # Optional: crawl PDFs → texts
    if args.urls:
        from .crawl import main as crawl_main
        # run crawl in-process
        import sys
        sys.argv = ["crawl.py", "--urls", args.urls, "--txt_out", args.inbox]
        crawl_main()

    # Optional: clean raw folder into inbox
    if args.clean_from:
        raw = Path(args.clean_from)
        inbox = Path(args.inbox)
        clean_folder(raw, inbox)

    convert_inbox_to_tei(args.inbox, args.out)

if __name__ == "__main__":
    main()
