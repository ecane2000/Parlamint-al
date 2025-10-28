from typing import List, Dict
import stanza

_nlp = None

def nlp() -> stanza.Pipeline:
    global _nlp
    if _nlp is None:
        _nlp = stanza.Pipeline('sq', processors='tokenize,pos,lemma,depparse', tokenize_no_ssplit=False, use_gpu=False)
    return _nlp

def ud_doc(text: str) -> List[List[Dict]]:
    doc = nlp()(text)
    sents = []
    for sent in doc.sentences:
        sent_items = []
        for word in sent.words:
            sent_items.append({
                'text': word.text,
                'lemma': getattr(word, 'lemma', None),
                'upos': getattr(word, 'upos', None),
                'feats': getattr(word, 'feats', None),
                'deprel': getattr(word, 'deprel', None),
            })
        sents.append(sent_items)
    return sents
