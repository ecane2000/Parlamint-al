import re
from datetime import datetime
from urllib.parse import urlparse

DATE_RE = re.compile(r"(\d{2})[.](\d{2})[.](\d{4})")

def guess_date_from_url(url: str) -> str:
    m = DATE_RE.search(url)
    if m:
        d, mth, y = m.groups()
        return f"{y}-{mth}-{d}"
    return datetime.today().strftime("%Y-%m-%d")

def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def chunk_paragraphs(text: str):
    parts = re.split(r"\n\s*\n+", text.strip())
    return [p.strip() for p in parts if p.strip()]
def filename_stem_from_url(url: str) -> str:
    """
    Create a stable stem used by the crawler for TXT names, so we can map
    TXT files back to their source URLs.
    """
    name = urlparse(url).path.split('/')[-1] or "document"
    name = name.replace('%20', '_').replace('%C3%AB', 'ë')
    if name.lower().endswith('.pdf'):
        name = name[:-4]
    return name or "document"




