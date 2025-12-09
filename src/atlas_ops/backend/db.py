from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional


class SignalStore:
    """Lightweight SQLite-backed signal store."""

    def __init__(self, db_url: str) -> None:
        if not db_url.startswith("sqlite://"):
            raise ValueError("Only sqlite URLs are supported (sqlite:///path/to/db)")
        _, _, path = db_url.partition("sqlite://")
        self.db_path = Path(path.replace("/", "", 1)) if path.startswith("/") else Path(path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_tables()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _ensure_tables(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    created_at TEXT NOT NULL
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

    def migrate(self) -> None:
        self._ensure_tables()

    def add_signal(self, name: str, status: str, details: Optional[dict] = None) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO signals (name, status, details, created_at) VALUES (?, ?, ?, ?)",
                (
                    name,
                    status,
                    json.dumps(details or {}),
                    datetime.utcnow().isoformat(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def list_signals(self) -> List[dict]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT id, name, status, details, created_at FROM signals ORDER BY created_at DESC"
            ).fetchall()
        finally:
            conn.close()

        return [
            {
                "id": row[0],
                "name": row[1],
                "status": row[2],
                "details": json.loads(row[3]) if row[3] else {},
                "created_at": row[4],
            }
            for row in rows
        ]

    def recent_signals(self, limit: int = 20) -> Iterable[dict]:
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT id, name, status, details, created_at FROM signals ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        finally:
            conn.close()

        for row in rows:
            yield {
                "id": row[0],
                "name": row[1],
                "status": row[2],
                "details": json.loads(row[3]) if row[3] else {},
                "created_at": row[4],
            }

