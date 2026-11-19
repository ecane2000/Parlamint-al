#!/usr/bin/env python3
"""
Automated PDF URL crawler for parlament.al.
Collects fresh PDF URLs from the parliament portal/API and saves to pdf_urls.json.
"""
import json
import sys
import argparse
from pathlib import Path
from typing import List, Optional

import requests

OUTPUT_FILE = Path("pdf_urls.json")
BASE_URL = "https://www.parlament.al/procesverbale"
API_URL = "https://kuvendiapi.azurewebsites.net/api/dokumentet"


def crawl_pdf_urls_api(limit: int = 100, structure: Optional[str] = None) -> List[str]:
    """
    Fetch PDF URLs directly from the official Kuvendi backend REST API.
    
    Args:
        limit: Maximum number of PDFs to collect
        structure: Optional structural filter (e.g. 'Seancë plenare')
    
    Returns:
        List of PDF URLs
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
    }
    # tipdokumentid cc439e41-586a-45b0-a005-a505f6a141a4 corresponds to 'Procesverbale'
    filter_expr = "tipdokumentid eq cc439e41-586a-45b0-a005-a505f6a141a4"
    if structure:
        filter_expr += f" and strukturedokumentet/any(s: s/strukture/emer eq '{structure}')"

    params = {
        "$orderby": "datekrijimi desc",
        "$filter": filter_expr,
        "$expand": "strukturedokumentet($expand=strukture)",
        "$top": limit,
        "$skip": 0,
    }

    try:
        r = requests.get(API_URL, params=params, headers=headers, timeout=25)
        r.raise_for_status()
        docs = r.json()
        urls: List[str] = []
        for d in docs:
            u = d.get("Url")
            fn = d.get("FileName", "Document")
            if u and "blob.core.windows.net" in u:
                urls.append(u)
                print(f"  [{len(urls)}/{limit}] Found: {fn}", file=sys.stderr)
            if len(urls) >= limit:
                break
        return urls
    except Exception as e:
        print(f"[WARN] Direct API query failed: {e}", file=sys.stderr)
        return []


def crawl_pdf_urls_playwright(limit: int = 100, headless: bool = True, timeout: int = 30000) -> List[str]:
    """Fallback crawler using Playwright headless browser."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[WARN] Playwright is not installed for browser fallback.", file=sys.stderr)
        return []

    collected_urls: List[str] = []
    print(f"Starting Playwright crawler (limit={limit}, headless={headless})...", file=sys.stderr)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )
        page = context.new_page()
        page.set_default_timeout(timeout)

        try:
            page.goto(BASE_URL, wait_until="domcontentloaded")
            for _ in range(3):
                page.evaluate("window.scrollBy(0, 1000)")
                page.wait_for_timeout(500)

            cards = page.query_selector_all(".act-card-wrapper")
            for i, card in enumerate(cards):
                if len(collected_urls) >= limit:
                    break
                try:
                    btn = card.query_selector(".dynamic-button.view-act")
                    if not btn:
                        continue
                    with context.expect_page(timeout=5000) as new_page_info:
                        btn.click()
                    new_page = new_page_info.value
                    new_page.wait_for_load_state("domcontentloaded", timeout=5000)
                    pdf_url = new_page.url
                    if "kuvendiwebfiles.blob.core.windows.net" in pdf_url and pdf_url not in collected_urls:
                        collected_urls.append(pdf_url)
                        print(f"  [{len(collected_urls)}/{limit}] Collected: {pdf_url.split('/')[-1]}", file=sys.stderr)
                    new_page.close()
                except Exception:
                    continue
        except Exception as e:
            print(f"[ERROR] Playwright crawler error: {e}", file=sys.stderr)
        finally:
            browser.close()

    return collected_urls


def crawl_pdf_urls(limit: int = 100, headless: bool = True, timeout: int = 30000, structure: Optional[str] = None) -> List[str]:
    """
    Crawl the parliament website/API to collect PDF URLs.
    
    Args:
        limit: Maximum number of PDFs to collect
        headless: Run browser in headless mode (if fallback used)
        timeout: Timeout in milliseconds
        structure: Optional structural filter
    
    Returns:
        List of PDF URLs
    """
    print(f"[*] Crawling up to {limit} PDF URLs from {BASE_URL}...", file=sys.stderr)
    urls = crawl_pdf_urls_api(limit=limit, structure=structure)
    if urls:
        return urls

    print("[*] Direct API unavailable, falling back to browser crawler...", file=sys.stderr)
    return crawl_pdf_urls_playwright(limit=limit, headless=headless, timeout=timeout)


def save_urls(urls: List[str], output_file: Path = OUTPUT_FILE) -> None:
    """Save URLs to JSON file."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(urls, f, indent=2, ensure_ascii=False)
    print(f"[OK] Saved {len(urls)} URLs to {output_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Crawl parliament PDFs and save URLs")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of PDFs to collect")
    parser.add_argument("--headless", action="store_true", default=True, help="Run in headless mode")
    parser.add_argument("--no-headless", dest="headless", action="store_false", help="Run with visible browser")
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE), help="Output JSON file")
    parser.add_argument("--timeout", type=int, default=30000, help="Timeout in milliseconds")
    parser.add_argument("--structure", type=str, default=None, help="Filter by structure (e.g. 'Seancë plenare')")

    args = parser.parse_args()

    urls = crawl_pdf_urls(
        limit=args.limit,
        headless=args.headless,
        timeout=args.timeout,
        structure=args.structure,
    )

    if urls:
        save_urls(urls, Path(args.output))
        print(f"\n[SUCCESS] Collected {len(urls)} URLs", file=sys.stderr)
        return 0
    else:
        print("\n[WARN] No URLs were collected", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
