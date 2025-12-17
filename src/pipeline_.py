
import argparse
from pathlib import Path
import glob
import unicodedata

from .segment import segment_by_speakers
from .tei import write_plain_day
from .utils import normalize_for_segmentation, parse_date_from_filename_or_text

DEFAULT_LICENSE = "https://creativecommons.org/licenses/by/4.0/"

def _mint_pid(name: str) -> str:
    base = ''.join(ch for ch in unicodedata.normalize('NFKD', name.lower()) if ch.isalnum())
    return f"pAL_{base}" if base else "pAL_UNKNOWN"

def convert_inbox_to_tei(inbox_dir: str, out_dir: str):
    inbox = Path(inbox_dir)
    candidates = []
    candidates += glob.glob(str(inbox / "*.txt"))
    candidates += glob.glob(str(inbox / "cleaned" / "*.txt"))
    if not candidates:
        raise FileNotFoundError(f"No TXT files found in {inbox} or {inbox/'cleaned'}")
    out = Path(out_dir)
    out_plain = out / "plain"
    out_plain.mkdir(parents=True, exist_ok=True)

    per_date_count = {}

    for f in sorted(candidates):
        stem = Path(f).stem
        raw_txt = Path(f).read_text(encoding="utf-8")
        cleaned = normalize_for_segmentation(raw_txt)

        session = segment_by_speakers(stem, cleaned)

        if not session.get("date"):
            session["date"] = parse_date_from_filename_or_text(stem, raw_txt) or "0000-00-00"

        name_to_pid = {}
        for who in session.get("speakers_found", []):
            name_to_pid[who.lower()] = _mint_pid(who)

        date = session.get("date") or "0000-00-00"
        cnt = per_date_count.get(date, 0)
        per_date_count[date] = cnt + 1
        suffix = "" if cnt == 0 else f"_{cnt+1:02d}"
        out_path = out_plain / f"ParlaMint-AL_{date}{suffix}.xml"

        write_plain_day(session, speakers_idx=name_to_pid, out_path=out_path, license_url=DEFAULT_LICENSE)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inbox", default="inbox", help="Folder with cleaned TXT (or inbox/cleaned)")
    ap.add_argument("--out", default="out", help="Output root folder")
    args = ap.parse_args()
    convert_inbox_to_tei(args.inbox, args.out)

if __name__ == "__main__":
    main()
