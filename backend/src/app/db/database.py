"""SQLite schema creation and connection helpers.

Schema per docs/architecture/data_model.md. Created fresh via CREATE TABLE IF NOT EXISTS
on backend startup -- v1 has no migration framework.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS car_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fetched_at TIMESTAMP NOT NULL,
    soc_pct REAL,
    range_bms_km REAL,
    range_imcu_km REAL,
    is_charging BOOLEAN,
    charging_current REAL,
    plug_status TEXT,
    battery_12v_voltage REAL,
    odometer_km REAL,
    cabin_temp_c REAL,
    tyre_pressure_fl REAL,
    tyre_pressure_fr REAL,
    tyre_pressure_rl REAL,
    tyre_pressure_rr REAL,
    latitude REAL,
    longitude REAL,
    doors_json TEXT,
    raw_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_car_snapshot_fetched_at ON car_snapshot (fetched_at);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS soh_estimate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    computed_at TIMESTAMP NOT NULL,
    cycle_start_snapshot_id INTEGER REFERENCES car_snapshot (id),
    cycle_end_snapshot_id INTEGER REFERENCES car_snapshot (id),
    soh_pct REAL,
    usable_kwh_estimate REAL,
    basis TEXT
);
"""

# Defaults per docs/architecture/data_model.md app_settings table.
DEFAULT_SETTINGS: dict[str, str] = {
    "schedule_enabled": "false",
    "schedule_interval_minutes": "120",
    "min_refresh_gap_minutes": "30",
    "battery_nameplate_kwh": "62.1",
}


def get_connection(db_path: Path) -> sqlite3.Connection:
    """Open a new SQLite connection with row access by column name.

    check_same_thread=False: each connection is scoped to a single request
    (opened and closed within app.api.deps.get_db) but FastAPI's sync-dependency
    handling can hand it from a worker thread to the event loop thread, so the
    default same-thread check would reject legitimate single-threaded-in-practice
    use. There is no concurrent multi-threaded use of a single connection here.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Path) -> None:
    """Create the schema (if missing) and seed default settings (if missing)."""
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_SQL)
        # v1 has no migration framework (see docs/architecture/data_model.md), but a
        # pre-existing car_snapshot table (from before doors_json was added) won't pick
        # up the new column from CREATE TABLE IF NOT EXISTS. Guarded, additive ALTER --
        # not a general migration framework.
        existing_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(car_snapshot)")
        }
        if "doors_json" not in existing_columns:
            conn.execute("ALTER TABLE car_snapshot ADD COLUMN doors_json TEXT")
        for key, value in DEFAULT_SETTINGS.items():
            conn.execute(
                "INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)",
                (key, value),
            )
        conn.commit()
    finally:
        conn.close()
