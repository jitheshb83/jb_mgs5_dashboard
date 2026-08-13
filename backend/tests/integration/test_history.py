"""Integration tests for GET /api/history query param filtering."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

BASE_TIME = datetime(2026, 8, 1, 0, 0, 0, tzinfo=UTC)


def _seed_snapshots(db_path: Path, count: int) -> list[str]:
    conn = sqlite3.connect(db_path)
    timestamps = []
    for i in range(count):
        fetched_at = (BASE_TIME + timedelta(days=i)).isoformat()
        timestamps.append(fetched_at)
        conn.execute(
            "INSERT INTO car_snapshot (fetched_at, soc_pct, raw_json) VALUES (?, ?, ?)",
            (fetched_at, 50.0 + i, "{}"),
        )
    conn.commit()
    conn.close()
    return timestamps


def test_history_default_returns_all_within_last_30_days(
    client: TestClient, temp_db_path: Path
) -> None:
    # Trigger app startup (creates schema) via any request before seeding directly.
    client.get("/api/latest")
    timestamps = _seed_snapshots(temp_db_path, 3)

    response = client.get(
        "/api/history",
        params={"from": timestamps[0], "to": timestamps[-1]},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["snapshots"]) == 3
    # Most recent first.
    assert [s["snapshot"]["soc_pct"] for s in body["snapshots"]] == [52.0, 51.0, 50.0]
    # Each entry carries its own fetched_at (see api_contract.md's 2026-08-12 correction).
    assert [s["fetched_at"] for s in body["snapshots"]] == [
        timestamps[2].replace("+00:00", "Z"),
        timestamps[1].replace("+00:00", "Z"),
        timestamps[0].replace("+00:00", "Z"),
    ]


def test_history_respects_from_to_range(client: TestClient, temp_db_path: Path) -> None:
    client.get("/api/latest")
    timestamps = _seed_snapshots(temp_db_path, 5)

    response = client.get(
        "/api/history",
        params={"from": timestamps[1], "to": timestamps[3]},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["snapshots"]) == 3
    assert [s["snapshot"]["soc_pct"] for s in body["snapshots"]] == [53.0, 52.0, 51.0]


def test_history_respects_limit(client: TestClient, temp_db_path: Path) -> None:
    client.get("/api/latest")
    timestamps = _seed_snapshots(temp_db_path, 5)

    response = client.get(
        "/api/history",
        params={"from": timestamps[0], "to": timestamps[-1], "limit": 2},
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["snapshots"]) == 2
    assert [s["snapshot"]["soc_pct"] for s in body["snapshots"]] == [54.0, 53.0]


def test_history_empty_when_no_snapshots(client: TestClient) -> None:
    response = client.get("/api/history")
    assert response.status_code == 200
    assert response.json() == {"snapshots": []}


def test_history_invalid_query_param_uses_contract_error_shape(client: TestClient) -> None:
    # `limit` must be an int -- FastAPI's default validation-error body is
    # {"detail": [...]}, not this app's {error, detail} contract shape. See
    # main.py's validation_exception_handler.
    response = client.get("/api/history", params={"limit": "not-a-number"})
    assert response.status_code == 422
    body = response.json()
    assert set(body.keys()) == {"error", "detail"}
    assert isinstance(body["error"], str)
    assert isinstance(body["detail"], str)
    assert "limit" in body["detail"]
