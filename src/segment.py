# -*- coding: utf-8 -*-
"""
Document segmentation layer for ParlaMint-AL conforming to ParlaMint 5.0:
Segments cleaned sitting transcripts into sitting blocks, speech turns, paragraphs,
and structured non-lexical chamber events (vocal, kinesic, note).
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict

from .utils import (
    split_paragraphs,
    normalize_newlines,
    reconstruct_broken_lines,
    squash_ws,
)

ALPHA_CLASS = r"\wÀ-ÖØ-öø-ÿÇËçë"
LOWER_CLASS = r"a-zçëà-öø-ÿ"
DASH_CLASS = r"–—-"
NAME_TOKEN = rf"(?!(?:Megjithëse|Ndërkohë|Përveç|Sipas|Rruga|Segmenti|Korridori|Pse|Kur|Nëse|Sepse|Prandaj|Gjithashtu)\b)[A-ZÇË][{LOWER_CLASS}’'\-]+"

# Speaker cue pattern: e.g. "Niko Peleshi – Mirëdita...", "8 Taulant Balla – ...", "Z. Taulant Balla – ..."
SPEAKER_CUE_RE = re.compile(
    rf"^\s*(?:\d+\s+)?(?P<label>(?:(?:Z\.|Znj\.|Deputeti|Deputetja|Ministri|Ministrja|Kryetari|Kryetarja)\s+)?{NAME_TOKEN}\s+{NAME_TOKEN})(?:\s+[{DASH_CLASS}]\s+|\s*[–—]\s+)(?P<rest>.*)$",
    flags=re.UNICODE | re.DOTALL,
)

LINE_CUE_RE = re.compile(
    rf"^\s*(?:\d+\s+)?(?:(?:Z\.|Znj\.|Deputeti|Deputetja|Ministri|Ministrja|Kryetari|Kryetarja)\s+)?{NAME_TOKEN}\s+{NAME_TOKEN}(?:\s+[{DASH_CLASS}]\s+|\s*[–—]\s+)",
    flags=re.UNICODE,
)

# Header paratext to remove if embedded mid-transcript
PARATEXT_LINES_RE = re.compile(
    r"^\s*(?:REPUBLIKA E SHQIPËRISË|KUVENDI|PROCESVERBAL|Drejton mbledhjen:|Rendi i ditës:|Marrin pjesë:|Mungojnë:)\s*$",
    re.I | re.M
)


@dataclass
class DiscourseItem:
    """Represents a speech segment (<seg>) or a chamber event (<vocal>, <kinesic>, <note>)."""
    kind: str  # "seg", "vocal", "kinesic", "note"
    type_attr: Optional[str] = None  # "interruption", "applause", "laughter", "comment"
    text: str = ""


@dataclass
class SpeechBlock:
    """Represents a single speech turn in a parliamentary sitting."""
    speech_id: str
    raw_speaker_label: Optional[str]
    speech_type: Optional[str] = "speech"
    items: List[DiscourseItem] = field(default_factory=list)

    @property
    def paragraphs(self) -> List[str]:
        """Convenience property for backward compatibility."""
        return [it.text for it in self.items if it.kind == "seg"]

    @paragraphs.setter
    def paragraphs(self, paras: List[str]):
        self.items = [DiscourseItem(kind="seg", text=p) for p in paras]


@dataclass
class SittingBlock:
    """Represents a full parliamentary sitting with header and speech turns."""
    doc_id: str
    date: str
    title: Optional[str] = None
    speeches: List[SpeechBlock] = field(default_factory=list)
    header_text: Optional[str] = None
    chair_name: Optional[str] = None
    chair_role: Optional[str] = None
    agenda_text: Optional[str] = None


def _classify_stage_direction(inner_text: str) -> Optional[DiscourseItem]:
    """
    Check if parenthetical text is a genuine parliamentary stage direction
    (vocal, kinesic, or procedural note) rather than a spoken parenthetical/acronym.
    """
    inner = inner_text.strip()
    low = inner.lower()
    if any(k in low for k in ("pa mikrofon", "ndërhyrje", "ndërhyre", "interruption", "flet nga salla", "jashtë mikrofonit")):
        return DiscourseItem(kind="vocal", type_attr="interruption", text=inner)
    if any(k in low for k in ("duartrokitje", "applause")):
        return DiscourseItem(kind="kinesic", type_attr="applause", text=inner)
    if any(k in low for k in ("të qeshura", "ilaritet", "laughter")):
        return DiscourseItem(kind="vocal", type_attr="laughter", text=inner)
    if any(
        k in low
        for k in (
            "bie gongu",
            "debat në sallë",
            "zhurmë në sallë",
            "pas pushimit",
            "shkëputje e shkurtër",
            "minutë heshtje",
            "drejtimin e seancës",
            "lexon rendin",
            "seanca filloi",
            "seanca u mbyll",
            "mbledhja u hap",
            "mbledhja u mbyll",
            "mungesë incizimi",
            "largohet nga salla",
            "kthehet në sallë",
            "vijon",
        )
    ):
        return DiscourseItem(kind="note", type_attr="comment", text=inner)
    return None


def parse_discourse_text(raw_para: str) -> List[DiscourseItem]:
    """
    Parse a paragraph into speech segments and embedded events (vocal, kinesic, notes).
    e.g. "Teksti para (Ndërhyrje pa mikrofon.) Teksti pas" -> [seg, vocal, seg]
    Normal spoken parentheticals like "(BERZH)" or "(GDPR)" remain inside the <seg>.
    """
    cleaned = squash_ws(raw_para).strip()
    if not cleaned:
        return []

    if cleaned.upper().startswith("MBYLLET MBLEDHJA") or cleaned.upper().startswith("HAPET MBLEDHJA"):
        return [DiscourseItem(kind="note", type_attr="comment", text=cleaned)]

    # Check if the entire paragraph is a parenthetical event
    if cleaned.startswith("(") and cleaned.endswith(")") and "(" not in cleaned[1:-1]:
        inner = cleaned[1:-1].strip()
        classified = _classify_stage_direction(inner)
        if classified:
            return [classified]
        return [DiscourseItem(kind="note", type_attr="comment", text=inner)]

    # Inline event extraction: only split <seg> on genuine stage directions
    event_pattern = re.compile(r"\(([^)]+)\)")
    items: List[DiscourseItem] = []
    last_end = 0

    for m in event_pattern.finditer(cleaned):
        event_text = m.group(1).strip()
        classified = _classify_stage_direction(event_text)
        if classified is None:
            continue

        start, end = m.span()
        prefix = cleaned[last_end:start].strip()
        if prefix:
            items.append(DiscourseItem(kind="seg", text=prefix))

        items.append(classified)
        last_end = end

    rest = cleaned[last_end:].strip()
    if rest:
        items.append(DiscourseItem(kind="seg", text=rest))

    return items if items else [DiscourseItem(kind="seg", text=cleaned)]


def split_into_paragraphs(text: str) -> List[str]:
    """Split text on blank lines, trimming excess whitespace."""
    return split_paragraphs(text)


def is_speaker_line(line: str) -> bool:
    """Check if a line matches the speaker cue pattern."""
    return bool(LINE_CUE_RE.match(line.strip()))


def normalize_speaker_label(label: str) -> str:
    """Clean and normalize a raw speaker label."""
    return squash_ws(label).strip()


def merge_broken_speech_lines(lines: List[str]) -> List[str]:
    """Merge wrapped lines that do not terminate with standard sentence punctuation."""
    return reconstruct_broken_lines("\n".join(lines)).splitlines()


def _strip_closing_signatures(lines: List[str]) -> List[str]:
    """
    Strip closing signature blocks at the end of transcripts (after MBYLLET MBLEDHJA
    or '(Seanca u mbyll në orën ...)').
    """
    cut_idx = None
    for i in range(max(0, len(lines) - 25), len(lines)):
        s = lines[i].strip()
        up = s.upper()
        if up.startswith("MBYLLET MBLEDHJA"):
            cut_idx = i + 1
            break
        if "seanca u mbyll në orën" in s.lower() or "mbledhja u mbyll në orën" in s.lower():
            cut_idx = i + 1
            break
    if cut_idx is not None:
        return lines[:cut_idx]
    return lines


def _split_header_body(txt: str) -> tuple[str, str]:
    """
    Split text into (header_text, body_text) at 'HAPET MBLEDHJA' or at the first
    speaker cue following 'Rendi i ditës:' (for plenary sessions).
    Also strips trailing signature lines after session closing.
    """
    lines = _strip_closing_signatures(normalize_newlines(txt).splitlines())
    i_open = None
    for i, l in enumerate(lines):
        if l.strip().upper().startswith("HAPET MBLEDHJA"):
            i_open = i
            break

    if i_open is not None:
        header = "\n".join(lines[:i_open])
        body = "\n".join(lines[i_open + 1 :])
        return header, body

    # Fallback for plenary transcripts without 'HAPET MBLEDHJA':
    # Find 'Rendi i ditës:' and split at the first speaker cue after it
    i_rendi = None
    for i, l in enumerate(lines[:100]):
        if l.strip().lower().startswith("rendi i ditës"):
            i_rendi = i
            break
    search_start = (i_rendi + 1) if i_rendi is not None else 0
    for i in range(search_start, len(lines)):
        if LINE_CUE_RE.match(lines[i].strip()):
            header = "\n".join(lines[:i])
            body = "\n".join(lines[i:])
            return header, body

    return "", "\n".join(lines)


def _reinsert_breaks_before_cues(body: str) -> str:
    """Ensure every speaker cue is preceded by a blank line so it forms a new paragraph."""
    out: List[str] = []
    lines = normalize_newlines(body).splitlines()

    for l in lines:
        stripped = l.strip()
        if not stripped:
            out.append("")
            continue

        if stripped.upper().startswith("HAPET MBLEDHJA"):
            out.append(l)
            continue

        if LINE_CUE_RE.match(stripped):
            if out and out[-1] != "":
                out.append("")
            out.append(stripped)
        else:
            out.append(l)

    return "\n".join(out)


def segment_document(text: str, doc_id: str, date: str, title: str | None = None) -> SittingBlock:
    """
    Parse a cleaned transcript text into a SittingBlock containing SpeechBlocks.
    Extracts speech turns, separates paragraphs, and categorizes non-speech events.
    """
    header_txt, body_txt = _split_header_body(text)
    body_txt = reconstruct_broken_lines(body_txt)
    body_txt = _reinsert_breaks_before_cues(body_txt)

    raw_paras = split_into_paragraphs(body_txt)
    speeches: List[SpeechBlock] = []
    current_speech: Optional[SpeechBlock] = None
    speech_counter = 1

    for para in raw_paras:
        m = SPEAKER_CUE_RE.match(para)
        if m:
            if current_speech and current_speech.items:
                speeches.append(current_speech)

            raw_label = normalize_speaker_label(m.group("label"))
            rest = m.group("rest").strip()
            speech_id = f"{doc_id}.u{speech_counter}"
            speech_counter += 1

            current_speech = SpeechBlock(
                speech_id=speech_id,
                raw_speaker_label=raw_label,
                speech_type="speech",
                items=parse_discourse_text(rest) if rest else [],
            )
        else:
            discourse_items = parse_discourse_text(para)
            if not discourse_items:
                continue

            if current_speech is not None:
                current_speech.items.extend(discourse_items)
            else:
                # Narrative / procedural text before first speaker
                speech_id = f"{doc_id}.u{speech_counter}"
                speech_counter += 1
                current_speech = SpeechBlock(
                    speech_id=speech_id,
                    raw_speaker_label=None,
                    speech_type="narrative",
                    items=discourse_items,
                )

    if current_speech and current_speech.items:
        speeches.append(current_speech)

    return SittingBlock(
        doc_id=doc_id,
        date=date,
        title=title,
        speeches=speeches,
        header_text=header_txt,
    )


def segment_by_speakers(clean_txt: str) -> Dict:
    """
    Backward-compatibility helper: returns dict with header_text and utterances list.
    """
    block = segment_document(clean_txt, doc_id="temp_doc", date="")
    utterances = [
        {
            "who_name": s.raw_speaker_label or "UNKNOWN",
            "paragraphs": s.paragraphs,
        }
        for s in block.speeches
    ]
    return {
        "header_text": block.header_text or "",
        "utterances": utterances,
    }
