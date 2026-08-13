"""Unit tests for init_db's guarded ALTER TABLE that adds doors_json to a pre-existing
car_snapshot table (one created before doors_json existed in SCHEMA_SQL).

Per docs/architecture/data_model.md, v1 has no general migration framework -- this is the one
deliberate, additive exception (see docs/architecture/data_model.md's "Migration approach").
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.db.database import get_connection, init_db
from app.db.repository import SNAPSHOT_COLUMNS


def test_init_db_adds_doors_json_to_pre_existing_car_snapshot_table(tmp_path: Path) -> None:
    db_path = tmp_path / "pre_existing.db"

    # Simulate a DB created before doors_json existed: no doors_json column, one row
    # of pre-existing data that must survive the migration.
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE car_snapshot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fetched_at TIMESTAMP NOT NULL,
            soc_pct REAL,
            raw_json TEXT NOT NULL
        )
        """
    )
    conn.execute(
        "INSERT INTO car_snapshot (fetched_at, soc_pct, raw_json) VALUES (?, ?, ?)",
        ("2026-08-01T00:00:00+00:00", 55.0, "{}"),
    )
    conn.commit()
    conn.close()

    init_db(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(car_snapshot)")}
    assert "doors_json" in columns

    row = conn.execute("SELECT * FROM car_snapshot").fetchone()
    assert row["soc_pct"] == 55.0
    assert row["doors_json"] is None
    conn.close()


def test_init_db_is_idempotent_when_doors_json_already_present(tmp_path: Path) -> None:
    db_path = tmp_path / "fresh.db"

    init_db(db_path)
    # Calling init_db again (e.g. app restart) must not error even though doors_json
    # already exists.
    init_db(db_path)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(car_snapshot)")}
    assert "doors_json" in columns
    conn.close()


def test_snapshot_columns_matches_schema(tmp_path: Path) -> None:
    """Guard rail for repository.SNAPSHOT_COLUMNS, which is hand-maintained
    separately from SCHEMA_SQL (see repository.py's comment on it) -- if a
    column is ever added to one and not the other, this fails loudly instead
    of silently dropping a field on insert.
    """
    db_path = tmp_path / "schema_check.db"
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        table_columns = {row["name"] for row in conn.execute("PRAGMA table_info(car_snapshot)")}
        expected = table_columns - {"id", "fetched_at", "raw_json"}
        assert set(SNAPSHOT_COLUMNS) == expected
    finally:
        conn.close()
