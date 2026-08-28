# -*- coding: utf-8 -*-
"""
Configuration and project settings for ParlaMint-AL.
Owns all paths, constants, licence info, and model paths.
Contains no business logic.
"""
from pathlib import Path
import json

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Corpus / Project Identifiers
PARLIAMENT_NAME = "Kuvendi i Shqipërisë"
COUNTRY_CODE = "AL"
LANGUAGE_CODE = "sq"
CITY = "Tiranë"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"

# Directory Defaults
INBOX_DIR = "inbox"
RAW_DIR = "inbox/raw"
CLEANED_DIR = "inbox/cleaned"
OUT_TEI_DIR = "out/TEI"
PLAIN_DIR = "out/TEI/plain"
ANA_DIR = "out/TEI/ana"
METADATA_DIR = "metadata"

# Absolute Path Constants
PATH_INBOX_RAW = PROJECT_ROOT / RAW_DIR
PATH_INBOX_CLEANED = PROJECT_ROOT / CLEANED_DIR
PATH_OUT_PLAIN = PROJECT_ROOT / PLAIN_DIR
PATH_OUT_ANA = PROJECT_ROOT / ANA_DIR
PATH_METADATA = PROJECT_ROOT / METADATA_DIR

# Metadata CSV Paths
DOCUMENTS_CSV = "metadata/documents.csv"
PERSONS_CSV = "metadata/persons.csv"
AFFILIATIONS_CSV = "metadata/affiliations.csv"
ORGS_CSV = "metadata/orgs.csv"

PATH_DOCUMENTS_CSV = PROJECT_ROOT / DOCUMENTS_CSV
PATH_PERSONS_CSV = PROJECT_ROOT / PERSONS_CSV
PATH_AFFILIATIONS_CSV = PROJECT_ROOT / AFFILIATIONS_CSV
PATH_ORGS_CSV = PROJECT_ROOT / ORGS_CSV

# Models & NLP
UDPIPE_MODEL_PATH = "models/udpipe/albanian.udpipe"
PATH_UDPIPE_MODEL = PROJECT_ROOT / UDPIPE_MODEL_PATH

# URLs Manifest & Seed URLs
PDF_URLS_FILE = PROJECT_ROOT / "pdf_urls.json"
URLS_TXT_FILE = PROJECT_ROOT / "urls.txt"

if PDF_URLS_FILE.exists():
    try:
        with open(PDF_URLS_FILE, "r", encoding="utf-8") as f:
            PDF_URLS = json.load(f)
    except Exception:
        PDF_URLS = []
else:
    PDF_URLS = [
        "https://kuvendiwebfiles.blob.core.windows.net/webfiles/202510241107180185Procesverbal%2C%20dat%C3%AB%2017.10.2025.pdf",
        "https://kuvendiwebfiles.blob.core.windows.net/webfiles/202510281244347130Procesverbal%2C%20dat%C3%AB%2006.10.2025_.pdf",
        "https://kuvendiwebfiles.blob.core.windows.net/webfiles/202510281244562738Procesverbal%2C%20dat%C3%AB%2007.10._2025.pdf",
        "https://kuvendiwebfiles.blob.core.windows.net/webfiles/202510281245171998Procesverbal%2C%20dat%C3%AB%2008.10.2025_.pdf",
        "https://kuvendiwebfiles.blob.core.windows.net/webfiles/202512111507528093Procesverbal%20dat%C3%AB%204.12.2025.pdf",
    ]