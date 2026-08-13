"""Unit tests for mapping raw saic_ismart_client_ng dataclasses onto Snapshot fields.

Uses the real dataclasses from the installed saic_ismart_client_ng library
(populated with synthetic values -- see module docstring in
backend/tests/fixtures/synthetic_saic_responses.py) so a schema change in the
library would be caught by a TypeError/AttributeError here, not silently ignored.
"""

from __future__ import annotations

import json

from app.services.saic_client import map_to_snapshot_fields
from tests.fixtures.synthetic_saic_responses import (
    synthetic_charging_management_data,
    synthetic_vehicle_status,
)


def test_maps_soc_from_bms_pack_soc_dsp() -> None:
    vehicle = synthetic_vehicle_status()
    charging = synthetic_charging_management_data(bms_pack_soc_dsp=780)
    fields = map_to_snapshot_fields(vehicle, charging)
    assert fields["soc_pct"] == 78.0


def test_falls_back_to_extended_data1_when_bms_soc_missing() -> None:
    vehicle = synthetic_vehicle_status(extended_data1=55)
    charging = synthetic_charging_management_data(bms_pack_soc_dsp=None)
    fields = map_to_snapshot_fields(vehicle, charging)
    assert fields["soc_pct"] == 55.0


def test_maps_ranges_tyre_pressure_mileage_voltage() -> None:
    vehicle = synthetic_vehicle_status(
        mileage=42105,
        battery_voltage=126,
        front_left_tyre_pressure=60,
    )
    charging = synthetic_charging_management_data(bms_estd_elec_rng=310, imcu_veh_elec_rng=295)
    fields = map_to_snapshot_fields(vehicle, charging)
    assert fields["odometer_km"] == 4210.5
    assert fields["battery_12v_voltage"] == 12.6
    assert fields["tyre_pressure_fl"] == 2.4
    assert fields["range_bms_km"] == 310.0
    assert fields["range_imcu_km"] == 295.0


def test_plug_status_and_charging_current() -> None:
    vehicle = synthetic_vehicle_status()
    charging = synthetic_charging_management_data(charging_gun_state=1, bms_pack_crnt=19980)
    fields = map_to_snapshot_fields(vehicle, charging)
    assert fields["plug_status"] == "plugged"
    assert fields["is_charging"] is True
    assert fields["charging_current"] is not None


def test_unplugged_and_not_charging() -> None:
    vehicle = synthetic_vehicle_status()
    charging = synthetic_charging_management_data(charging_gun_state=0, bms_chrg_sts=0)
    fields = map_to_snapshot_fields(vehicle, charging)
    assert fields["plug_status"] == "unplugged"
    assert fields["is_charging"] is False


def test_latitude_longitude_always_null_in_v1() -> None:
    # Location view is deferred to v2 (docs/planning/decisions_log.md) -- lat/long
    # must stay null even though the synthetic GPS payload has real-looking values.
    vehicle = synthetic_vehicle_status(with_gps=True)
    charging = synthetic_charging_management_data()
    fields = map_to_snapshot_fields(vehicle, charging)
    assert fields["latitude"] is None
    assert fields["longitude"] is None


def test_missing_optional_data_yields_null_fields() -> None:
    vehicle = synthetic_vehicle_status(basic_status=None)
    charging = synthetic_charging_management_data(chrg_mgmt_data=None, rvs_charge_status=None)
    fields = map_to_snapshot_fields(vehicle, charging)
    assert fields["odometer_km"] is None
    assert fields["battery_12v_voltage"] is None
    assert fields["plug_status"] is None
    assert fields["is_charging"] is None
    assert fields["doors_json"] is None


def test_doors_locked_and_closed() -> None:
    vehicle = synthetic_vehicle_status(
        lock_status=1,
        driver_door=0,
        passenger_door=0,
        rear_left_door=0,
        rear_right_door=0,
        bonnet_status=0,
        boot_status=0,
        driver_window=0,
        passenger_window=0,
        rear_left_window=0,
        rear_right_window=0,
        sunroof_status=0,
    )
    charging = synthetic_charging_management_data()
    fields = map_to_snapshot_fields(vehicle, charging)
    assert fields["doors_json"] is not None
    doors = json.loads(fields["doors_json"])  # type: ignore[arg-type]
    assert doors == {
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


def test_doors_unlocked_and_open() -> None:
    vehicle = synthetic_vehicle_status(
        lock_status=0,
        driver_door=1,
        passenger_door=1,
        rear_left_door=1,
        rear_right_door=1,
        bonnet_status=1,
        boot_status=1,
        driver_window=1,
        passenger_window=1,
        rear_left_window=1,
        rear_right_window=1,
        sunroof_status=1,
    )
    charging = synthetic_charging_management_data()
    fields = map_to_snapshot_fields(vehicle, charging)
    doors = json.loads(fields["doors_json"])  # type: ignore[arg-type]
    # lock_status=0 means unlocked (locked=False); every door/window/bonnet/boot/sunroof
    # raw value of 1 means open (True).
    assert doors["locked"] is False
    assert all(value is True for key, value in doors.items() if key != "locked")


def test_doors_individual_field_null_when_raw_value_none() -> None:
    vehicle = synthetic_vehicle_status(lock_status=None, driver_door=1)
    charging = synthetic_charging_management_data()
    fields = map_to_snapshot_fields(vehicle, charging)
    doors = json.loads(fields["doors_json"])  # type: ignore[arg-type]
    assert doors["locked"] is None
    assert doors["driver_door_open"] is True


def test_doors_whole_object_null_when_basic_vehicle_status_missing() -> None:
    vehicle = synthetic_vehicle_status(basic_status=None)
    charging = synthetic_charging_management_data()
    fields = map_to_snapshot_fields(vehicle, charging)
    assert fields["doors_json"] is None
