"""Conversion helpers between SQLite rows and API response models."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from datetime import UTC, datetime

from fastapi.responses import JSONResponse

from app.db.repository import SNAPSHOT_COLUMNS
from app.models.schemas import ErrorResponse, Snapshot


def row_to_snapshot(row: sqlite3.Row | Mapping[str, object]) -> Snapshot:
    fields: dict[str, object] = {
        col: row[col] for col in SNAPSHOT_COLUMNS if col != "doors_json"
    }
    doors_json = row["doors_json"]
    fields["doors"] = json.loads(str(doors_json)) if doors_json is not None else None
    return Snapshot.model_validate(fields)


def parse_fetched_at(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def no_snapshot_response() -> JSONResponse:
    """Shared 404 body for every '/api/latest*' route when no snapshot exists
    yet -- used by latest.py, advanced.py, and battery_usage.py so the three
    stay in sync by construction instead of by copy-paste discipline."""
    return JSONResponse(
        status_code=404,
        content=ErrorResponse(
            error="no_snapshot",
            detail="No snapshot exists yet. Trigger a refresh first.",
        ).model_dump(),
    )
