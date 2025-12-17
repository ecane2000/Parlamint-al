
import re
from datetime import datetime
from typing import Optional, Tuple, List

def normalize_whitespace(text: str) -> str:
    return re.sub(r"[ \t]+", " ", text or "").strip()

def normalize_text(text: str, *, preserve_paragraphs: bool = True) -> str:
    if text is None:
        return ""
    s = text.replace("\r\n", "\n").replace("\r", "\n")
    s = "\n".join(line.rstrip() for line in s.split("\n"))
    if not preserve_paragraphs:
        s = re.sub(r"\n{3,}", "\n\n", s)
    return s

_NBSPS = ("\u00A0", "\u202F")
_DASH_MAP = {"\u2014": "–", "\u2212": "-"}

def normalize_for_segmentation(text: str) -> str:
    if text is None:
        return ""
    for nb in _NBSPS:
        text = text.replace(nb, " ")
    for src, tgt in _DASH_MAP.items():
        text = text.replace(src, tgt)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text

def strip_page_numbers(lines: List[str]) -> List[str]:
    out = []
    for ln in lines:
        if re.fullmatch(r"\s*\d+\s*", ln):
            continue
        out.append(ln)
    return out

def find_idx(lines: List[str], needle: str) -> int:
    for i, ln in enumerate(lines):
        if ln.strip().startswith(needle):
            return i
    return -1

def parse_date_from_filename_or_text(stem: str, text: str = "") -> str:
    def _safe(y, m, d):
        try:
            return datetime(int(y), int(m), int(d)).strftime("%Y-%m-%d")
        except Exception:
            return ""
    for pat in (r"(?P<y>\d{4})[-_](?P<m>\d{2})[-_](?P<d>\d{2})",
                r"(?P<d>\d{2})[.](?P<m>\d{2})[.](?P<y>\d{4})",
                r"(?P<y>\d{4})(?P<m>\d{2})(?P<d>\d{2})"):
        m = re.search(pat, stem)
        if not m and text:
            m = re.search(pat, text)
        if m:
            if 'd' in m.groupdict():
                return _safe(m.group('y'), m.group('m'), m.group('d'))
    return ""

_RE_DATETIME = re.compile(
    r"Tiran[ëe],\s*m[ëe]\s*(?P<d>\d{1,2})[.](?P<m>\d{1,2})[.](?P<y>\d{4}),\s*ora\s*(?P<h>\d{1,2}):(?P<min>\d{2})",
    flags=re.IGNORECASE,
)

def extract_date_time_from_header(text: str, scan_lines: int = 120) -> Tuple[Optional[str], Optional[str]]:
    lines = text.splitlines()[:scan_lines]
    chunk = "\n".join(lines)
    m = _RE_DATETIME.search(chunk)
    if not m:
        return None, None
    y, mth, d = m.group("y"), m.group("m"), m.group("d")
    h, mi = m.group("h").zfill(2), m.group("min").zfill(2)
    iso = ""
    try:
        iso = datetime(int(y), int(mth), int(d)).strftime("%Y-%m-%d")
    except Exception:
        iso = ""
    return (iso or None), f"{h}:{mi}"

def extract_event_type_from_cleaned(text: str, max_scan_lines: int = 120) -> Optional[str]:
    txt = normalize_for_segmentation(text)
    lines = strip_page_numbers(txt.splitlines()[:max_scan_lines])
    i_k = find_idx(lines, "KUVENDI")
    i_pv = find_idx(lines, "PROCESVERBAL")
    if i_k >= 0 and i_pv > i_k:
        mid = [ln.strip() for ln in lines[i_k+1:i_pv] if ln.strip()]
        if mid:
            return "\n".join(mid)
    return None

def split_name_function(line: str):
    try:
        import regex as _rx
        rx = _rx
        pat = r"^\s*([A-ZÇË][\p{L}.'’\-]*\s+[A-ZÇË][\p{L}.'’\-]*)\s*[–—-]\s*(.+)$"
    except Exception:
        rx = re
        pat = r"^\s*([A-ZÇË][A-Za-zÇËçëÀ-ÖØ-öø-ÿ.'’\-]*\s+[A-ZÇË][A-Za-zÇËçëÀ-ÖØ-öø-ÿ.'’\-]*)\s*[–—-]\s*(.+)$"
    m = rx.match(pat, line.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return line.strip(), None
