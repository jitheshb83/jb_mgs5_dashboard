"""Integration tests for GET /api/latest/advanced."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_advanced_404_when_no_snapshot_exists(client: TestClient) -> None:
    response = client.get("/api/latest/advanced")
    assert response.status_code == 404
    body = response.json()
    assert set(body.keys()) == {"error", "detail"}


def test_advanced_200_after_a_refresh(client: TestClient, mock_saic_success: None) -> None:
    client.post("/api/refresh")

    response = client.get("/api/latest/advanced")
    assert response.status_code == 200
    body = response.json()
    assert "fetched_at" in body
    advanced = body["advanced"]

    # Matches synthetic_vehicle_status()'s defaults.
    assert advanced["engine_running"] is False
    assert advanced["is_parked"] is True
    assert advanced["hand_brake_on"] is True
    assert advanced["main_beam_on"] is False
    assert advanced["dipped_beam_on"] is False
    assert advanced["side_light_on"] is False
    assert advanced["exterior_temp_c"] == 19.0
    assert advanced["remote_climate_status"] == "off"
    assert advanced["rear_window_heat_on"] is False
    assert advanced["front_left_seat_heat_level"] == 0
    assert advanced["front_right_seat_heat_level"] == 0
    assert advanced["current_journey"] is None
    # with_gps defaults to False in the synthetic fixture.
    assert advanced["gps"] is None
    # alert_data_sum defaults to [] in the synthetic fixture -- an empty list is
    # falsy for "any active", not "unknown" (that's None, only when the API
    # didn't return the field at all).
    assert advanced["has_active_alerts"] is False
    assert advanced["vehicle_reported_at"] is not None

    # Matches synthetic_charging_management_data()'s defaults.
    assert advanced["charging_pile_id"] == "PILE-0001"
    assert advanced["charging_pile_supplier"] == "ACME Charging"
    assert advanced["charging_type_raw"] == 1
    assert advanced["charging_working_voltage_raw"] == 230
    assert advanced["charging_working_current_raw"] == 16
    assert advanced["charging_remaining_time_minutes"] == 45
    assert advanced["target_soc_pct"] == 80
    assert advanced["charge_current_limit"] == "16A"
    # Regression test: fixture default is ccuEleccLckCtrlDspCmd=2 (a real captured
    # value, not 0 or 1) -- must be False under the confirmed `== 1` convention,
    # not True under the `> 0` convention _int_to_bool uses elsewhere (the bug
    # this fixture default exists to catch).
    assert advanced["charging_port_locked"] is False
    assert advanced["bms_charging_status"] == "CHARGING_1"
    assert advanced["charging_stop_reason"] is None  # bms_chrg_sp_rsn not set by default
    assert advanced["hv_battery"] == {"voltage_v": 600.0, "power_kw": -0.6}
    assert advanced["battery_heating"] == {"active": None, "stop_reason": None}
    # Not set by default in the fixture -- both null rather than a guessed default.
    assert advanced["scheduled_charging"] is None
    assert advanced["obc_ac_input"] is None

    # Fields with no confirmed decode -- surfaced raw, not fabricated.
    raw_undecoded = advanced["raw_undecoded"]
    for field in (
        "lastKeySeen",
        "steeringHeatLevel",
        "steeringWheelHeatFailureReason",
        "timeOfLastCANBUSActivity",
        "vehElecRngDsp",
        "clstrDspdFuelLvlSgmt",
        "extendedData1",
        "extendedData2",
        "powerMode",
        "vehicleAlarmStatus",
        "wheelTyreMonitorStatus",
        "canBusActive",
        "fuelLevelPrc",
        "fuelRange",
        "fuelRangeElec",
        "bmsChrgOtptCrntReq",
        "chrgngDoorPosSts",
        "rvsExtendedData1",
        "rvsFuelRangeElec",
        "alertDataSum",
    ):
        assert field in raw_undecoded
    # Now confirmed-decoded elsewhere -- must NOT still appear as "undecoded".
    assert "bmsReserCtrlDspCmd" not in raw_undecoded
    assert "onBdChrgrAltrCrntInptCrnt" not in raw_undecoded


def test_advanced_scheduled_charging_and_obc_ac_input(
    client: TestClient, mock_saic_success_with_schedule_and_obc: None
) -> None:
    client.post("/api/refresh")

    response = client.get("/api/latest/advanced")
    assert response.status_code == 200
    advanced = response.json()["advanced"]

    # Matches a real captured vehicle response (2026-08-13): a configured but
    # DISABLED 22:00-06:00 schedule.
    assert advanced["scheduled_charging"] == {
        "mode": "DISABLED",
        "start_time": "22:00",
        "end_time": "06:00",
    }
    assert advanced["obc_ac_input"] == {
        "current_a": 16.0,
        "voltage_v": 230.0,
        "power_single_phase_kw": 3.68,
        "power_three_phase_kw": 2.125,
    }
