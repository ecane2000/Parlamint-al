#!/usr/bin/env python3
"""
Automated PDF URL crawler for parlament.al using Selenium.
Collects PDF URLs from the parliament website and saves to pdf_urls.json.

Install dependencies:
    pip install selenium webdriver-manager
"""
import json
import sys
import time
import argparse
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError as e:
    print(f"Error: Missing required package: {e}", file=sys.stderr)
    print("Install with: pip install selenium webdriver-manager", file=sys.stderr)
    sys.exit(1)

OUTPUT_FILE = Path("pdf_urls.json")
BASE_URL = "https://www.parlament.al/procesverbale"

def setup_driver(headless=True):
    """Setup Chrome driver with appropriate options."""
    options = Options()
    if headless:
        options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver

def crawl_pdf_urls(limit=10, headless=True):
    """
    Crawl the parliament website to collect PDF URLs.
    
    Args:
        limit: Maximum number of PDFs to collect
        headless: Run browser in headless mode
    
    Returns:
        List of PDF URLs
    """
    collected_urls = []
    driver = None
    
    try:
        print(f"Setting up browser (headless={headless})...", file=sys.stderr)
        driver = setup_driver(headless=headless)
        
        print(f"Navigating to {BASE_URL}...", file=sys.stderr)
        driver.get(BASE_URL)
        
        # Wait for page to load
        print("Waiting for content to load...", file=sys.stderr)
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "act-card-wrapper")))
        
        # Scroll to load more content
        print("Scrolling to load content...", file=sys.stderr)
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 1000);")
            time.sleep(0.5)
        
        # Find all document cards
        cards = driver.find_elements(By.CLASS_NAME, "act-card-wrapper")
        print(f"Found {len(cards)} document cards", file=sys.stderr)
        
        # Get the main window handle
        main_window = driver.current_window_handle
        
        for i, card in enumerate(cards):
            if len(collected_urls) >= limit:
                break
            
            try:
                # Find download button
                download_btn = card.find_element(By.CSS_SELECTOR, ".dynamic-button.view-act")
                
                # Get document title
                try:
                    title_el = card.find_element(By.TAG_NAME, "h5")
                    title = title_el.text.strip()[:50]
                except:
                    title = f"Document {i+1}"
                
                # Click download button
                download_btn.click()
                time.sleep(1)
                
                # Switch to new window
                windows = driver.window_handles
                if len(windows) > 1:
                    driver.switch_to.window(windows[-1])
                    
                    # Get PDF URL
                    pdf_url = driver.current_url
                    
                    # Verify it's a blob storage URL
                    if 'kuvendiwebfiles.blob.core.windows.net' in pdf_url and pdf_url not in collected_urls:
                        collected_urls.append(pdf_url)
                        print(f"[{len(collected_urls)}/{limit}] {title}...", file=sys.stderr)
                    
                    # Close PDF window
                    driver.close()
                    driver.switch_to.window(main_window)
                    time.sleep(0.3)
                
            except Exception as e:
                print(f"Error processing card {i}: {e}", file=sys.stderr)
                # Make sure we're back on main window
                try:
                    driver.switch_to.window(main_window)
                except:
                    pass
                continue
        
    except Exception as e:
        print(f"Error during crawling: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()
    
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
    
    args = parser.parse_args()
    
    print(f"Crawling up to {args.limit} PDFs from {BASE_URL}", file=sys.stderr)
    print("This may take a minute...\n", file=sys.stderr)
    
    urls = crawl_pdf_urls(limit=args.limit, headless=args.headless)
    
    if urls:
        save_urls(urls, Path(args.output))
        print(f"\n✓ Success! Collected {len(urls)} URLs", file=sys.stderr)
        return 0
    else:
        print("\n✗ Warning: No URLs were collected", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
