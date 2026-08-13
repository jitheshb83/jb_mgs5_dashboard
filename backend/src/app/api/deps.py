"""FastAPI dependencies: a DB connection per request."""

from __future__ import annotations

import sqlite3
from collections.abc import Generator

from app.config import get_settings, resolve_database_path
from app.db.database import get_connection


def get_db() -> Generator[sqlite3.Connection, None, None]:
    settings = get_settings()
    db_path = resolve_database_path(settings.database_path)
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()
