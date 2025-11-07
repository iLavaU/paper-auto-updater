import os
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import traceback

# --- Config from .env ---
WATCH_FOLDER = Path(os.getenv("WATCH_FOLDER", "/papers/new"))
PROCESSED_FOLDER = Path(os.getenv("PROCESSED_FOLDER", "/papers/processed"))
GROBID_URL = os.getenv("GROBID_URL", "http://grobid:8070/api/processHeaderDocument")
ILIBRARIAN_UPLOAD_URL = os.getenv("ILIBRARIAN_UPLOAD_URL", "")
INTERVAL_MINUTES = int(os.getenv("INTERVAL_MINUTES", "10"))
ILIBRARIAN_USER = os.getenv("ILIBRARIAN_USER")
ILIBRARIAN_PASS = os.getenv("ILIBRARIAN_PASS")

# --- Setup folders ---
for folder in [WATCH_FOLDER, PROCESSED_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def process_pdf(pdf_path: Path):
    log(f"Processing {pdf_path.name}...")

    # Send to GROBID
    try:
        with open(pdf_path, "rb") as f:
            resp = requests.post(GROBID_URL, files={"input": f}, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        log(f"GROBID request failed for {pdf_path.name}: {e}")
        return

    # Parse XML
    try:
        root = ET.fromstring(resp.text)
        title_el = root.find(".//titleStmt/title")
        title = title_el.text.strip() if title_el is not None and title_el.text else pdf_path.stem
    except Exception as e:
        log(f"XML parse error for {pdf_path.name}: {e}")
        title = pdf_path.stem

    # Upload to I Librarian
    try:
        with open(pdf_path, "rb") as f:
            files = {"file": f}
            data = {"user": ILIBRARIAN_USER, "password": ILIBRARIAN_PASS, "title": title}
            resp = requests.post(ILIBRARIAN_UPLOAD_URL, files=files, data=data, timeout=30)
        resp.raise_for_status()
        log(f"Uploaded successfully → {pdf_path.name}")
        pdf_path.rename(PROCESSED_FOLDER / pdf_path.name)
    except Exception as e:
        log(f"Upload failed for {pdf_path.name}: {e}")

def main():
    log("Starting auto-importer...")
    while True:
        pdf_generator = WATCH_FOLDER.glob("*.pdf")
        pdfs = list(WATCH_FOLDER.glob("*.pdf"))
        if not pdfs or len(pdfs) == 0:
            log(f"No new pdfs in {str(WATCH_FOLDER)}. Sleeping {str(INTERVAL_MINUTES * 60)}")
            time.sleep(INTERVAL_MINUTES * 60)
            continue
        try:
            for pdf in pdf_generator:
                process_pdf(pdf)
        except Exception as e:
            log("Unexpected error in main loop:")
            log(traceback.format_exc())
        finally:
            # Wait before next scan even if an error occurred
            time.sleep(INTERVAL_MINUTES * 60)

if __name__ == "__main__":
    main()
