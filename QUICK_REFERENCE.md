# ParlaMint-AL Quick Reference Card

**For Students: Essential Commands & Concepts**

---

## Quick Start

```bash
# Process everything (recommended)
python3 run_pipeline.py

# Crawl fresh PDFs first, then process
python3 run_pipeline.py --crawl --limit 10
```

---

## Pipeline Steps

| Step | Module | Input | Output | What It Does |
|------|--------|-------|--------|--------------|
| **1. Crawl** | `crawl_pdfs_selenium.py` | parlament.al website | `pdf_urls.json` | Collects PDF URLs |
| **2. Download** | `crawl.py` | `pdf_urls.json` | `pdfs/` | Downloads PDFs |
| **3. Extract** | `crawl.py` (pdfminer) | `pdfs/` | `raw_txt/` | Extracts text from PDFs |
| **4. Clean** | `extract.py` | `raw_txt/` | `texts/` | Removes noise, fixes OCR errors |
| **5. Segment** | `segment.py` | `texts/` | utterances | Identifies speakers |
| **6. Build TEI** | `tei.py` | utterances + metadata | `out/plain/*.xml` | Creates TEI XML |

---

## Key Functions

### 1. Crawling
```python
# src/crawl_pdfs_selenium.py
crawl_pdf_urls(limit=10)
  → Returns: List of PDF URLs
  → Saves: pdf_urls.json
```

### 2. Text Extraction
```python
# src/crawl.py
crawl_urls(urls, pdf_out="pdfs", txt_out="raw_txt")
  → Downloads PDFs
  → Extracts text with pdfminer.six
  → Saves raw text files
```

### 3. Cleaning
```python
# src/extract.py
clean_text(raw_txt)
  → Removes page numbers
  → Fixes OCR errors (é→ë, ¢→ç, gë→që)
  → Returns: cleaned text

extract_header_block(txt)
  → Extracts: date, time, chair, agenda, eventType
  → Returns: metadata dict
```

### 4. Segmentation
```python
# src/segment.py
segment_by_speakers(clean_txt)
  → Finds speaker cues: "Name Surname – text"
  → Groups paragraphs by speaker
  → Returns: {"utterances": [...]}
```

### 5. TEI Generation
```python
# src/tei.py
write_plain_day(session, speakers_idx, out_path, ...)
  → Creates TEI XML structure
  → Adds metadata to header
  → Writes utterances as <u> elements
  → Saves: out/plain/ParlaMint-AL_YYYY-MM-DD.xml
```

---

## Directory Structure

```
Parlamint-al/
├── pdf_urls.json          # Crawled URLs
├── pdfs/                  # Downloaded PDFs
├── raw_txt/               # Raw extracted text
├── texts/                 # Cleaned text
└── out/plain/             # TEI XML files
```

---

## Important Patterns

### Speaker Cue Pattern
```regex
[A-ZÇË][\w]+ [A-ZÇË][\w]+ [–—-] text...
```
**Examples:**
- `Erion Braçe – Faleminderit, zonja Kryetare.`
- `Lindita Nikolla – Ju lutem, vazhdoni.`

### Date Pattern
```regex
më (\d{1,2})\.(\d{1,2})\.(\d{4}) ora (\d{1,2}:\d{2})
```
**Example:** `më 17.10.2025 ora 10:00`

---

## Common Issues & Solutions

| Problem | Solution |
|---------|----------|
| Pipeline only processes 4 files | Use `--clean_from raw_txt` flag |
| No TEI XML generated | Check that `texts/` has cleaned files |
| Speaker not recognized | Check speaker cue format (Name Surname – text) |
| Wrong date in XML | Check date format in source PDF |
| Empty text files | PDF might be scanned (needs OCR) |

---

## Testing Your Understanding

1. **Trace a PDF**: Pick one PDF and follow it through all 6 steps
2. **Find speaker cues**: Open a `texts/` file and identify 3 speaker cues
3. **Check metadata**: Open a TEI XML file and find the date, chair, and event type
4. **Count utterances**: How many `<u>` elements in one XML file?
5. **Modify cleaner**: Add a new OCR fix pattern to `extract.py`

---

## Key Concepts

- **Normalization**: Cleaning and standardizing text
- **Segmentation**: Splitting text by speakers
- **Utterance**: Everything one speaker says before another speaks
- **TEI**: Text Encoding Initiative (XML standard for texts)
- **Metadata**: Structured information (date, time, participants)

---

## Advanced Commands

```bash
# Run individual steps
python3 src/crawl_pdfs_selenium.py --limit 10
python3 -m src.crawl --urls pdf_urls.json
python3 -m src.extract
python3 -m src.pipeline --out out

# Process with custom directories
python3 -m src.pipeline --clean_from my_raw_txt --inbox my_texts --out my_output

# Debug mode (see what's happening)
python3 -m src.pipeline --clean_from raw_txt --out out 2>&1 | tee pipeline.log
```

---

## Resources

- **Full Guide**: `PIPELINE_GUIDE.md`
- **Source Code**: `src/` directory
- **Examples**: `out/plain/` (generated TEI files)
- **ParlaMint Standard**: https://clarin-eric.github.io/ParlaMint/

---

**Quick Help**

```bash
# Get help for any module
python3 run_pipeline.py --help
python3 -m src.pipeline --help
python3 src/crawl_pdfs_selenium.py --help
```
