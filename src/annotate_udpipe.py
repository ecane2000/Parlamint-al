# -*- coding: utf-8 -*-
"""
UDPipe linguistic annotation layer for ParlaMint-AL:
Transforms plain TEI files (out/TEI/plain/*.xml) into linguistically annotated
TEI.ana files (out/TEI/ana/*.ana.xml) using UDPipe.
"""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional
import xml.etree.ElementTree as ET

from .config import UDPIPE_MODEL_PATH
from .tei import qname, TEI_NS, XML_NS

try:
    from ufal.udpipe import Model, Pipeline, ProcessingError
except ImportError:
    Model = None
    Pipeline = None


def load_udpipe_model(model_path: Path | str):
    """Load a pretrained UDPipe model."""
    if Model is None:
        raise RuntimeError("ufal.udpipe is not installed. Install with `pip install ufal.udpipe`.")

    p = Path(model_path)
    if not p.exists():
        raise FileNotFoundError(
            f"UDPipe model file not found at {p}. "
            f"Please download an Albanian UDPipe model (e.g. sq-ud-2.5.udpipe) into {model_path}."
        )

    model = Model.load(str(p))
    if not model:
        raise RuntimeError(f"Cannot load UDPipe model from {p}")

    pipeline = Pipeline(model, "tokenize", Pipeline.DEFAULT, Pipeline.DEFAULT, "conllu")
    return pipeline


def parse_conllu(conllu: str) -> List[List[Dict[str, str]]]:
    """Parse CoNLL-U format string into a list of sentences of token dictionaries."""
    sentences: List[List[Dict[str, str]]] = []
    current_sent: List[Dict[str, str]] = []

    for line in conllu.splitlines():
        line = line.strip()
        if not line:
            if current_sent:
                sentences.append(current_sent)
                current_sent = []
            continue
        if line.startswith("#"):
            continue

        parts = line.split("\t")
        if len(parts) >= 10:
            token_id = parts[0]
            # Skip multi-word token lines like 1-2
            if "-" in token_id or "." in token_id:
                continue

            current_sent.append({
                "id": parts[0],
                "form": parts[1],
                "lemma": parts[2] if parts[2] != "_" else "",
                "upos": parts[3] if parts[3] != "_" else "",
                "xpos": parts[4] if parts[4] != "_" else "",
                "feats": parts[5] if parts[5] != "_" else "",
                "head": parts[6] if parts[6] != "_" else "",
                "deprel": parts[7] if parts[7] != "_" else "",
            })

    if current_sent:
        sentences.append(current_sent)

    return sentences


def annotate_seg_with_udpipe(seg_el: ET.Element, pipeline) -> None:
    """Annotate a <seg> element using UDPipe."""
    text = (seg_el.text or "").strip()
    if not text:
        return

    error = ProcessingError()
    processed = pipeline.process(text, error)
    if error.occurred():
        print(f"[WARN] UDPipe processing error: {error.message}")
        return

    sentences = parse_conllu(processed)

    xml_id = seg_el.get(f"{{{XML_NS}}}id")
    seg_el.clear()
    if xml_id:
        seg_el.set(f"{{{XML_NS}}}id", xml_id)

    for sent_idx, sent in enumerate(sentences, start=1):
        s_attrs = {}
        if xml_id:
            s_attrs[f"{{{XML_NS}}}id"] = f"{xml_id}.s{sent_idx}"
        s_el = ET.SubElement(seg_el, qname("s"), s_attrs)

        for w in sent:
            tag = "pc" if w["upos"] == "PUNCT" else "w"
            token_el = ET.SubElement(s_el, qname(tag))
            token_el.text = w["form"]

            if w["lemma"]:
                token_el.set("lemma", w["lemma"])
            if w["upos"]:
                token_el.set("pos", w["upos"])
            if w["feats"]:
                token_el.set("msd", w["feats"])
            if w["deprel"]:
                token_el.set("dep", w["deprel"])
            if w["head"]:
                token_el.set("head", w["head"])


def annotate_file_udpipe(src: Path | str, dst: Path | str, pipeline) -> None:
    """Annotate a single plain TEI file using UDPipe and write to dst."""
    tree = ET.parse(src)
    root = tree.getroot()

    orig_id = root.get(f"{{{XML_NS}}}id", "")
    if orig_id and not orig_id.endswith(".ana"):
        root.set(f"{{{XML_NS}}}id", f"{orig_id}.ana")

    current_ana = root.get("ana", "")
    if "#ud-sq-udpipe" not in current_ana:
        root.set("ana", f"{current_ana} #ud-sq-udpipe".strip())

    for seg in root.findall(f".//{{{TEI_NS}}}seg"):
        annotate_seg_with_udpipe(seg, pipeline)

    dst_path = Path(dst)
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(dst_path, encoding="utf-8", xml_declaration=True)


def annotate_corpus_udpipe(
    plain_dir: Path | str,
    ana_dir: Path | str,
    model_path: Optional[Path | str] = None,
) -> None:
    """Annotate all plain TEI files in plain_dir to ana_dir using UDPipe."""
    mpath = model_path or UDPIPE_MODEL_PATH
    pipeline = load_udpipe_model(mpath)

    plain_p = Path(plain_dir)
    ana_p = Path(ana_dir)
    ana_p.mkdir(parents=True, exist_ok=True)

    for src in sorted(plain_p.glob("*.xml")):
        target_name = src.stem + ".ana.xml"
        dst = ana_p / target_name
        annotate_file_udpipe(src, dst, pipeline)
        print(f"[OK] UDPipe annotated: {src.name} -> {target_name}")


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Annotate ParlaMint-AL plain TEI files using UDPipe")
    ap.add_argument("--plain", default="out/TEI/plain", help="Directory of plain TEI files")
    ap.add_argument("--ana", default="out/TEI/ana", help="Directory for output .ana.xml files")
    ap.add_argument("--model", default=UDPIPE_MODEL_PATH, help="Path to .udpipe model file")
    args = ap.parse_args()

    annotate_corpus_udpipe(args.plain, args.ana, model_path=args.model)
