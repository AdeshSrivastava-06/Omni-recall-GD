import sqlite3
import numpy as np

DB_PATH = "omnirecall.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS captures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            app_name TEXT NOT NULL,
            text TEXT NOT NULL,
            screenshot_path TEXT NOT NULL,
            embedding BLOB NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_capture(timestamp, app_name, text, screenshot_path, embedding: np.ndarray):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO captures (timestamp, app_name, text, screenshot_path, embedding) VALUES (?, ?, ?, ?, ?)",
        (timestamp, app_name, text, screenshot_path, embedding.astype(np.float32).tobytes())
    )
    conn.commit()
    conn.close()


def get_all_captures():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, timestamp, app_name, text, screenshot_path, embedding FROM captures")
    rows = c.fetchall()
    conn.close()
    return _rows_to_dicts(rows)


def get_captures_in_range(start_timestamp: str, end_timestamp: str):
    """timestamps as 'YYYY-MM-DD HH:MM:SS' strings — works with simple string comparison
    since your format is zero-padded and sortable."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, timestamp, app_name, text, screenshot_path, embedding FROM captures "
        "WHERE timestamp >= ? AND timestamp <= ?",
        (start_timestamp, end_timestamp)
    )
    rows = c.fetchall()
    conn.close()
    return _rows_to_dicts(rows)


def _rows_to_dicts(rows):
    results = []
    for row in rows:
        id_, timestamp, app_name, text, screenshot_path, emb_blob = row
        embedding = np.frombuffer(emb_blob, dtype=np.float32)
        results.append({
            "id": id_,
            "timestamp": timestamp,
            "app_name": app_name,
            "text": text,
            "screenshot_path": screenshot_path,
            "embedding": embedding
        })
    return results
