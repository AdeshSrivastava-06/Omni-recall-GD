import time
import os
import re
from datetime import datetime
import numpy as np
import mss
import pytesseract
from PIL import Image
import imagehash
import ollama
import pygetwindow as gw

from db import init_db, save_capture

# ---- CONFIG ----
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SCREENSHOT_DIR = "screenshots"
CAPTURE_INTERVAL_SECONDS = 10
MIN_TEXT_LENGTH = 15          # skip captures with barely any text
HASH_DIFF_THRESHOLD = 5       # lower = more sensitive to screen changes
EMBED_MODEL = "nomic-embed-text"

# Privacy: any window whose title contains these substrings will NEVER be captured
BLOCKED_APPS = ["1Password", "Bitwarden", "Banking", "Incognito", "Netbanking", "Password"]

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
    return any(blocked.lower() in app_name.lower() for blocked in BLOCKED_APPS)


def run_capture_loop():
    init_db()
    last_hash = None
    print("OmniRecall capture daemon started. Press Ctrl+C to stop.")
    print(f"Privacy blocklist active for: {BLOCKED_APPS}")

    with mss.mss() as sct:
        monitor = sct.monitors[1]  # primary monitor

        while True:
            try:
                app_name = get_active_app_name()

                if is_blocked(app_name):
                    print(f"Skipped capture — blocked app detected ({app_name})")
                    time.sleep(CAPTURE_INTERVAL_SECONDS)
                    continue

                sct_img = sct.grab(monitor)
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

                current_hash = imagehash.average_hash(img)

                if last_hash is not None and (current_hash - last_hash) < HASH_DIFF_THRESHOLD:
                    time.sleep(CAPTURE_INTERVAL_SECONDS)
                    continue

                last_hash = current_hash

                text = pytesseract.image_to_string(img).strip()
                text = clean_ocr_text(text)

                if len(text) < MIN_TEXT_LENGTH:
                    time.sleep(CAPTURE_INTERVAL_SECONDS)
                    continue

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                filename = os.path.join(SCREENSHOT_DIR, f"{timestamp.replace(':', '-')}.png")
                img.save(filename)

                embedding = get_embedding(text)
                save_capture(timestamp, app_name, text, filename, embedding)

                print(f"[{timestamp}] ({app_name}) Captured and indexed ({len(text)} chars)")

            except Exception as e:
                print(f"Error during capture: {e}")

            time.sleep(CAPTURE_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_capture_loop()
