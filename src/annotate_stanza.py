# -*- coding: utf-8 -*-
"""
Stanza linguistic annotation layer for ParlaMint-AL:
Transforms plain TEI files (out/TEI/plain/YYYY/*.xml) into linguistically annotated
TEI.ana files (out/TEI/ana/YYYY/*.ana.xml) with tokenized and morphosyntactically tagged
<s>, <w>, and <pc> elements using Stanza.
"""
from __future__ import annotations
from pathlib import Path
from typing import Iterable
import xml.etree.ElementTree as ET

from .tei import _indent_xml, qname, TEI_NS, XML_NS

try:
    import stanza
except ImportError:
    stanza = None


def iter_plain_tei_files(plain_dir: Path | str) -> Iterable[Path]:
    """Iterate over plain TEI component files."""
    return sorted(Path(plain_dir).rglob("*.xml"))


def stanza_pipeline(lang: str = "sq"):
    """Initialize Stanza UD pipeline for Albanian."""
    if stanza is None:
        raise RuntimeError(
            "stanza is not installed. Install it with `pip install stanza` "
            "and download the Albanian models with `python -m stanza.download sq`."
        )
    return stanza.Pipeline(
        lang=lang,
        processors="tokenize,pos,lemma,depparse",
        tokenize_no_ssplit=False,
    )


def annotate_seg_with_stanza(seg_el: ET.Element, nlp) -> None:
    """
    Replace the plain text content of a <seg> element with
    tokenized sentences (<s>) and words/punctuation (<w>, <pc>).
    """
    text = (seg_el.text or "").strip()
    if not text:
        return

    doc = nlp(text)

    xml_id = seg_el.get(f"{{{XML_NS}}}id")
    seg_el.clear()
    if xml_id:
        seg_el.set(f"{{{XML_NS}}}id", xml_id)

    for sent_idx, sent in enumerate(doc.sentences, start=1):
        s_attrs = {}
        if xml_id:
            s_attrs[f"{{{XML_NS}}}id"] = f"{xml_id}.s{sent_idx}"
        s_el = ET.SubElement(seg_el, qname("s"), s_attrs)

        for w in sent.words:
            tag = "pc" if w.upos == "PUNCT" else "w"
            token_el = ET.SubElement(s_el, qname(tag))
            token_el.text = w.text

            if w.lemma:
                token_el.set("lemma", w.lemma)
            if w.upos:
                token_el.set("pos", w.upos)
            if w.feats:
                token_el.set("msd", w.feats)
            if w.deprel:
                token_el.set("dep", w.deprel)
            if w.head is not None:
                token_el.set("head", str(w.head))


def annotate_file_stanza(src: Path | str, dst: Path | str, nlp) -> None:
    """Annotate a single TEI XML file using Stanza and write to dst."""
    tree = ET.parse(src)
    root = tree.getroot()

    # Update root xml:id and ana tag for .ana format
    orig_id = root.get(f"{{{XML_NS}}}id", "")
    if orig_id and not orig_id.endswith(".ana"):
        root.set(f"{{{XML_NS}}}id", f"{orig_id}.ana")

    current_ana = root.get("ana", "")
    if "#ud-sq-stanza" not in current_ana:
        root.set("ana", f"{current_ana} #ud-sq-stanza".strip())

    for seg in root.findall(f".//{{{TEI_NS}}}seg"):
        annotate_seg_with_stanza(seg, nlp)

    dst_path = Path(dst)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    _indent_xml(root)
    tree.write(dst_path, encoding="utf-8", xml_declaration=True)


def annotate_corpus_stanza(
    plain_dir: Path | str,
    ana_dir: Path | str,
    lang: str = "sq",
) -> None:
    """Annotate all plain TEI files in plain_dir to ana_dir."""
    nlp = stanza_pipeline(lang=lang)
    plain_p = Path(plain_dir)
    ana_p = Path(ana_dir)
    ana_p.mkdir(parents=True, exist_ok=True)

    for src in iter_plain_tei_files(plain_p):
        target_name = src.stem + ".ana.xml"
        dst = ana_p / src.relative_to(plain_p).parent / target_name
        annotate_file_stanza(src, dst, nlp)
        print(f"[OK] Stanza annotated: {src.name} -> {target_name}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Annotate ParlaMint-AL plain TEI files using Stanza")
    ap.add_argument("--plain", default="out/TEI/plain", help="Directory of plain TEI files")
    ap.add_argument("--ana", default="out/TEI/ana", help="Directory for output .ana.xml files")
    args = ap.parse_args()

    annotate_corpus_stanza(args.plain, args.ana)
