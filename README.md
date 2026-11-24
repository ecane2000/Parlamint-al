# ParlaMint‑AL Pilot Stack (Python)

End‑to‑end pipeline for a tiny Albanian Parliament corpus:
- Crawl given PDF URLs
- Extract text
- Create ParlaMint‑compatible TEI (plain) + optional .ana (UD token/lemma/pos/deprel)

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -c "import stanza; stanza.download('sq')"

# Fetch PDFs into ./inbox and build TEI (plain + .ana samples)
make crawl
make build-ana    # or: python -m src.pipeline --out out --with-ana
```

> Note: this project requires `pdfminer.six` for PDF extraction. Do not install the legacy `pdfminer` package, as it conflicts with the current dependency.

Outputs go to `out/TEI/plain/YYYY` and (if enabled) `out/TEI/ana/YYYY`, grouped by year and referenced from their master corpus files. Plain TEI XML files are written with two-space indentation for readability.
