"""
UD annotator with graceful fallback:
  1) Try Stanza (if 'sq' processors exist).
  2) Fallback to UDPipe (ufal.udpipe) using a local .udpipe model.
Returns a unified sentence structure consumable by tei.insert_body_ana:
  List[List[Token]], where Token is dict with:
    form, lemma, upos, feats (string or "_"), head (int), deprel (str)
"""
from typing import List, Dict
from pathlib import Path


try:
    import stanza
    _HAS_STANZA = True
except Exception:
    _HAS_STANZA = False

from .config import UDPIPE_MODEL_PATH

_nlp = None
_udpipe_model = None

def nlp():
    """Try to build a Stanza pipeline; raise if unavailable."""
    if not _HAS_STANZA:
        raise RuntimeError("Stanza not installed")
    global _nlp
    if _nlp is None:
        # This will raise ValueError if 'sq' is unsupported.
        _nlp = stanza.Pipeline('sq',
                               processors='tokenize,pos,lemma,depparse',
                               tokenize_no_ssplit=False, use_gpu=False)
    return _nlp

def _udpipe():
    """Load UDPipe model if present; raise if not found."""
    global _udpipe_model
    if _udpipe_model is not None:
        return _udpipe_model
    try:
        from ufal.udpipe import Model, Pipeline
    except Exception as e:
        raise RuntimeError("UDPipe not installed. Run: pip install ufal.udpipe conllu") from e
    model_path = Path(UDPIPE_MODEL_PATH)
    if not model_path.exists():
        raise FileNotFoundError(f"UDPipe model not found at {model_path}. "
                                "Download an Albanian UD model (.udpipe) and place it there.")
    _udpipe_model = Model.load(str(model_path))
    if _udpipe_model is None:
        raise RuntimeError(f"Failed to load UDPipe model: {model_path}")
    return _udpipe_model

def _annotate_with_udpipe(text: str) -> List[List[Dict]]:
    """Annotate text with UDPipe and return unified token structure."""
    from ufal.udpipe import Pipeline
    from conllu import parse

    model = _udpipe()
    # Tokenize+tag+parse in one go; udpipe output format = conllu
    pipeline = Pipeline(model, "tokenize", "tag", "parse", "conllu")
    conllu_str = pipeline.process(text)
    sentences = parse(conllu_str)

    out: List[List[Dict]] = []
    for sent in sentences:
        toks: List[Dict] = []
        for t in sent:
            if isinstance(t, dict) and "form" in t:
                toks.append({
                    "form": t.get("form", ""),
                    "lemma": t.get("lemma", "_"),
                    "upos": t.get("upostag", "_"),
                    "feats": t.get("feats") if t.get("feats") not in (None, {}) else "_",
                    "head": t.get("head", 0) or 0,
                    "deprel": t.get("deprel", "_"),
                })
        if toks:
            out.append(toks)
    return out

def _annotate_with_stanza(text: str):
    """Annotate with Stanza and convert to unified structure."""
    doc = nlp()(text)
    sents = []
    for s in doc.sentences:
        toks = []
        for w in s.words:
            toks.append({
                "form": w.text,
                "lemma": w.lemma or "_",
                "upos": w.upos or "_",
                "feats": w.feats or "_",
                "head": int(w.head or 0),
                "deprel": w.deprel or "_",
            })
        if toks:
           sents.append(toks)
    return sents

def ud_doc(text: str):
    """
    Return List[List[Token]] with keys: form, lemma, upos, feats, head, deprel.
    Tries Stanza first; on failure, falls back to UDPipe.
    """
    # Try Stanza
    if _HAS_STANZA:
        try:
            return _annotate_with_stanza(text)
        except Exception:
            pass
    # Fallback to UDPipe
    return _annotate_with_udpipe(text)
