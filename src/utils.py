# -*- coding: utf-8 -*-
"""
Small reusable helpers used across the ParlaMint-AL repository.
"""
from __future__ import annotations
import re
from pathlib import Path
from urllib.parse import unquote

# Dash variations
UNICODE_DASHES = r"[–—-]"
SPACE_DASH_SPACE = re.compile(rf"\s*{UNICODE_DASHES}\s*")
BLANK_PARA_RE = re.compile(r"\n\s*\n", flags=re.UNICODE)
RE_VALID_PUNCT_END = re.compile(r"[.?!…][”\"»'\)\]]*\s*$")

# Abbreviations that end with a period but do NOT end a sentence
RE_ABBREV_END = re.compile(
    r"(?:\b(?:nr|dt|datë|z|znj|prof|dr|akad|sh\.a|sh\.p\.k|p\.sh|fq|neni|kap|pika)\."
    r"|\b[A-ZÇË]\.)\s*$",
    flags=re.IGNORECASE | re.UNICODE,
)

# Standalone numbered list item like "1." or "19."
RE_STANDALONE_LIST_NUM = re.compile(r"^\d+\.$")

# Speaker cue at start of line
_LOWER = r"a-zçëà-öø-ÿ"
_NAME_WORD = rf"(?!(?:Megjithëse|Ndërkohë|Përveç|Sipas|Rruga|Segmenti|Korridori|Pse|Kur|Nëse|Sepse|Prandaj|Gjithashtu)\b)[A-ZÇË][{_LOWER}’'\-]+"
RE_SPEAKER_LINE_START = re.compile(
    rf"^\s*(?:\d+\s+)?(?:(?:Z\.|Znj\.|Deputeti|Deputetja|Ministri|Ministrja|Kryetari|Kryetarja)\s+)?"
    rf"{_NAME_WORD}(?:\s+{_NAME_WORD}){{1,2}}(?:\s+[–—-]\s+|\s*[–—]\s+)",
    flags=re.UNICODE,
)
RE_NAME_PART = re.compile(
    rf"^(?:\d+\s+)?(?:(?:Z\.|Znj\.|Deputeti|Deputetja|Ministri|Ministrja|Kryetari|Kryetarja)\s+)?"
    rf"{_NAME_WORD}(?:\s+{_NAME_WORD})?$",
    flags=re.UNICODE,
)
RE_SINGLE_NAME_WORD = re.compile(rf"^{_NAME_WORD}$", flags=re.UNICODE)
RE_DASH_REST = re.compile(r"^[–—-]\s+\S", flags=re.UNICODE)

# Structural / header markers that must stay on their own line
RE_STRUCTURAL_LINE = re.compile(
    r"^(?:REPUBLIKA E SHQIPËRISË|KUVENDI|PROCESVERBAL|HAPET\s+MBLEDHJA.*|MBYLLET\s+MBLEDHJA.*|"
    r"(?:Drejton\s+mbledhjen|Seancën\s+e\s+drejton|Drejton\s+seancën|Rendi\s+i\s+ditës|Marrin\s+pjesë|Mungojnë)\s*:.*)$",
    flags=re.UNICODE,
)

# Proper nouns, titles, institutions, organizations, places, and months in Albanian parliamentary text
RE_PROPER_NOUN_START = re.compile(
    r"^(?:Shqipëri\w*|Kosov\w*|Tiran\w*|Durrës\w*|Vlor\w*|Shkod\w*|Elbasan\w*|Korç\w*|Fier\w*|"
    r"Berat\w*|Lezh\w*|Kukës\w*|Dibër\w*|Dibr\w*|Gjirokast\w*|rop\w*|Europ\w*|Evrop\w*|Ballkan\w*|"
    r"Kuvend\w*|Komision\w*|Këshill\w*|Qeveri\w*|Ministr\w*|Bashki\w*|Gjykat\w*|Prokurori\w*|"
    r"Agjenci\w*|Autoritet\w*|Institut\w*|Institucion\w*|Bank\w*|Fond\w*|Ent\w*|Drejtori\w*|Zyr\w*|"
    r"Shërbim\w*|Komunitet\w*|Republik\w*|Shtet\w*|Parti\w*|Grup\w*|Aleanc\w*|Lëvizj\w*|Bashkim\w*|"
    r"Organizat\w*|Komitet\w*|Konferenc\w*|Konvent\w*|Kushtetut\w*|Ligj\w*|Projektligj\w*|Neni\b|"
    r"Vendim\w*|Rregullor\w*|Strategji\w*|Program\w*|Marrëveshj\w*|Traktat\w*|Kod\w*|Buxhet\w*|"
    r"Raport\w*|Rezol\w*|Deklarat\w*|Seanc\w*|Legjislatur\w*|"
    r"Zot\w*|Zonj\w*|Z\.|Znj\.|Deputet\w*|Kryetar\w*|Nënkryetar\w*|Kryeminist\w*|President\w*|"
    r"Avokat\w*|Komisioner\w*|Drejtues\w*|Sekretar\w*|Relator\w*|Guvernator\w*| Kontroll\w*|"
    r"SPAK\w*|BKH\w*|KLSH\w*|KLP\w*|KLGJ\w*|KQZ\w*|KESH\w*|OSHEE\w*|OST\w*|AKSHI\w*|AZHBR\w*|"
    r"RTSH\w*|AMA\w*|AKEP\w*|ERE\w*|ERRU\w*|INSTAT\w*|FSSH\w*|ISSH\w*| NATO\w*|OSBE\w*|BE\b|BE-\w*|"
    r"OKB\w*|KiE\w*|BERZH\w*|FMN\w*|BB\b|SHBA\w*|USAID\w*|OLAF\w*|IPARD\w*|CEFTA\w*|UNESCO\w*|GDPR\w*|"
    r"Janar\w*|Shkurt\w*|Mars\w*|Prill\w*|Maj\w*|Qershor\w*|Korrik\w*|Gusht\w*|Shtator\w*|Tetor\w*|Nëntor\w*|Dhjetor\w*|"
    r"[A-ZÇË]{2,}\b)",
    flags=re.UNICODE,
)


def ensure_dir(path: Path | str) -> Path:
    """Ensure directory exists, creating parents if necessary."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_text(path: Path | str) -> str:
    """Read a text file with UTF-8 encoding, ignoring decoding errors."""
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path | str, text: str) -> None:
    """Write text to file with UTF-8 encoding, creating parent directories."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


def normalize_newlines(text: str) -> str:
    """Standardize CRLF and CR newlines to LF."""
    return (text or "").replace("\r\n", "\n").replace("\r", "\n")


def squash_ws(s: str) -> str:
    """Collapse internal spaces/tabs to a single space while keeping newlines."""
    return re.sub(r"[ \t]+", " ", s or "")


def normalize_whitespace(text: str) -> str:
    """Normalize all whitespace runs into single spaces and trim."""
    return re.sub(r"\s+", " ", text or "").strip()


def normalise_text(text: str, preserve_paragraphs: bool = False) -> str:
    """Normalize text encoding and whitespace."""
    if not text:
        return ""
    txt = normalize_newlines(text)
    if preserve_paragraphs:
        paras = [squash_ws(p.strip()) for p in txt.split("\n\n") if p.strip()]
        return "\n\n".join(paras)
    return normalize_whitespace(txt)


normalize_text = normalise_text


def count_words(text: str) -> int:
    """Count lexical words in text."""
    if not text:
        return 0
    # Split on whitespace after removing XML tags if present
    clean = re.sub(r"<[^>]+>", " ", text)
    tokens = [t for t in re.split(r"\s+", clean) if t.strip()]
    return len(tokens)


def safe_xml_text(text: str) -> str:
    """Remove control characters that are invalid in XML 1.0."""
    if not text:
        return ""
    # Remove XML-invalid characters (ASCII < 32 except \t, \n, \r)
    return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)


def guess_date_from_url(text: str) -> str:
    """
    Attempt to extract an ISO date (YYYY-MM-DD) from a URL or filename.
    Supports formats like dd.mm.yyyy, dd_mm_yyyy, dd.mm._yyyy, yyyymmdd, etc.
    """
    if not text:
        return ""
    decoded = unquote(text)

    # 1. Matches like 17.10.2025, 06.10.2025, 07.10._2025, 4.12.2025
    m = re.search(r"(\d{1,2})[\s._\-]+(\d{1,2})[\s._\-]+(\d{4})", decoded)
    if m:
        d, mo, y = m.groups()
        if 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
            return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"

    # 2. Matches like 2025-10-17 or 2025_10_17
    m2 = re.search(r"(\d{4})[\s._\-]+(\d{1,2})[\s._\-]+(\d{1,2})", decoded)
    if m2:
        y, mo, d = m2.groups()
        if 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
            return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"

    # 3. Matches like timestamp at beginning of filename e.g. 20251024...
    m3 = re.search(r"\b(20\d{2})(\d{2})(\d{2})\b", decoded)
    if m3:
        y, mo, d = m3.groups()
        if 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
            return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"

    return ""


def filename_stem_from_url(url: str) -> str:
    """Extract a sanitized, legible filename stem from a URL."""
    if not url:
        return "doc"
    raw_name = url.split("/")[-1].split("?")[0]
    decoded = unquote(raw_name)
    stem = Path(decoded).stem
    # Replace unsafe characters
    cleaned = re.sub(r"[^A-Za-z0-9_.%-]+", "_", stem).strip("_")
    return cleaned or "doc"


def normalize_name(name: str) -> str:
    """Normalize a person or speaker name for indexing and lookups."""
    return re.sub(r"\s+", " ", (name or "").strip()).lower()


def mint_person_id(full_name: str) -> str:
    """
    Create a stable, ParlaMint-style person id from a name.
    e.g. 'Agron Gjekmarkaj' -> 'AL_PERS_AgronGjekmarkaj'
    """
    full_name = (full_name or "").strip()
    parts = re.split(r"\s+", full_name)
    if len(parts) >= 2:
        surname = re.sub(r"[^A-Za-zÇËçëÀ-ÖØ-öø-ÿ]", "", parts[-1])
        forename = re.sub(r"[^A-Za-zÇËçëÀ-ÖØ-öø-ÿ]", "", parts[0])
        base = f"{forename}{surname}"
    else:
        base = re.sub(r"[^A-Za-zÇËçëÀ-ÖØ-öø-ÿ]", "", full_name) or "Unknown"
    return f"AL_PERS_{base}"


def split_paragraphs(text: str) -> list[str]:
    """Split on blank lines; trim single trailing/leading newlines per paragraph."""
    norm = normalize_newlines(text).strip("\n")
    if not norm:
        return []
    parts = BLANK_PARA_RE.split(norm)
    return [p.strip() for p in parts if p.strip()]


def _join_wrapped_lines(prev: str, nxt: str) -> str:
    """
    Join two lines that belong to the same sentence, healing hyphenated words
    split across a line wrap (e.g. 'Administrativo-\\nTerritoriale' -> 'Administrativo-Territoriale',
    'SMSI-\\nja' -> 'SMSI-ja', '2014-\\ns' -> '2014-s') while keeping space after list bullets ('1- ').
    """
    prev_s = prev.rstrip()
    nxt_s = nxt.lstrip()
    if not prev_s:
        return nxt_s
    if not nxt_s:
        return prev_s

    # If prev ends with a word-attached hyphen (and is not a standalone list bullet like "1-")
    if (
        re.search(r"[\wÇËçë%”\"»]-$", prev_s, flags=re.UNICODE)
        and not re.match(r"^\d+-$", prev_s)
        and re.match(r"^[A-Za-zÇËçë0-9]", nxt_s, flags=re.UNICODE)
    ):
        return prev_s + nxt_s

    # If nxt starts with punctuation like ',', '.', ';', ':', '!', '?', ')'
    if nxt_s[0] in ",.;:!?)]”»":
        return prev_s + nxt_s

    return prev_s + " " + nxt_s


def _ends_with_sentence_punct(line: str, next_line: str = "") -> bool:
    """
    Return True if `line` ends with genuine sentence-ending punctuation ('.', '?', '!', '…').
    Returns False if:
    - `line` does not end with '.', '?', '!', '…' (plus optional closing quotes/parens)
    - `line` is a standalone list number like '1.' or '19.'
    - `line` ends with a known abbreviation ('nr.', 'dt.', 'z.', 'znj.', 'sh.a.', etc.)
    - `line` ends with '.' and `next_line` starts with a lowercase letter
    """
    s = line.strip()
    if not s:
        return False
    if not RE_VALID_PUNCT_END.search(s):
        return False
    if RE_STANDALONE_LIST_NUM.match(s):
        return False
    if RE_ABBREV_END.search(s):
        return False
    # If it ends with a period and the next line begins with a lowercase letter, it's an abbreviation/mid-sentence dot
    if s.endswith(".") and next_line and re.match(r"^[a-zçë]", next_line.strip()):
        return False
    return True


def _should_merge_incomplete_line(buffer: str, next_line: str) -> bool:
    """
    Determine whether `buffer` (which does NOT end with sentence-ending punctuation)
    should be merged with `next_line`.
    Merges when `next_line` starts with:
    - a lowercase letter
    - a digit, quote, parenthesis, dash, or punctuation
    - a capital letter that is a person, organization, institution, place, or other proper noun
      (or any continuation word when `buffer` does not end with ':' or ';' or a short salutation ',')
    """
    nxt = next_line.strip()
    if not nxt:
        return False

    # Never merge if next_line is a speaker cue or structural marker
    if RE_SPEAKER_LINE_START.match(nxt) or RE_STRUCTURAL_LINE.match(nxt):
        return False

    # Never merge if next_line is a standalone stage direction in parentheses and buffer ends with punctuation
    if nxt.startswith("(") and nxt.endswith(")") and buffer.rstrip().endswith((":", ";")):
        return False

    first_ch = nxt[0]
    # 1. Next line begins with a lowercase letter -> always merge
    if first_ch.islower() or first_ch in "çë":
        return True

    # 2. Next line begins with a digit, quote, or punctuation -> merge unless buffer ends with ':' before a numbered item
    if not (first_ch.isupper() or first_ch in "ÇË"):
        if buffer.rstrip().endswith(":") and re.match(r"^\d+[\.\)\-]\s", nxt):
            return False
        return True

    # 3. Next line begins with a capital letter:
    # Check if it matches known proper nouns (persons, orgs, institutions, places, titles)
    if RE_PROPER_NOUN_START.match(nxt):
        return True

    # Check if next_line starts with a capitalized person name (e.g., Firstname Lastname or Capitalized proper noun)
    # In PDF line wraps, any line that does NOT end with sentence punctuation ('.', '?', '!')
    # and does NOT end with ':' or ';' (introducing a list) or a short salutation comma
    # is broken mid-sentence across the PDF margin and must be merged.
    buf_r = buffer.rstrip()
    if buf_r.endswith((":", ";")):
        return False
    if buf_r.endswith(",") and len(buf_r) < 45 and any(
        w in buf_r.lower() for w in ("nderuar", "kolegë", "kryetar", "zoti", "zonja", "faleminderit", "mirëdita")
    ):
        return False

    return True


def reconstruct_broken_lines(text: str) -> str:
    """
    Merge lines that do not end with sentence-end punctuation (. ! ?).
    Heals sentences fragmented across PDF line wraps (including across blank lines
    inserted by pdfminer between every visual line) while preserving speaker turns,
    structural headers, and complete paragraphs.
    """
    raw_lines = normalize_newlines(text).splitlines()
    if not raw_lines:
        return ""

    # Step 1: Filter out empty lines and join wrapped speaker cues
    # (e.g. "Niko\nPeleshi\n–\nFaleminderit..." -> "Niko Peleshi – Faleminderit...")
    non_empty = [ln.strip() for ln in raw_lines if ln.strip()]
    if not non_empty:
        return ""

    pre_merged: list[str] = []
    idx = 0
    n = len(non_empty)
    while idx < n:
        cur = non_empty[idx]
        # Pattern A: Line i is "Firstname" (or "Z. Firstname"), Line i+1 is "Lastname", Line i+2 starts with "–"
        if (
            idx + 2 < n
            and RE_NAME_PART.match(cur)
            and RE_SINGLE_NAME_WORD.match(non_empty[idx + 1])
            and RE_DASH_REST.match(non_empty[idx + 2])
        ):
            pre_merged.append(f"{cur} {non_empty[idx + 1]} {non_empty[idx + 2]}")
            idx += 3
            continue
        # Pattern B: Line i is "Firstname Lastname", Line i+1 starts with "–"
        if (
            idx + 1 < n
            and RE_NAME_PART.match(cur)
            and " " in cur
            and RE_DASH_REST.match(non_empty[idx + 1])
        ):
            pre_merged.append(f"{cur} {non_empty[idx + 1]}")
            idx += 2
            continue
        # Pattern C: Line i is "Firstname Lastname –" (ends with dash) and Line i+1 is the start of speech
        if (
            idx + 1 < n
            and re.match(
                rf"^(?:\d+\s+)?(?:(?:Z\.|Znj\.|Deputeti|Deputetja|Ministri|Ministrja|Kryetari|Kryetarja)\s+)?"
                rf"{_NAME_WORD}\s+{_NAME_WORD}\s*[–—-]$",
                cur,
                flags=re.UNICODE,
            )
        ):
            pre_merged.append(f"{cur} {non_empty[idx + 1]}")
            idx += 2
            continue

        pre_merged.append(cur)
        idx += 1

    # Step 2: Merge fragmented sentences across line breaks
    out: list[str] = []
    buffer = pre_merged[0]

    for i in range(1, len(pre_merged)):
        next_line = pre_merged[i]

        if not buffer:
            buffer = next_line
            continue

        # If buffer is a structural header line (e.g. HAPET MBLEDHJA, PROCESVERBAL), flush it
        if RE_STRUCTURAL_LINE.match(buffer) and not buffer.lower().startswith("rendi i ditës"):
            out.append(buffer)
            buffer = next_line
            continue

        # If next_line is a speaker cue or structural marker, never merge into buffer
        if RE_SPEAKER_LINE_START.match(next_line) or RE_STRUCTURAL_LINE.match(next_line):
            out.append(buffer)
            buffer = next_line
            continue

        # Check if buffer ends with sentence-end punctuation ('.', '?', '!', '…')
        if _ends_with_sentence_punct(buffer, next_line):
            out.append(buffer)
            buffer = next_line
        elif _should_merge_incomplete_line(buffer, next_line):
            buffer = _join_wrapped_lines(buffer, next_line)
        else:
            out.append(buffer)
            buffer = next_line

    if buffer:
        out.append(buffer)

    return "\n\n".join(out)
