#!/usr/bin/env python3
"""
Automated PDF URL crawler for parlament.al using Playwright.
Collects PDF URLs from the parliament website and saves to pdf_urls.json.
"""
import json
import sys
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

OUTPUT_FILE = Path("pdf_urls.json")
BASE_URL = "https://www.parlament.al/procesverbale"

def crawl_pdf_urls(limit=10, headless=True, timeout=30000):
    """
    Crawl the parliament website to collect PDF URLs.
    
    Args:
        limit: Maximum number of PDFs to collect
        headless: Run browser in headless mode
        timeout: Timeout in milliseconds for page operations
    
    Returns:
        List of PDF URLs
    """
    collected_urls = []
    
    print(f"Starting crawler (limit={limit}, headless={headless})...", file=sys.stderr)
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        # Set default timeout
        page.set_default_timeout(timeout)
        
        try:
            # Navigate to the page
            print(f"Navigating to {BASE_URL}...", file=sys.stderr)
            page.goto(BASE_URL, wait_until='domcontentloaded')
            
            # Wait for content to load
            print("Waiting for content to load...", file=sys.stderr)
            try:
                page.wait_for_selector(".act-card-wrapper", timeout=10000)
            except PlaywrightTimeout:
                print("Warning: Content took longer to load, continuing anyway...", file=sys.stderr)
            
            # Scroll to load more content
            for _ in range(3):
                page.evaluate("window.scrollBy(0, 1000)")
                page.wait_for_timeout(500)
            
            # Find all download buttons
            print("Finding download buttons...", file=sys.stderr)
            cards = page.query_selector_all(".act-card-wrapper")
            print(f"Found {len(cards)} document cards", file=sys.stderr)
            
            for i, card in enumerate(cards):
                if len(collected_urls) >= limit:
                    break
                
                try:
                    # Find the download button in this card
                    download_btn = card.query_selector(".dynamic-button.view-act")
                    if not download_btn:
                        continue
                    
                    # Get document title for logging
                    title_el = card.query_selector("h5")
                    title = title_el.inner_text().strip() if title_el else f"Document {i+1}"
                    
                    # Click the download button and wait for new page
                    with context.expect_page(timeout=5000) as new_page_info:
                        download_btn.click()
                    
                    new_page = new_page_info.value
                    new_page.wait_for_load_state('domcontentloaded', timeout=5000)
                    
                    # Get the PDF URL
                    pdf_url = new_page.url
                    
                    # Verify it's a blob storage URL
                    if 'kuvendiwebfiles.blob.core.windows.net' in pdf_url:
                        collected_urls.append(pdf_url)
                        print(f"[{len(collected_urls)}/{limit}] {title[:50]}...", file=sys.stderr)
                    else:
                        print(f"Skipping non-blob URL: {pdf_url}", file=sys.stderr)
                    
                    # Close the PDF page
                    new_page.close()
                    
                    # Small delay to avoid overwhelming the server
                    page.wait_for_timeout(300)
                    
                except Exception as e:
                    print(f"Error processing card {i}: {e}", file=sys.stderr)
                    continue
            
        except Exception as e:
            print(f"Error during crawling: {e}", file=sys.stderr)
        finally:
            browser.close()
    
    return collected_urls

def save_urls(urls, output_file=OUTPUT_FILE):
    """Save URLs to JSON file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(urls, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(urls)} URLs to {output_file}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description="Crawl parliament PDFs and save URLs")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of PDFs to collect")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    parser.add_argument("--no-headless", dest="headless", action="store_false", help="Run with visible browser")
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE), help="Output JSON file")
    parser.add_argument("--timeout", type=int, default=30000, help="Timeout in milliseconds")
    
    args = parser.parse_args()
    
    print(f"Crawling up to {args.limit} PDFs from {BASE_URL}", file=sys.stderr)
    
    urls = crawl_pdf_urls(
        limit=args.limit,
        headless=args.headless,
        timeout=args.timeout
    )
    
    if urls:
        save_urls(urls, Path(args.output))
        print(f"\nSuccess! Collected {len(urls)} URLs", file=sys.stderr)
        return 0
    else:
        print("\nWarning: No URLs were collected", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
