"""Data access functions for car_snapshot and app_settings tables.

All functions take an open sqlite3.Connection so callers (API routes, tests) control
connection lifecycle and transactions explicitly.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Mapping
from datetime import datetime
from typing import cast

# Hand-maintained to match database.py's SCHEMA_SQL car_snapshot definition
# (minus id/fetched_at/raw_json) -- kept in sync by
# tests/unit/test_database_migration.py's test_snapshot_columns_matches_schema
# guard-rail test rather than a dynamic PRAGMA lookup, so a drift fails a test
# instead of silently dropping a field on insert.
SNAPSHOT_COLUMNS = (
    "soc_pct",
    "range_bms_km",
    "range_imcu_km",
    "is_charging",
    "charging_current",
    "plug_status",
    "battery_12v_voltage",
    "odometer_km",
    "cabin_temp_c",
    "tyre_pressure_fl",
    "tyre_pressure_fr",
    "tyre_pressure_rl",
    "tyre_pressure_rr",
    "latitude",
    "longitude",
    "doors_json",
)


def insert_snapshot(
    conn: sqlite3.Connection,
    *,
    fetched_at: datetime,
    snapshot_fields: dict[str, float | bool | str | None],
    raw_json: str,
) -> Mapping[str, object]:
    """Insert a new car_snapshot row and return its SNAPSHOT_COLUMNS fields.

    Built directly from the values just inserted rather than re-SELECTing the
    row -- every field the caller needs (via row_to_snapshot) was already
    known here, so the extra DB round trip was pure waste.
    """
    columns = ["fetched_at", *SNAPSHOT_COLUMNS, "raw_json"]
    values: list[object] = [fetched_at.isoformat()]
    values.extend(snapshot_fields.get(col) for col in SNAPSHOT_COLUMNS)
    values.append(raw_json)
    placeholders = ", ".join("?" for _ in columns)
    conn.execute(
        f"INSERT INTO car_snapshot ({', '.join(columns)}) VALUES ({placeholders})",
        values,
    )
    conn.commit()
    return {col: snapshot_fields.get(col) for col in SNAPSHOT_COLUMNS}


def get_latest_snapshot(conn: sqlite3.Connection) -> sqlite3.Row | None:
    row = conn.execute(
        "SELECT * FROM car_snapshot ORDER BY fetched_at DESC, id DESC LIMIT 1"
    ).fetchone()
    return cast("sqlite3.Row | None", row)


def get_snapshots(
    conn: sqlite3.Connection,
    *,
    from_dt: datetime,
    to_dt: datetime,
    limit: int,
) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM car_snapshot "
        "WHERE fetched_at >= ? AND fetched_at <= ? "
        # Same tie-break as get_latest_snapshot's ORDER BY, so /api/history's
        # ordering matches /api/latest's for rows sharing an identical
        # fetched_at (see api_contract.md's ordering note).
        "ORDER BY fetched_at DESC, id DESC LIMIT ?",
        (from_dt.isoformat(), to_dt.isoformat(), limit),
    ).fetchall()


def get_all_snapshots_ascending(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Full car_snapshot history, oldest first -- used by soh.py's full-charge-cycle
    detection, which needs to scan is_charging/soc_pct transitions in order."""
    return conn.execute(
        "SELECT id, fetched_at, soc_pct, is_charging, raw_json FROM car_snapshot "
        "ORDER BY fetched_at ASC, id ASC"
    ).fetchall()


def get_existing_soh_cycle_end_ids(conn: sqlite3.Connection) -> set[int]:
    """Already-recorded cycle end points -- soh.py uses this to avoid re-detecting
    (and re-inserting a duplicate row for) a full-charge cycle already stored."""
    rows = conn.execute("SELECT cycle_end_snapshot_id FROM soh_estimate").fetchall()
    return {row["cycle_end_snapshot_id"] for row in rows}


def insert_soh_estimate(
    conn: sqlite3.Connection,
    *,
    computed_at: datetime,
    cycle_start_snapshot_id: int,
    cycle_end_snapshot_id: int,
    soh_pct: float,
    usable_kwh_estimate: float,
    basis: str,
) -> None:
    conn.execute(
        "INSERT INTO soh_estimate "
        "(computed_at, cycle_start_snapshot_id, cycle_end_snapshot_id, soh_pct, "
        "usable_kwh_estimate, basis) VALUES (?, ?, ?, ?, ?, ?)",
        (
            computed_at.isoformat(),
            cycle_start_snapshot_id,
            cycle_end_snapshot_id,
            soh_pct,
            usable_kwh_estimate,
            basis,
        ),
    )
    conn.commit()


def get_soh_estimates(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """Most recent first -- same convention as get_snapshots/get_latest_snapshot."""
    return conn.execute(
        "SELECT computed_at, soh_pct, usable_kwh_estimate, basis FROM soh_estimate "
        "ORDER BY computed_at DESC, id DESC"
    ).fetchall()


def get_all_settings(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
    return {row["key"]: row["value"] for row in rows}


def update_settings(conn: sqlite3.Connection, updates: dict[str, str]) -> None:
    """Writes each key/value pair. Does not re-read the table afterwards --
    the caller already knows exactly what it wrote; a full re-SELECT here was
    a wasted round trip every callers already had the data for (see
    api/settings.py, the only caller, which always passes the complete
    merged settings dict and builds its response from that directly)."""
    for key, value in updates.items():
        conn.execute(
            "INSERT INTO app_settings (key, value) VALUES (?, ?) "
            "ON CONFLICT (key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
    conn.commit()
