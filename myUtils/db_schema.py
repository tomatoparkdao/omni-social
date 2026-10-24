"""Add missing legacy tables without replacing any existing account data."""
import sqlite3
from contextlib import closing
from pathlib import Path


def ensure_schema(base_dir):
    db_dir = Path(base_dir) / 'db'
    db_dir.mkdir(parents=True, exist_ok=True)
    # These local storage roots are created only when absent; existing sessions and media are untouched.
    for directory in ('videoFile', 'cookiesFile', 'cookies'):
        (Path(base_dir) / directory).mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_dir / 'database.db')) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS user_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type INTEGER NOT NULL,
            filePath TEXT NOT NULL,
            userName TEXT NOT NULL,
            status INTEGER DEFAULT 0
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS file_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filesize REAL,
            upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            file_path TEXT
        )''')
        conn.commit()
