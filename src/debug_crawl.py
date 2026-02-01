print("Hello from debug script", flush=True)
import sys
print(f"Python: {sys.version}", flush=True)
try:
    print("Importing playwright...", flush=True)
    from playwright.sync_api import sync_playwright
    print("Imported playwright successfully.", flush=True)
except Exception as e:
    print(f"Import failed: {e}", flush=True)
except ImportError as e:
    print(f"ImportError: {e}", flush=True)

print("End of debug script", flush=True)
