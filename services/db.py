from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _db_path() -> Path:
    path = Path(os.getenv("DB_PATH", "data/smartpid.db"))
    return path if path.is_absolute() else ROOT / path


@contextmanager
def _connect():
    path = _db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _connect() as c:
        c.execute(
            """CREATE TABLE IF NOT EXISTS projects (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT UNIQUE NOT NULL,
                   created_at TEXT DEFAULT CURRENT_TIMESTAMP
               )"""
        )


def list_projects() -> list:
    with _connect() as c:
        return [r[0] for r in c.execute("SELECT name FROM projects ORDER BY id")]


def create_project(name: str) -> None:
    with _connect() as c:
        c.execute("INSERT OR IGNORE INTO projects (name) VALUES (?)", (name,))