import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'history.db')


class HistoryStore:
    """SQLite-backed store for transcription history."""

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transcriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    duration REAL DEFAULT 0,
                    model TEXT DEFAULT ''
                )
                """
            )

    def add(self, text, duration=0.0, model=''):
        text = (text or '').strip()
        if not text:
            return None
        created_at = datetime.now().isoformat(timespec='seconds')
        with self._connect() as conn:
            cur = conn.execute(
                "INSERT INTO transcriptions (text, created_at, duration, model) VALUES (?, ?, ?, ?)",
                (text, created_at, float(duration or 0), model or ''),
            )
            return cur.lastrowid

    def list(self, query='', limit=500):
        sql = "SELECT * FROM transcriptions"
        params = []
        if query:
            sql += " WHERE text LIKE ?"
            params.append(f'%{query}%')
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def delete(self, item_id):
        with self._connect() as conn:
            conn.execute("DELETE FROM transcriptions WHERE id = ?", (item_id,))

    def clear(self):
        with self._connect() as conn:
            conn.execute("DELETE FROM transcriptions")
