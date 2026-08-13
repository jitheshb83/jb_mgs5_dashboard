"""Integration tests: full POST /api/refresh -> SQLite round-trip.

Per docs/planning/testing_strategy.md, the SAIC API is always mocked here
(see tests/integration/conftest.py's FakeSaicApi) -- never call the real API.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from tests.integration.conftest import FakeSaicApi


def test_first_refresh_calls_live_and_persists_to_sqlite(
    client: TestClient, mock_saic_success: None, temp_db_path: Path
) -> None:
    response = client.post("/api/refresh")
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "live"
    assert body["fetched_at"].endswith("Z")

    snapshot = body["snapshot"]
    assert snapshot["soc_pct"] == 78.0
    assert snapshot["range_bms_km"] == 310.0
    assert snapshot["range_imcu_km"] == 295.0
    assert snapshot["odometer_km"] == 4210.5
    assert snapshot["battery_12v_voltage"] == 12.6
    assert snapshot["plug_status"] == "plugged"
    assert snapshot["is_charging"] is True
    # Location view deferred to v2 -- always null in v1 API responses.
    assert snapshot["latitude"] is None
    assert snapshot["longitude"] is None

    conn = sqlite3.connect(temp_db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM car_snapshot").fetchall()
    assert len(rows) == 1
    assert rows[0]["soc_pct"] == 78.0
    raw = json.loads(rows[0]["raw_json"])
    assert "vehicle_status" in raw
    assert "charging_management_data" in raw
    conn.close()


def test_second_refresh_within_gap_returns_cached(
    client: TestClient, mock_saic_success: None
) -> None:
    first = client.post("/api/refresh").json()
    second = client.post("/api/refresh").json()

    assert second["source"] == "cached"
    assert second["fetched_at"] == first["fetched_at"]
    assert second["snapshot"] == first["snapshot"]
    # Only the first refresh should have logged in to the (fake) SAIC API.
    assert FakeSaicApi.login_call_count == 1


def test_refresh_calls_live_again_once_gap_has_elapsed(
    client: TestClient, mock_saic_success: None, temp_db_path: Path
) -> None:
    client.post("/api/refresh")
    assert FakeSaicApi.login_call_count == 1

    # Backdate the stored snapshot so the 30-minute gap has elapsed, without
    # sleeping in the test.
    backdated = (datetime.now(UTC) - timedelta(minutes=31)).isoformat()
    conn = sqlite3.connect(temp_db_path)
    conn.execute("UPDATE car_snapshot SET fetched_at = ?", (backdated,))
    conn.commit()
    conn.close()

    second = client.post("/api/refresh")
    assert second.status_code == 200
    assert second.json()["source"] == "live"
    assert FakeSaicApi.login_call_count == 2


def test_refresh_saic_failure_returns_502_without_leaking_secrets(
    client: TestClient, mock_saic_auth_failure: None
) -> None:
    response = client.post("/api/refresh")
    assert response.status_code == 502
    body = response.json()
    assert set(body.keys()) == {"error", "detail"}
    assert isinstance(body["detail"], str)
    # `error` must be a short, static, safe code -- never the raw underlying
    # exception text (see saic_client.py's SaicClientError docstring).
    assert body["error"] == "saic_authentication_failure"

    full_text = response.text
    assert "super-secret-test-password" not in full_text
    assert "Traceback" not in full_text
    # The fake auth failure's exception message ("invalid credentials") must
    # never reach the response body -- only the server-side log should see it.
    assert "invalid credentials" not in full_text
