# -*- coding: utf-8 -*-
"""
Document segmentation layer for ParlaMint-AL:
Segments cleaned sitting transcripts into sitting blocks, speech turns, and paragraphs.
Produces structured intermediate dataclasses (SittingBlock, SpeechBlock) rather than XML directly.
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
DASH_CLASS = r"–—-"

# Regex matching a speaker cue at start of line/paragraph:
# e.g., "Niko Peleshi – Mirëdita...", "8 Taulant Balla – ...", "Z. Taulant Balla – ..."
SPEAKER_CUE_RE = re.compile(
    rf"^\s*(?:\d+\s+)?(?P<label>(?:(?:Z\.|Znj\.|Deputeti|Deputetja|Ministri|Ministrja|Kryetari|Kryetarja)\s+)?[A-ZÇË][{ALPHA_CLASS}’'\.\-]*\s+[A-ZÇË][{ALPHA_CLASS}’'\.\-]*)\s*[{DASH_CLASS}]\s*(?P<rest>.*)$",
    flags=re.UNICODE | re.DOTALL,
)


@dataclass
class SpeechBlock:
    """Represents a single speech/utterance turn in a sitting."""
    speech_id: str
    raw_speaker_label: Optional[str]
    speech_type: Optional[str] = "speech"
    paragraphs: List[str] = field(default_factory=list)


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


def split_into_paragraphs(text: str) -> List[str]:
    """Split text on blank lines, trimming excess whitespace."""
    return split_paragraphs(text)


def is_speaker_line(line: str) -> bool:
    """Check if a line matches the speaker cue pattern."""
    return bool(SPEAKER_CUE_RE.match(line.strip()))


def normalize_speaker_label(label: str) -> str:
    """Clean and normalize a raw speaker label."""
    return squash_ws(label).strip()


def merge_broken_speech_lines(lines: List[str]) -> List[str]:
    """Merge wrapped lines that do not terminate with standard sentence punctuation."""
    return reconstruct_broken_lines("\n".join(lines)).splitlines()


def _split_header_body(txt: str) -> tuple[str, str]:
    """Split text into (header_text, body_text) at 'HAPET MBLEDHJA'."""
    lines = normalize_newlines(txt).splitlines()
    i_open = None
    for i, l in enumerate(lines):
        if l.strip().upper().startswith("HAPET MBLEDHJA"):
            i_open = i
            break
    if i_open is None:
        return "", normalize_newlines(txt)
    header = "\n".join(lines[:i_open])
    body = "\n".join(lines[i_open + 1 :])
    return header, body


LINE_CUE_RE = re.compile(
    rf"^\s*(?:\d+\s+)?(?:(?:Z\.|Znj\.|Deputeti|Deputetja|Ministri|Ministrja|Kryetari|Kryetarja)\s+)?[A-ZÇË][{ALPHA_CLASS}’'\.\-]*\s+[A-ZÇË][{ALPHA_CLASS}’'\.\-]*\s*[{DASH_CLASS}]",
    flags=re.UNICODE,
)


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
            # Check if previous item in out was already empty
            if out and out[-1] != "":
                out.append("")
            out.append(stripped)
        else:
            out.append(l)

    return "\n".join(out)


def segment_document(text: str, doc_id: str, date: str, title: str | None = None) -> SittingBlock:
    """
    Parse a cleaned transcript text into a SittingBlock containing SpeechBlocks.
    """
    header_txt, body_txt = _split_header_body(text)
    body_txt = reconstruct_broken_lines(body_txt)
    body_txt = _reinsert_breaks_before_cues(body_txt)

    paras = split_into_paragraphs(body_txt)
    speeches: List[SpeechBlock] = []
    current_speech: Optional[SpeechBlock] = None
    speech_counter = 1

    for para in paras:
        m = SPEAKER_CUE_RE.match(para)
        if m:
            if current_speech and current_speech.paragraphs:
                speeches.append(current_speech)

            raw_label = normalize_speaker_label(m.group("label"))
            rest = m.group("rest").strip()
            speech_id = f"{doc_id}.u{speech_counter:04d}"
            speech_counter += 1

            current_speech = SpeechBlock(
                speech_id=speech_id,
                raw_speaker_label=raw_label,
                speech_type="speech",
                paragraphs=[rest] if rest else [],
            )
        else:
            if current_speech is not None:
                current_speech.paragraphs.append(para.strip())
            else:
                # Text before the first speaker in body
                speech_id = f"{doc_id}.u{speech_counter:04d}"
                speech_counter += 1
                current_speech = SpeechBlock(
                    speech_id=speech_id,
                    raw_speaker_label=None,
                    speech_type="narrative",
                    paragraphs=[para.strip()],
                )

    if current_speech and current_speech.paragraphs:
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
