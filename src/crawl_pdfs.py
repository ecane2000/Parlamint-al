
import json
import time
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_FILE = Path("pdf_urls.json")

def text_match(element, text):
    return text.lower() in element.inner_text().lower()

def run(limit=None):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        print("Navigating to https://www.parlament.al/procesverbale ...")
        page.goto("https://www.parlament.al/procesverbale", timeout=60000)
        
        # Wait for the "Struktura" dropdown or similar to load
        # Based on subagent, there is a dropdown. Let's try to find "Seanca Plenare"
        # If we can't find it easily, we might just crawl whatever is default or loop options.
        # But usually these sites default to nothing or "All".
        # Let's try to select "Seanca Plenare" if possible.
        
        # We need to wait for content.
        try:
            # Try to interact with the structure filter if simple list isn't there
            # usage: page.locator(".ant-select").click() ...
            # For now, let's assume the page loads *some* list or we need to click "Kërko" (Search).
            
            # Wait for at least one card or the spinner to finish
            page.wait_for_selector(".act-card-wrapper", timeout=10000)
        except:
            print("Content didn't load immediately, trying to select structure...")
            # Try clicking dropdown
            # This is speculative without live DOM, but robust enough to try standard selectors
            pass

        collected_pdfs = []
        page_num = 1
        
        while True:
            print(f"Processing page {page_num}...")
            
            # Get all download buttons
            # Selector from subagent: .dynamic-button.view-act inside .act-card-wrapper
            card_wrappers = page.query_selector_all(".act-card-wrapper")
            
            if not card_wrappers:
                print("No cards found on this page.")
                break
                
            print(f"Found {len(card_wrappers)} documents on page {page_num}.")
            
            for i, card in enumerate(card_wrappers):
                if limit and len(collected_pdfs) >= limit:
                    break
                    
                # Extract Title
                try:
                    title_el = card.query_selector("h5")
                    title = title_el.inner_text().strip() if title_el else "Unknown Title"
                    
                    # We might want to filter for "Procesverbal" if mixed content?
                    # The URL pattern in user prompt was all "Procesverbal..."
                    
                    # Find download button (div with text 'Shkarko' or class .view-act)
                    btn = card.query_selector(".dynamic-button.view-act")
                    
                    if btn:
                        # Setup popup or download listener
                        # It seems it opens a new tab with the PDF (blob url)?
                        # Or triggers a download?
                        
                        # We'll try expecting a popup first (browser view)
                        with context.expect_page() as new_page_info:
                            btn.click()
                            
                        new_page = new_page_info.value
                        new_page.wait_for_load_state()
                        pdf_url = new_page.url
                        
                        print(f"Found PDF: {title} -> {pdf_url}")
                        collected_pdfs.append(pdf_url)
                        
                        new_page.close()
                    else:
                        print(f"No download button for {title}")
                        
                except Exception as e:
                    print(f"Error processing card {i}: {e}")
            
            if limit and len(collected_pdfs) >= limit:
                print(f"Reached limit of {limit} PDFs.")
                break

            # Pagination
            # Look for "Next" button in ant-pagination
            # Usually .ant-pagination-next
            next_btn = page.query_selector(".ant-pagination-next")
            if next_btn and "ant-pagination-disabled" not in next_btn.get_attribute("class"):
                next_btn.click()
                # Wait for loading?
                time.sleep(2) # crude wait for transition
                page.wait_for_selector(".act-card-wrapper")
                page_num += 1
            else:
                print("No next page or disabled.")
                break

        browser.close()
        
        # Save results
        with open(OUTPUT_FILE, "w") as f:
            json.dump(collected_pdfs, f, indent=2)
        
        print(f"Saved {len(collected_pdfs)} URLs to {OUTPUT_FILE}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="Limit number of PDFs", default=None)
    args = parser.parse_args()
    run(limit=args.limit)
