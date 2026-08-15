"""Integration tests for GET /api/soh and its refresh-time persistence."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.fixtures.synthetic_saic_responses import synthetic_charging_management_data


def test_soh_empty_when_no_estimates_exist(client: TestClient) -> None:
    response = client.get("/api/soh")
    assert response.status_code == 200
    body = response.json()
    assert body["estimates"] == []
    assert body["nameplate_usable_kwh"] == 62.1


def _seed_charge_start(db_path: Path, *, fetched_at: datetime) -> None:
    raw_json = json.dumps(
        {
            "charging_management_data": {
                "rvsChargeStatus": {"realtimePower": 2_000},
            }
        }
    )
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO car_snapshot (fetched_at, soc_pct, is_charging, raw_json) VALUES (?, ?, ?, ?)",
        (fetched_at.isoformat(), 20.0, True, raw_json),
    )
    conn.commit()
    conn.close()


@pytest.fixture
def mock_saic_full_charge_end(monkeypatch: pytest.MonkeyPatch) -> None:
    """A refresh response representing a completed full-charge cycle's end point:
    98% SOC, still marked charging, realtimePower=2_620 (raw) -> 262.0 kWh current_energy_kwh."""
    from tests.fixtures.synthetic_saic_responses import synthetic_vehicle_status
    from tests.integration.conftest import FakeSaicApi

    class FakeSaicApiFullChargeEnd(FakeSaicApi):
        async def get_vehicle_charging_management_data(self, _vin: str) -> object:
            # total_battery_capacity=None matches this project's real vehicle (see
            # api_contract.md's 2026-08-15 correction) -- correction_factor stays 1.0, so
            # current_energy_kwh is realtimePower / 10.0 directly, uncorrected.
            return synthetic_charging_management_data(
                bms_pack_soc_dsp=980, realtime_power=2_620, total_battery_capacity=None
            )

        async def get_vehicle_status(self, _vin: str) -> object:
            return synthetic_vehicle_status()

    FakeSaicApiFullChargeEnd.login_call_count = 0
    monkeypatch.setattr("app.services.saic_client.SaicApi", FakeSaicApiFullChargeEnd)


def test_refresh_detects_and_persists_a_completed_full_charge_cycle(
    client: TestClient, temp_db_path: Path, mock_saic_full_charge_end: None
) -> None:
    # Trigger app startup (creates schema) before seeding directly.
    client.get("/api/latest")
    _seed_charge_start(temp_db_path, fetched_at=datetime.now(UTC) - timedelta(days=2))

    response = client.post("/api/refresh")
    assert response.status_code == 200

    soh_response = client.get("/api/soh")
    assert soh_response.status_code == 200
    body = soh_response.json()
    assert len(body["estimates"]) == 1
    estimate = body["estimates"][0]
    assert estimate["basis"] == "current_energy_kwh_delta"
    # kwh_delivered = 262.0 - 200.0 = 62.0, soc_delta = 98 - 20 = 78.
    assert estimate["usable_kwh_estimate"] == round(62.0 / 78 * 100, 2)
    assert estimate["soh_pct"] == round(estimate["usable_kwh_estimate"] / 62.1 * 100, 1)


def test_refresh_does_not_duplicate_an_already_recorded_cycle(
    client: TestClient, temp_db_path: Path, mock_saic_full_charge_end: None
) -> None:
    client.get("/api/latest")
    _seed_charge_start(temp_db_path, fetched_at=datetime.now(UTC) - timedelta(days=2))

    client.post("/api/refresh")
    first = client.get("/api/soh").json()
    assert len(first["estimates"]) == 1

    # A second refresh (past the rate-limit gap) that returns the exact same charging-management
    # snapshot shouldn't detect and store the same completed cycle again.
    conn = sqlite3.connect(temp_db_path)
    conn.execute(
        "UPDATE car_snapshot SET fetched_at = ? WHERE id = (SELECT MAX(id) FROM car_snapshot)",
        ((datetime.now(UTC) - timedelta(hours=1)).isoformat(),),
    )
    conn.commit()
    conn.close()

    client.post("/api/refresh")
    second = client.get("/api/soh").json()
    assert len(second["estimates"]) == 1


def test_refresh_still_succeeds_if_soh_detection_raises(
    client: TestClient, temp_db_path: Path, mock_saic_full_charge_end: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The new snapshot is already committed by the time SOH detection runs -- a bug there
    must not turn an otherwise-successful refresh into a client-visible failure (code-review
    follow-up to the 2026-08-15 SOH implementation)."""

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("simulated SOH detection failure")

    monkeypatch.setattr("app.api.refresh.compute_new_soh_estimates", _boom)

    client.get("/api/latest")
    _seed_charge_start(temp_db_path, fetched_at=datetime.now(UTC) - timedelta(days=2))

    response = client.post("/api/refresh")
    assert response.status_code == 200
    assert response.json()["source"] == "live"

    # The snapshot itself was still persisted despite the SOH-detection failure.
    latest = client.get("/api/latest")
    assert latest.status_code == 200
    assert latest.json()["snapshot"]["soc_pct"] == 98.0
