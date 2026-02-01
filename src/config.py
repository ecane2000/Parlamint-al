
import json
from pathlib import Path

# Try to load scraped URLs from pdf_urls.json in the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PDF_URLS_FILE = PROJECT_ROOT / "pdf_urls.json"

if PDF_URLS_FILE.exists():
    with open(PDF_URLS_FILE, "r", encoding="utf-8") as f:
        PDF_URLS = json.load(f)
else:
    # Fallback to initial seeds if crawl hasn't run
    PDF_URLS = [
        "https://kuvendiwebfiles.blob.core.windows.net/webfiles/202510241107180185Procesverbal%2C%20dat%C3%AB%2017.10.2025.pdf",
        "https://kuvendiwebfiles.blob.core.windows.net/webfiles/202512111507528093Procesverbal%20dat%C3%AB%204.12.2025.pdf",
        "https://kuvendiwebfiles.blob.core.windows.net/webfiles/202512151346506127Procesverbal-KKIE-19.11.2025.pdf",
        "https://kuvendiwebfiles.blob.core.windows.net/webfiles/202512100754029370Procesverbal%20KEPF%20-%2023.10.25.pdf",
    ]

# Optional defaults used elsewhere
PARLIAMENT_NAME = "Kuvendi i Shqipërisë"
CITY = "Tiranë"
LICENSE_URL = "https://creativecommons.org/licenses/by/4.0/"


# --- UDPipe fallback model path (place the .udpipe file here) -------------
# Example suggestion:
#   models/udpipe/albanian.udpipe
UDPIPE_MODEL_PATH = "models/udpipe/albanian.udpipe"