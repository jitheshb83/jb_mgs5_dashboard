"""Integration tests for GET /api/latest/battery-usage."""

from __future__ import annotations

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
