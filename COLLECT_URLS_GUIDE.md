# How to Collect Valid PDF URLs

Since some blob storage URLs expire quickly, here's how to manually collect fresh URLs:

## Steps

1. **Open the Parliament website** (you already have it open):
   - https://www.parlament.al/procesverbale

2. **Filter for Plenary Sessions**:
   - In the "Struktura" dropdown, select **"Seanca Plenare"** (Plenary Session)
   - These are the parliamentary debate transcripts you want

3. **Collect URLs**:
   - For each document, click the **"Shkarko"** button
   - A new tab will open with the PDF
   - Copy the URL from the address bar (it will look like: `https://kuvendiwebfiles.blob.core.windows.net/webfiles/...`)
   - Close the PDF tab
   - Paste the URL into `pdf_urls.json`

4. **Update `pdf_urls.json`**:
   ```json
   [
     "https://kuvendiwebfiles.blob.core.windows.net/webfiles/PASTE_URL_HERE.pdf",
     "https://kuvendiwebfiles.blob.core.windows.net/webfiles/PASTE_URL_HERE.pdf",
     ...
   ]
   ```

5. **Run the pipeline**:
   ```bash
   python -m src.pipeline --out out
   ```

## Current Working URLs

These 4 URLs are confirmed to work:
- `https://kuvendiwebfiles.blob.core.windows.net/webfiles/202510241107180185Procesverbal%2C%20dat%C3%AB%2017.10.2025.pdf`
- `https://kuvendiwebfiles.blob.core.windows.net/webfiles/202512111507528093Procesverbal%20dat%C3%AB%204.12.2025.pdf`
- `https://kuvendiwebfiles.blob.core.windows.net/webfiles/202512151346506127Procesverbal-KKIE-19.11.2025.pdf`
- `https://kuvendiwebfiles.blob.core.windows.net/webfiles/202512100754029370Procesverbal%20KEPF%20-%2023.10.25.pdf`

Add 6 more to reach your limit of 10.

## Alternative: Use Browser DevTools

1. Open DevTools (F12)
2. Go to the **Network** tab
3. Filter by "pdf" or "blob"
4. Click "Shkarko" buttons
5. Copy the URLs from the Network tab
