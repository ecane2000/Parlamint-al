from pathlib import Path
from pdfminer.high_level import extract_text

def pdf_to_text(pdf_path: Path) -> str:
    return extract_text(str(pdf_path))

if __name__ == "__main__":
    from argparse import ArgumentParser
    ap = ArgumentParser()
    ap.add_argument('pdf', type=Path)
    args = ap.parse_args()
    print(pdf_to_text(args.pdf))
