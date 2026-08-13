"""Integration tests for GET/PUT /api/settings."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_get_settings_returns_documented_defaults(client: TestClient) -> None:
    response = client.get("/api/settings")
    assert response.status_code == 200
    assert response.json() == {
        "schedule_enabled": False,
        "schedule_interval_minutes": 120,
        "min_refresh_gap_minutes": 30,
        "battery_nameplate_kwh": 62.1,
    }


def test_put_settings_partial_update(client: TestClient) -> None:
    response = client.put("/api/settings", json={"schedule_enabled": True})
    assert response.status_code == 200
    body = response.json()
    assert body["schedule_enabled"] is True
    # Unset fields are unchanged.
    assert body["schedule_interval_minutes"] == 120
    assert body["min_refresh_gap_minutes"] == 30
    assert body["battery_nameplate_kwh"] == 62.1

    # Persisted -- a subsequent GET reflects it.
    assert client.get("/api/settings").json()["schedule_enabled"] is True


def test_put_settings_rejects_interval_below_min_gap(client: TestClient) -> None:
    response = client.put("/api/settings", json={"schedule_interval_minutes": 10})
    assert response.status_code == 400
    body = response.json()
    assert set(body.keys()) == {"error", "detail"}
    assert "10" in body["detail"]
    assert "30" in body["detail"]

    # Rejected update must not have been persisted.
    assert client.get("/api/settings").json()["schedule_interval_minutes"] == 120


def test_put_settings_allows_interval_equal_to_min_gap(client: TestClient) -> None:
    response = client.put(
        "/api/settings", json={"schedule_interval_minutes": 30, "min_refresh_gap_minutes": 30}
    )
    assert response.status_code == 200
    assert response.json()["schedule_interval_minutes"] == 30
