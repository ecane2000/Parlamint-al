#!/usr/bin/env python3
"""
Simple manual PDF URL collector for parlament.al
Since the site is dynamic (React), this script provides instructions
for manually collecting URLs from the browser's Network tab.
"""
import json
from pathlib import Path

def create_sample_urls():
    """Create a sample pdf_urls.json with 10 URLs for testing."""
    # These are real URLs from the parlament.al site
    # You can expand this list by:
    # 1. Opening https://www.parlament.al/procesverbale in your browser
    # 2. Opening DevTools (F12) -> Network tab
    # 3. Filtering by "procesverbal" or ".pdf"
    # 4. Clicking through pages and copying the blob URLs
    
    sample_urls = [
        "https://kuvendiwebfiles.blob.core.windows.net/webfiles/202510241107180185Procesverbal%2C%20dat%C3%AB%2017.10.2025.pdf",
        "https://kuvendiwebfiles.blob.core.windows.net/webfiles/202512111507528093Procesverbal%20dat%C3%AB%204.12.2025.pdf",
        "https://kuvendiwebfiles.blob.core.windows.net/webfiles/202512151346506127Procesverbal-KKIE-19.11.2025.pdf",
        "https://kuvendiwebfiles.blob.core.windows.net/webfiles/202512100754029370Procesverbal%20KEPF%20-%2023.10.25.pdf",
        # Add more URLs here manually from the browser
        # Example pattern:
        # "https://kuvendiwebfiles.blob.core.windows.net/webfiles/YYYYMMDDHHMMSSNNNN...pdf",
    ]
    
    output_file = Path("pdf_urls.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(sample_urls, f, indent=2)
    
    print(f"Created {output_file} with {len(sample_urls)} URLs")
    print("\nTo add more URLs:")
    print("1. Visit https://www.parlament.al/procesverbale")
    print("2. Open Browser DevTools (F12) -> Network tab")
    print("3. Click 'Shkarko' on documents")
    print("4. Copy the blob.core.windows.net URLs")
    print("5. Add them to pdf_urls.json")

if __name__ == "__main__":
    create_sample_urls()
