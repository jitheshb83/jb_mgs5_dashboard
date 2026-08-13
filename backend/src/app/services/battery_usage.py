"""Decode GET /api/latest/battery-usage from the stored `raw_json` of the latest snapshot.

Source: `charging_management_data.rvsChargeStatus`, already fetched every refresh as part of
`ChrgMgmtDataResp` -- no extra live SAIC call, no historical storage (decoded on demand at
request time, per docs/architecture/api_contract.md).

Correction-factor technique (scaling the vehicle's self-reported power-usage figures against
our own configured `battery_nameplate_kwh` rather than the vehicle's possibly-inaccurate
self-reported capacity) is taken directly from SAIC-iSmart-API/saic-python-mqtt-gateway's
`src/status_publisher/charge/rvs_charge_status.py` (`get_actual_battery_capacity` method) --
verified by reading that file's source, not guessed. `current_energy_kwh` (from `realtimePower`,
despite the misleading raw field name -- confirmed via that same file's `soc_kwh` computation,
using the identical correction-factor formula) is the battery's current usable energy content,
not a power/rate figure.
"""

from __future__ import annotations

from typing import TypedDict


class BatteryUsageFields(TypedDict):
    total_battery_capacity_kwh: float | None
    power_usage_today_kwh: float | None
    power_usage_since_last_charge_kwh: float | None
    last_charge_added_kwh: float | None
    current_energy_kwh: float | None
    mileage_today_km: float | None
    mileage_since_last_charge_km: float | None


def _in_range(value: object, low: float, high: float) -> bool:
    return isinstance(value, int | float) and low <= value <= high


def decode_battery_usage(
    raw: dict[str, object], battery_nameplate_kwh: float
) -> BatteryUsageFields:
    """Decode battery usage statistics from a parsed `raw_json` dict.

    `raw` is `json.loads(car_snapshot.raw_json)`, i.e.
    `{"vehicle_status": {...}, "charging_management_data": {...}}`.
    """
    charging_management_data = raw.get("charging_management_data")
    rvs: dict[str, object] = {}
    if isinstance(charging_management_data, dict):
        maybe_rvs = charging_management_data.get("rvsChargeStatus")
        if isinstance(maybe_rvs, dict):
            rvs = maybe_rvs

    raw_capacity = rvs.get("totalBatteryCapacity")
    total_battery_capacity_kwh: float | None = None
    correction_factor = 1.0
    if isinstance(raw_capacity, int | float) and raw_capacity > 0:
        total_battery_capacity_kwh = round(raw_capacity / 10.0, 2)
        correction_factor = battery_nameplate_kwh / (raw_capacity / 10.0)

    def _corrected_kwh(raw_value: object) -> float | None:
        if not _in_range(raw_value, 0, 65535):
            return None
        assert isinstance(raw_value, int | float)
        return round((correction_factor * raw_value) / 10.0, 2)

    def _km(raw_value: object) -> float | None:
        if not _in_range(raw_value, 0, 65535):
            return None
        assert isinstance(raw_value, int | float)
        return round(raw_value / 10.0, 1)

    return {
        "total_battery_capacity_kwh": total_battery_capacity_kwh,
        "power_usage_today_kwh": _corrected_kwh(rvs.get("powerUsageOfDay")),
        "power_usage_since_last_charge_kwh": _corrected_kwh(rvs.get("powerUsageSinceLastCharge")),
        "last_charge_added_kwh": _corrected_kwh(rvs.get("lastChargeEndingPower")),
        "current_energy_kwh": _corrected_kwh(rvs.get("realtimePower")),
        "mileage_today_km": _km(rvs.get("mileageOfDay")),
        "mileage_since_last_charge_km": _km(rvs.get("mileageSinceLastCharge")),
    }
