import argparse
from pathlib import Path
from .config import PARLIAMENT_NAME, CITY, LICENSE_URL, PDF_URLS
from .crawl import crawl_pdfs
from .extract import pdf_to_text
from .metadata import DocMeta
from .utils import chunk_paragraphs
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
    ap.add_argument('--inbox', default='inbox', help='Folder for downloaded PDFs')
    ap.add_argument('--out', default='out', help='Output folder (TEI)')
    ap.add_argument('--with-ana', action='store_true', help='Also build .ana annotated TEI using Stanza')
    args = ap.parse_args()

    inbox = Path(args.inbox); inbox.mkdir(parents=True, exist_ok=True)
    out = Path(args.out); (out / 'TEI' / 'plain').mkdir(parents=True, exist_ok=True)
    if args.with_ana: (out / 'TEI' / 'ana').mkdir(parents=True, exist_ok=True)

    pdfs = crawl_pdfs(inbox)
    for url, pdf_path in zip(PDF_URLS, pdfs):
        meta = DocMeta.from_url(url)
        text = pdf_to_text(pdf_path)
        paragraphs = chunk_paragraphs(text)

        plain_out = out / 'TEI' / 'plain' / f"ParlaMint-AL_{meta.when_iso}.xml"
        build_plain(plain_out, meta, paragraphs[:20] or paragraphs)

        if args.with_ana:
            ana_out = out / 'TEI' / 'ana' / f"ParlaMint-AL_{meta.when_iso}.ana.xml"
            build_ana(ana_out, meta, '\n'.join(paragraphs[:5]))

    print("Done. Outputs in:", out)

if __name__ == '__main__':
    main()
