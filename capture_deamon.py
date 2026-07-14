import time
import os
import re
from datetime import datetime, timedelta
import numpy as np
import mss
import pytesseract
from PIL import Image
import imagehash
import ollama
import pygetwindow as gw

from db import init_db, save_capture, get_blocked_apps, get_captures_older_than, archive_capture

# ---- CONFIG ----
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SCREENSHOT_DIR = "screenshots"
CAPTURE_INTERVAL_SECONDS = 10
MIN_TEXT_LENGTH = 20
HASH_DIFF_THRESHOLD = 5
EMBED_MODEL = "nomic-embed-text"
ARCHIVE_AFTER_HOURS = 2          # screenshots older than this get archived to JSON + PNG deleted
CLEANUP_EVERY_N_CYCLES = 30      # run the cleanup check roughly every ~5 minutes (30 x 10s)

os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def clean_ocr_text(text: str) -> str:
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r' {2,}', ' ', text)
    lines = text.split('\n')
    clean_lines = [line for line in lines if len(re.sub(r'[^a-zA-Z0-9]', '', line)) > 3]
    return '\n'.join(clean_lines).strip()


def get_embedding(text: str):
    response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return np.array(response["embedding"])


def get_active_app_name() -> str:
    try:
        active_window = gw.getActiveWindow()
        return active_window.title if active_window and active_window.title else "Unknown"
    except Exception:
        return "Unknown"


def is_blocked(app_name: str) -> bool:
    blocked_list = get_blocked_apps()
    return any(blocked.lower() in app_name.lower() for blocked in blocked_list)


def run_storage_cleanup():
    """Archive screenshots older than ARCHIVE_AFTER_HOURS: delete PNG, store JSON text record."""
    cutoff = (datetime.now() - timedelta(hours=ARCHIVE_AFTER_HOURS)).strftime("%Y-%m-%d %H:%M:%S")
    old_captures = get_captures_older_than(cutoff)

    if not old_captures:
        return

    archived_count = 0
    for capture_id, timestamp, app_name, text, screenshot_path in old_captures:
        try:
            if screenshot_path and os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            archive_capture(capture_id, timestamp, app_name, text)
            archived_count += 1
        except Exception as e:
            print(f"Error archiving capture {capture_id}: {e}")

    if archived_count:
        print(f"Storage cleanup: archived {archived_count} screenshot(s) older than {ARCHIVE_AFTER_HOURS}h to JSON.")


def run_capture_loop():
    init_db()
    last_hash = None
    cycle_count = 0
    print("OmniRecall capture daemon started. Press Ctrl+C to stop.")

    with mss.mss() as sct:
        monitor = sct.monitors[1]

        while True:
            try:
                cycle_count += 1

                app_name = get_active_app_name()

                if is_blocked(app_name):
                    print(f"Skipped capture — blocked app detected ({app_name})")
                else:
                    sct_img = sct.grab(monitor)
                    img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

                    current_hash = imagehash.average_hash(img)

                    if last_hash is None or (current_hash - last_hash) >= HASH_DIFF_THRESHOLD:
                        last_hash = current_hash

                        text = pytesseract.image_to_string(img).strip()
                        text = clean_ocr_text(text)

                        if len(text) >= MIN_TEXT_LENGTH:
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            filename = os.path.join(SCREENSHOT_DIR, f"{timestamp.replace(':', '-')}.png")
                            img.save(filename)

                            embedding = get_embedding(text)
                            save_capture(timestamp, app_name, text, filename, embedding)

                            print(f"[{timestamp}] ({app_name}) Captured and indexed ({len(text)} chars)")

                if cycle_count % CLEANUP_EVERY_N_CYCLES == 0:
                    run_storage_cleanup()

            except Exception as e:
                print(f"Error during capture: {e}")

            time.sleep(CAPTURE_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_capture_loop()
