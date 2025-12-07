import argparse
from pathlib import Path
from .config import PARLIAMENT_NAME, CITY, LICENSE_URL, PDF_URLS
from .crawl import crawl_to_txt
from .metadata import DocMeta
from .utils import chunk_paragraphs, filename_stem_from_url
from .tei import build_header, insert_body_plain, insert_body_ana, serialize

try:
    from .annotate import ud_doc
    HAS_UD = True
except Exception:
    HAS_UD = False

def build_plain(xml_out: Path, meta: DocMeta, paragraphs: list[str]):
    root = build_header(meta.title, meta.source_url, meta.when_iso, PARLIAMENT_NAME, CITY, LICENSE_URL)
    root = insert_body_plain(root, paragraphs)
    xml_out.write_text(serialize(root), encoding='utf-8')

def build_ana(xml_out: Path, meta: DocMeta, text: str):
    root = build_header(meta.title.replace('(plain)','(.ana)'), meta.source_url, meta.when_iso, PARLIAMENT_NAME, CITY, LICENSE_URL)
    if not HAS_UD:
        raise RuntimeError("UD pipeline not available. Run: stanza.download('sq') and retry.")
    sents = ud_doc(text)
    root = insert_body_ana(root, sents)
    xml_out.write_text(serialize(root), encoding='utf-8')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--inbox', default='inbox', help='Inbox root for TXT (crawler writes raw/ and cleaned/)')

    ap.add_argument('--out', default='out', help='Output folder (TEI)')
    ap.add_argument('--with-ana', action='store_true', help='Also build .ana annotated TEI using Stanza')
    args = ap.parse_args()

    inbox = Path(args.inbox); inbox.mkdir(parents=True, exist_ok=True)
    inbox = Path(args.inbox); inbox.mkdir(parents=True, exist_ok=True)

    out = Path(args.out); (out / 'TEI' / 'plain').mkdir(parents=True, exist_ok=True)
    if args.with_ana: (out / 'TEI' / 'ana').mkdir(parents=True, exist_ok=True)

    # 1) Crawl sources → TXT (raw + cleaned). Returns list of RAW paths.
    raw_txt_paths = crawl_to_txt(inbox, do_clean=True)

    # 2) Build a mapping stem → original URL so metadata can cite the source.
    stem_to_url = {filename_stem_from_url(u): u for u in PDF_URLS}

    # 3) For each RAW TXT, prefer CLEANED if present; then build TEI.
    cleaned_dir = inbox / "cleaned"
    for raw_path in raw_txt_paths:
        stem = raw_path.stem
        txt_path = cleaned_dir / f"{stem}.txt" if (cleaned_dir / f"{stem}.txt").exists() else raw_path
        text = txt_path.read_text(encoding="utf-8", errors="replace")
        paragraphs = chunk_paragraphs(text)

        meta = DocMeta.from_source(path=txt_path, url=stem_to_url.get(stem))

        plain_out = out / 'TEI' / 'plain' / f"ParlaMint-AL_{meta.when_iso}.xml"
        build_plain(plain_out, meta, paragraphs[:20] or paragraphs)

        if args.with_ana:
            ana_out = out / 'TEI' / 'ana' / f"ParlaMint-AL_{meta.when_iso}.ana.xml"
            build_ana(ana_out, meta, '\n'.join(paragraphs[:5]))

    print("Done. Outputs in:", out)

if __name__ == '__main__':
    main()
