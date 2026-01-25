<<<<<<< HEAD
# Parlamint-al
=======
# ParlaMint‑AL Pilot Stack (Python)

End‑to‑end pipeline for a tiny Albanian Parliament corpus:
- Crawl given PDF URLs
- Extract text
- Create ParlaMint‑compatible TEI (plain) + optional .ana (UD token/lemma/pos/deprel)
- (Optional) Hook for NER using transformers

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -c "import stanza; stanza.download('sq')"

# Fetch PDFs into ./inbox and build TEI (plain + .ana samples)
make crawl
make build-ana    # or: python -m parlamint_al.pipeline --out out --with-ana
```
Outputs go to `out/TEI/plain` and (if enabled) `out/TEI/ana`.
>>>>>>> dd8156e0 (Initial commit: ParlaMint-AL pilot stack)
>>>>>>>
>>>>>>> nnn
