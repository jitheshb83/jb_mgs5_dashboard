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

`compute_derived_battery_usage` below is a separate, second-line fallback -- see
docs/architecture/api_contract.md's 2026-08-15 correction. This vehicle's account has never
reported the `powerUsageOfDay`/`powerUsageSinceLastCharge`/`lastChargeEndingPower`/
`totalBatteryCapacity` fields `decode_battery_usage` above reads (confirmed null across every
stored snapshot, live-tested against the SAIC API directly), so the API route falls back to
estimating from `car_snapshot` history for whichever fields the vehicle didn't report: a
SOC-delta x capacity estimate, directional not a true energy measurement -- the same *spirit*
as SOH's estimate, but not the same technique SOH actually uses. soh.py's own 2026-08-15
correction found the SOC-delta-against-nameplate formula mathematically circular for SOH's
purposes (start-to-end SOH change) and replaced it with a `current_energy_kwh` delta instead;
that fix doesn't apply here because `compute_derived_battery_usage` isn't estimating capacity
degradation, just a single day's/session's energy delta against whatever capacity figure is
already known -- there's no comparable circularity to it. Still worth remembering these are
two different derived-value systems, not one shared implementation.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from itertools import pairwise
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


def _rvs_charge_status(raw: dict[str, object]) -> dict[str, object]:
    """`raw` is `json.loads(car_snapshot.raw_json)`, i.e.
    `{"vehicle_status": {...}, "charging_management_data": {...}}`."""
    charging_management_data = raw.get("charging_management_data")
    if isinstance(charging_management_data, dict):
        maybe_rvs = charging_management_data.get("rvsChargeStatus")
        if isinstance(maybe_rvs, dict):
            return maybe_rvs
    return {}


def decode_uncorrected_current_energy_kwh(raw: dict[str, object]) -> float | None:
    """`current_energy_kwh` (realtimePower / 10.0) *without* decode_battery_usage's
    correction_factor rescaling.

    Used by soh.py, which needs a delta between two different snapshots' readings of the
    same physical quantity -- decode_battery_usage's correction_factor is recomputed
    independently per snapshot from *that snapshot's own* self-reported totalBatteryCapacity,
    so it is not guaranteed identical at a cycle's start vs. end and must not be relied on to
    cancel out of a delta. Using the raw, unscaled reading at both ends instead keeps the delta
    a true measurement; soh.py rescales the final result against nameplate_usable_kwh itself.
    """
    raw_value = _rvs_charge_status(raw).get("realtimePower")
    if not _in_range(raw_value, 0, 65535):
        return None
    assert isinstance(raw_value, int | float)
    return round(raw_value / 10.0, 2)


def decode_battery_usage(
    raw: dict[str, object], battery_nameplate_kwh: float
) -> BatteryUsageFields:
    """Decode battery usage statistics from a parsed `raw_json` dict."""
    rvs = _rvs_charge_status(raw)

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


@dataclass(frozen=True)
class SnapshotPoint:
    """The subset of a `car_snapshot` row `compute_derived_battery_usage` needs."""

    fetched_at: datetime
    soc_pct: float | None
    odometer_km: float | None
    is_charging: bool | None


class DerivedBatteryUsageFields(TypedDict):
    power_usage_today_kwh: float | None
    power_usage_since_last_charge_kwh: float | None
    last_charge_added_kwh: float | None
    mileage_today_km: float | None
    mileage_since_last_charge_km: float | None


def compute_derived_battery_usage(
    points: Sequence[SnapshotPoint], *, now: datetime, capacity_kwh: float
) -> DerivedBatteryUsageFields:
    """History-derived fallback for whichever fields the vehicle itself reports as null.

    `points` must be sorted ascending by `fetched_at`. See api_contract.md's 2026-08-15
    correction for why this exists and soh_methodology.md for the shared "directional, not
    precise" caveat -- this is a SOC-delta x capacity estimate, not a true energy measurement.
    Returns null for any field it doesn't have enough history to estimate, rather than guessing.
    """
    result: DerivedBatteryUsageFields = {
        "power_usage_today_kwh": None,
        "power_usage_since_last_charge_kwh": None,
        "last_charge_added_kwh": None,
        "mileage_today_km": None,
        "mileage_since_last_charge_km": None,
    }

    local_midnight = now.astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
    soc_points = [p for p in points if p.soc_pct is not None]
    odo_points = [p for p in points if p.odometer_km is not None]

    today_drop_pct = 0.0
    today_seen = False
    for prev, curr in pairwise(soc_points):
        if curr.fetched_at.astimezone() >= local_midnight:
            today_seen = True
            if curr.soc_pct is not None and prev.soc_pct is not None and curr.soc_pct < prev.soc_pct:
                today_drop_pct += prev.soc_pct - curr.soc_pct
    if today_seen:
        result["power_usage_today_kwh"] = round(today_drop_pct / 100 * capacity_kwh, 2)

    today_odo = [p for p in odo_points if p.fetched_at.astimezone() >= local_midnight]
    if today_odo and odo_points and odo_points[-1].odometer_km is not None:
        result["mileage_today_km"] = round(
            odo_points[-1].odometer_km - today_odo[0].odometer_km,  # type: ignore[operator]
            1,
        )

    # Last completed charge *session*: the most recent is_charging True -> False transition,
    # any SOC range. Deliberately broader than soh.py's detect_full_charge_cycles (which
    # requires starting below 30% and reaching >=97% SOC) -- a normal partial top-up is a
    # legitimate "last charge" for everyday usage stats here, even though it's not valid input
    # for a capacity/SOH estimate. The two can disagree on what "the last charge" was; that's
    # intentional, not drift, but is why this doesn't just call soh.detect_full_charge_cycles.
    charging_points = [p for p in points if p.is_charging is not None]
    run_start: SnapshotPoint | None = None
    prev_charging_point: SnapshotPoint | None = None
    last_start: SnapshotPoint | None = None
    last_end: SnapshotPoint | None = None
    for point in charging_points:
        if point.is_charging is True and run_start is None:
            run_start = point
        elif point.is_charging is False and run_start is not None:
            last_start, last_end = run_start, prev_charging_point
            run_start = None
        prev_charging_point = point

    if last_start is not None and last_end is not None:
        if last_start.soc_pct is not None and last_end.soc_pct is not None:
            added_pct = last_end.soc_pct - last_start.soc_pct
            if added_pct > 0:
                result["last_charge_added_kwh"] = round(added_pct / 100 * capacity_kwh, 2)

        since_points = [p for p in soc_points if p.fetched_at >= last_end.fetched_at]
        if since_points:
            since_drop_pct = 0.0
            for prev, curr in pairwise(since_points):
                if curr.soc_pct is not None and prev.soc_pct is not None and curr.soc_pct < prev.soc_pct:
                    since_drop_pct += prev.soc_pct - curr.soc_pct
            result["power_usage_since_last_charge_kwh"] = round(since_drop_pct / 100 * capacity_kwh, 2)

        since_odo = [p for p in odo_points if p.fetched_at >= last_end.fetched_at]
        if since_odo and odo_points[-1].odometer_km is not None:
            result["mileage_since_last_charge_km"] = round(
                odo_points[-1].odometer_km - since_odo[0].odometer_km,  # type: ignore[operator]
                1,
            )

    return result


def compute_efficiency_kwh_per_100km(kwh: float | None, km: float | None) -> float | None:
    """`round(kwh / km * 100, 2)` -- `null` if either input is missing or `km <= 0` (no
    distance travelled, or bad data), which would otherwise divide by zero or yield a
    nonsensical figure. See api_contract.md's 2026-08-16 addition: not vehicle-reported (the
    SAIC API has no consumption/efficiency field), derived from whichever power-usage/mileage
    values the caller already resolved (vehicle-reported or history-derived fallback)."""
    if kwh is None or km is None or km <= 0:
        return None
    return round(kwh / km * 100, 2)
