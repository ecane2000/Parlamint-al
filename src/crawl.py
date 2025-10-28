import requests
from pathlib import Path
from .config import PDF_URLS

def crawl_pdfs(out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for url in PDF_URLS:
        name = url.split('/')[-1]
        name = name.replace('%20', '_').replace('%C3%AB', 'ë')
        if not name.lower().endswith('.pdf'):
            name += '.pdf'
        path = out_dir / name
        if not path.exists():
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            path.write_bytes(r.content)
        saved.append(path)
    return saved

if __name__ == "__main__":
    from argparse import ArgumentParser
    ap = ArgumentParser()
    ap.add_argument('--out', default='inbox')
    args = ap.parse_args()
    paths = crawl_pdfs(Path(args.out))
    print("Downloaded:", *map(str, paths), sep='\n- ')
