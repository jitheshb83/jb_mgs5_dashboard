"""Unit tests for the battery-usage correction-factor math (GET /api/latest/battery-usage).

Per docs/architecture/api_contract.md: correction_factor = battery_nameplate_kwh /
total_battery_capacity_kwh (1.0 if the vehicle didn't report a capacity, or reported <= 0),
applied as round((correction_factor * raw_value) / 10.0, 2) to the kWh fields. Mileage fields
are raw / 10.0, validated 0 <= raw <= 65535.
"""

from __future__ import annotations

from app.services.battery_usage import (
    compute_efficiency_kwh_per_100km,
    decode_battery_usage,
    decode_uncorrected_current_energy_kwh,
)


def _raw(rvs: dict[str, object] | None) -> dict[str, object]:
    return {"charging_management_data": {"rvsChargeStatus": rvs}}


def test_capacity_present_applies_correction_factor() -> None:
    raw = _raw(
        {
            "totalBatteryCapacity": 618,  # 61.8 kWh self-reported
            "powerUsageOfDay": 420,
            "powerUsageSinceLastCharge": 1_260,
            "lastChargeEndingPower": 3_840,
            "realtimePower": 3_440,  # current battery energy content, not a power rate
            "mileageOfDay": 213,
            "mileageSinceLastCharge": 1_437,
        }
    )
    result = decode_battery_usage(raw, battery_nameplate_kwh=62.1)
    assert result["total_battery_capacity_kwh"] == 61.8
    # correction_factor = 62.1 / 61.8
    assert result["power_usage_today_kwh"] == 42.2
    assert result["power_usage_since_last_charge_kwh"] == 126.61
    assert result["last_charge_added_kwh"] == 385.86
    assert result["current_energy_kwh"] == 345.67
    assert result["mileage_today_km"] == 21.3
    assert result["mileage_since_last_charge_km"] == 143.7


def test_capacity_absent_uses_correction_factor_of_one() -> None:
    raw = _raw({"totalBatteryCapacity": None, "powerUsageOfDay": 420})
    result = decode_battery_usage(raw, battery_nameplate_kwh=62.1)
    assert result["total_battery_capacity_kwh"] is None
    # No correction applied -- raw value / 10.0 directly.
    assert result["power_usage_today_kwh"] == 42.0


def test_capacity_reported_as_zero_uses_correction_factor_of_one() -> None:
    raw = _raw({"totalBatteryCapacity": 0, "powerUsageOfDay": 420})
    result = decode_battery_usage(raw, battery_nameplate_kwh=62.1)
    assert result["total_battery_capacity_kwh"] is None
    assert result["power_usage_today_kwh"] == 42.0


def test_capacity_reported_as_negative_uses_correction_factor_of_one() -> None:
    raw = _raw({"totalBatteryCapacity": -5, "powerUsageOfDay": 420})
    result = decode_battery_usage(raw, battery_nameplate_kwh=62.1)
    assert result["total_battery_capacity_kwh"] is None
    assert result["power_usage_today_kwh"] == 42.0


def test_mileage_out_of_range_is_null() -> None:
    raw = _raw({"mileageOfDay": 65_536, "mileageSinceLastCharge": -1})
    result = decode_battery_usage(raw, battery_nameplate_kwh=62.1)
    assert result["mileage_today_km"] is None
    assert result["mileage_since_last_charge_km"] is None


def test_mileage_boundary_65535_is_valid() -> None:
    raw = _raw({"mileageOfDay": 65_535})
    result = decode_battery_usage(raw, battery_nameplate_kwh=62.1)
    assert result["mileage_today_km"] == 6553.5


def test_missing_rvs_charge_status_yields_all_null() -> None:
    raw: dict[str, object] = {"charging_management_data": {"rvsChargeStatus": None}}
    result = decode_battery_usage(raw, battery_nameplate_kwh=62.1)
    assert result == {
        "total_battery_capacity_kwh": None,
        "power_usage_today_kwh": None,
        "power_usage_since_last_charge_kwh": None,
        "last_charge_added_kwh": None,
        "current_energy_kwh": None,
        "mileage_today_km": None,
        "mileage_since_last_charge_km": None,
    }


def test_decode_uncorrected_current_energy_kwh_ignores_reported_capacity() -> None:
    """Per soh.py's use of this function: unlike decode_battery_usage's current_energy_kwh,
    this must NOT apply the nameplate correction_factor -- a cycle's start/end snapshots can
    each report a different totalBatteryCapacity, and soh.py needs a true delta between two
    readings of the same physical quantity, not two differently-rescaled numbers."""
    raw = _raw({"totalBatteryCapacity": 618, "realtimePower": 3_440})
    # Same raw realtimePower regardless of what totalBatteryCapacity says -- no correction_factor.
    assert decode_uncorrected_current_energy_kwh(raw) == 344.0


def test_decode_uncorrected_current_energy_kwh_out_of_range_is_null() -> None:
    raw = _raw({"realtimePower": 65_536})
    assert decode_uncorrected_current_energy_kwh(raw) is None


def test_decode_uncorrected_current_energy_kwh_missing_rvs_is_null() -> None:
    raw: dict[str, object] = {"charging_management_data": {"rvsChargeStatus": None}}
    assert decode_uncorrected_current_energy_kwh(raw) is None


def test_compute_efficiency_kwh_per_100km() -> None:
    assert compute_efficiency_kwh_per_100km(4.2, 21.3) == 19.72
    assert compute_efficiency_kwh_per_100km(12.6, 143.7) == 8.77


def test_compute_efficiency_kwh_per_100km_null_when_either_input_missing() -> None:
    assert compute_efficiency_kwh_per_100km(None, 21.3) is None
    assert compute_efficiency_kwh_per_100km(4.2, None) is None
    assert compute_efficiency_kwh_per_100km(None, None) is None


def test_compute_efficiency_kwh_per_100km_null_for_zero_or_negative_distance() -> None:
    assert compute_efficiency_kwh_per_100km(4.2, 0) is None
    assert compute_efficiency_kwh_per_100km(4.2, -5.0) is None
