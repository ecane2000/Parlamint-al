# annotate_stanza.py  (annotator option 1)
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import xml.etree.ElementTree as ET

from .tei import qname, TEI_NS, XML_NS  # type: ignore[attr-defined]

# Stanza is an optional dependency; import lazily in main()
try:
    import stanza  # type: ignore[import]
except ImportError:  # pragma: no cover - handled at runtime
    stanza = None  # type: ignore[assignment]


def iter_plain_tei_files(plain_dir: Path) -> Iterable[Path]:
    return sorted(plain_dir.glob("*.xml"))


def stanza_pipeline(lang: str = "sq"):
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
    Replace the text content of <seg> with <s>/<w>/<pc> structure
    using Stanza's UD annotation.
    """
    text = (seg_el.text or "").strip()
    if not text:
        return

    doc = nlp(text)

    # Preserve xml:id, then remove children/attributes
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


def annotate_file_stanza(src: Path, dst: Path, nlp) -> None:
    tree = ET.parse(src)
    root = tree.getroot()

    # Mark this component as linguistically annotated
    root.set("ana", (root.get("ana", "") + " #ud-sq-stanza").strip())

    for seg in root.findall(".//{%s}seg" % TEI_NS):
        annotate_seg_with_stanza(seg, nlp)

    dst.parent.mkdir(parents=True, exist_ok=True)
    tree.write(dst, encoding="utf-8", xml_declaration=True)


def annotate_corpus_stanza(
    plain_dir: Path,
    ana_dir: Path,
    lang: str = "sq",
) -> None:
    """
    Annotate all TEI component files in `plain_dir` and write
    linguistically annotated `.ana.xml` files to `ana_dir`.
    """
    nlp = stanza_pipeline(lang=lang)

    for src in iter_plain_tei_files(plain_dir):
        target_name = src.stem + ".ana.xml"
        dst = ana_dir / target_name
        annotate_file_stanza(src, dst, nlp)


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--plain", type=Path, default=Path("out/plain"))
    ap.add_argument("--ana", type=Path, default=Path("out/ana"))
    args = ap.parse_args()

    annotate_corpus_stanza(args.plain, args.ana)
