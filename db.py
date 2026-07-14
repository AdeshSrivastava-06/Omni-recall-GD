import sqlite3
import json
import numpy as np

DB_PATH = "omnirecall.db"

DEFAULT_BLOCKED_APPS = [
    "1Password",
    "Bitwarden",
    "Banking",
    "Incognito",
    "Netbanking",
    "Password",
    "OmniRecall",
    "localhost:8501",
    "Streamlit"
]


def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS captures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            app_name TEXT NOT NULL,
            text TEXT NOT NULL,
            screenshot_path TEXT,
            archived_json TEXT,
            embedding BLOB NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            app_name TEXT PRIMARY KEY,
            blocked INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.commit()

    # Pre-populate default sensitive apps, only if the settings table is empty
    c.execute("SELECT COUNT(*) FROM app_settings")
    count = c.fetchone()[0]
    if count == 0:
        for app in DEFAULT_BLOCKED_APPS:
            c.execute(
                "INSERT OR IGNORE INTO app_settings (app_name, blocked) VALUES (?, 1)",
                (app,)
            )
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
    c.execute("SELECT id, timestamp, app_name, text, screenshot_path, archived_json, embedding FROM captures")
    rows = c.fetchall()
    conn.close()
    return _rows_to_dicts(rows)


def get_captures_in_range(start_timestamp: str, end_timestamp: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, timestamp, app_name, text, screenshot_path, archived_json, embedding FROM captures "
        "WHERE timestamp >= ? AND timestamp <= ? ORDER BY timestamp ASC",
        (start_timestamp, end_timestamp)
    )
    rows = c.fetchall()
    conn.close()
    return _rows_to_dicts(rows)


def _rows_to_dicts(rows):
    results = []
    for row in rows:
        id_, timestamp, app_name, text, screenshot_path, archived_json, emb_blob = row
        embedding = np.frombuffer(emb_blob, dtype=np.float32)
        results.append({
            "id": id_,
            "timestamp": timestamp,
            "app_name": app_name,
            "text": text,
            "screenshot_path": screenshot_path,
            "archived_json": archived_json,
            "embedding": embedding
        })
    return results


# ---- Storage cleanup: archive old screenshots as JSON, delete PNG ----

def get_captures_older_than(cutoff_timestamp: str):
    """Returns captures older than cutoff that still have a screenshot file."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "SELECT id, timestamp, app_name, text, screenshot_path FROM captures "
        "WHERE timestamp < ? AND screenshot_path IS NOT NULL",
        (cutoff_timestamp,)
    )
    rows = c.fetchall()
    conn.close()
    return rows


def archive_capture(capture_id: int, timestamp: str, app_name: str, text: str):
    """Store a JSON record in place of the screenshot, and clear screenshot_path."""
    archived = json.dumps({"timestamp": timestamp, "app_name": app_name, "text": text})
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "UPDATE captures SET archived_json = ?, screenshot_path = NULL WHERE id = ?",
        (archived, capture_id)
    )
    conn.commit()
    conn.close()


# ---- Privacy settings ----

def get_all_app_settings():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT app_name, blocked FROM app_settings ORDER BY app_name ASC")
    rows = c.fetchall()
    conn.close()
    return [{"app_name": r[0], "blocked": bool(r[1])} for r in rows]


def get_blocked_apps():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT app_name FROM app_settings WHERE blocked = 1")
    rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]


def set_app_blocked(app_name: str, blocked: bool):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO app_settings (app_name, blocked) VALUES (?, ?) "
        "ON CONFLICT(app_name) DO UPDATE SET blocked = excluded.blocked",
        (app_name, int(blocked))
    )
    conn.commit()
    conn.close()


def add_custom_app(app_name: str, blocked: bool = True):
    set_app_blocked(app_name, blocked)
