"""Integration tests for GET /api/latest."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_latest_404_when_no_snapshot_exists(client: TestClient) -> None:
    response = client.get("/api/latest")
    assert response.status_code == 404
    body = response.json()
    assert set(body.keys()) == {"error", "detail"}


def test_latest_200_after_a_refresh(client: TestClient, mock_saic_success: None) -> None:
    refresh_body = client.post("/api/refresh").json()

    response = client.get("/api/latest")
    assert response.status_code == 200
    body = response.json()
    assert body["fetched_at"] == refresh_body["fetched_at"]
    assert body["snapshot"] == refresh_body["snapshot"]


def test_latest_snapshot_includes_doors(client: TestClient, mock_saic_success: None) -> None:
    client.post("/api/refresh")

    body = client.get("/api/latest").json()
    # Matches synthetic_vehicle_status()'s defaults: locked, all doors/windows closed.
    assert body["snapshot"]["doors"] == {
        "locked": True,
        "driver_door_open": False,
        "passenger_door_open": False,
        "rear_left_door_open": False,
        "rear_right_door_open": False,
        "bonnet_open": False,
        "boot_open": False,
        "driver_window_open": False,
        "passenger_window_open": False,
        "rear_left_window_open": False,
        "rear_right_window_open": False,
        "sunroof_open": False,
    }
