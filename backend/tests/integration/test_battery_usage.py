"""Integration tests for GET /api/latest/battery-usage."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient


def test_battery_usage_404_when_no_snapshot_exists(client: TestClient) -> None:
    response = client.get("/api/latest/battery-usage")
    assert response.status_code == 404
    body = response.json()
    assert set(body.keys()) == {"error", "detail"}


def test_battery_usage_200_after_a_refresh(client: TestClient, mock_saic_success: None) -> None:
    client.post("/api/refresh")

    response = client.get("/api/latest/battery-usage")
    assert response.status_code == 200
    body = response.json()
    assert "fetched_at" in body
    battery_usage = body["battery_usage"]

    # Matches synthetic_charging_management_data()'s defaults (totalBatteryCapacity=618 ->
    # 61.8 kWh self-reported) corrected against the default battery_nameplate_kwh (62.1).
    assert battery_usage["total_battery_capacity_kwh"] == 61.8
    assert battery_usage["power_usage_today_kwh"] == 42.2
    assert battery_usage["power_usage_since_last_charge_kwh"] == 126.61
    assert battery_usage["last_charge_added_kwh"] == 385.86
    assert battery_usage["mileage_today_km"] == 21.3
    assert battery_usage["mileage_since_last_charge_km"] == 143.7
    # 42.2 kWh / 21.3 km * 100, 126.61 kWh / 143.7 km * 100.
    assert battery_usage["efficiency_today_kwh_per_100km"] == 198.12
    assert battery_usage["efficiency_since_last_charge_kwh_per_100km"] == 88.11
    # Vehicle reported every field itself -- nothing estimated.
    assert battery_usage["estimated_fields"] == []


_NULL_RVS_RAW_JSON = json.dumps(
    {
        "vehicle_status": {},
        "charging_management_data": {
            "chrgMgmtData": {},
            "rvsChargeStatus": {
                "totalBatteryCapacity": None,
                "powerUsageOfDay": None,
                "powerUsageSinceLastCharge": None,
                "lastChargeEndingPower": None,
                "realtimePower": None,
                "mileageOfDay": None,
                "mileageSinceLastCharge": None,
            },
        },
    }
)


def _insert_snapshot(
    db_path: Path,
    *,
    fetched_at: datetime,
    soc_pct: float,
    odometer_km: float,
    is_charging: bool,
    raw_json: str = "{}",
) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO car_snapshot "
        "(fetched_at, soc_pct, odometer_km, is_charging, raw_json) VALUES (?, ?, ?, ?, ?)",
        (fetched_at.isoformat(), soc_pct, odometer_km, is_charging, raw_json),
    )
    conn.commit()
    conn.close()


def test_battery_usage_falls_back_to_history_when_vehicle_reports_null(
    client: TestClient, temp_db_path: Path
) -> None:
    # Trigger app startup (creates schema) before seeding directly, same pattern as
    # test_history.py.
    client.get("/api/latest")

    now = datetime.now(UTC)
    charge_start = now - timedelta(days=2)
    charge_end = now - timedelta(days=1)
    latest = now - timedelta(minutes=5)

    _insert_snapshot(
        temp_db_path, fetched_at=charge_start, soc_pct=30.0, odometer_km=1600.0, is_charging=True
    )
    _insert_snapshot(
        temp_db_path,
        fetched_at=charge_start + timedelta(hours=1),
        soc_pct=90.0,
        odometer_km=1600.0,
        is_charging=True,
    )
    _insert_snapshot(
        temp_db_path, fetched_at=charge_end, soc_pct=90.0, odometer_km=1600.0, is_charging=False
    )
    _insert_snapshot(
        temp_db_path,
        fetched_at=latest,
        soc_pct=80.0,
        odometer_km=1620.0,
        is_charging=False,
        raw_json=_NULL_RVS_RAW_JSON,
    )

    response = client.get("/api/latest/battery-usage")
    assert response.status_code == 200
    battery_usage = response.json()["battery_usage"]

    # Vehicle default nameplate fallback (no app_settings override in this test).
    assert battery_usage["total_battery_capacity_kwh"] == 62.1
    # 90 - 30 = 60 pct of 62.1 kWh.
    assert battery_usage["last_charge_added_kwh"] == 37.26
    # 90 -> 80 = 10 pct of 62.1 kWh, since the charge ended.
    assert battery_usage["power_usage_since_last_charge_kwh"] == 6.21
    # 1620 - 1600 km, since the charge ended.
    assert battery_usage["mileage_since_last_charge_km"] == 20.0
    # 6.21 kWh / 20.0 km * 100 -- also estimated, since both its inputs are.
    assert battery_usage["efficiency_since_last_charge_kwh_per_100km"] == 31.05
    # power_usage_today_kwh and mileage_today_km both derive to 0.0 (no drive today, only
    # charging) -- 0.0 km distance makes efficiency undefined, so this stays null rather than
    # being added to estimated_fields (nothing to flag an estimate on top of).
    assert battery_usage["efficiency_today_kwh_per_100km"] is None
    assert set(battery_usage["estimated_fields"]) == {
        "total_battery_capacity_kwh",
        "power_usage_since_last_charge_kwh",
        "last_charge_added_kwh",
        "mileage_since_last_charge_km",
        "power_usage_today_kwh",
        "mileage_today_km",
        "efficiency_since_last_charge_kwh_per_100km",
    }
    # current_energy_kwh never falls back -- stays null when the vehicle doesn't report it.
    assert battery_usage["current_energy_kwh"] is None
