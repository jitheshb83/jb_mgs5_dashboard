"""Derived battery SOH (State of Health) estimate -- see docs/planning/soh_methodology.md.

**2026-08-15 correction to the documented v1 "fallback" method:** as originally written, the
fallback formula (kWh delivered := soc_delta/100 x nameplate_kwh, then usable_kwh_estimate :=
kWh delivered / soc_delta x 100) is circular -- substituting the first into the second cancels
soc_delta out entirely, so usable_kwh_estimate always equals nameplate_kwh exactly and soh_pct
always computes to ~100%, regardless of actual battery condition. Caught before implementation,
not after (see the /api/latest/battery-usage investigation this project did the same day).

This module instead uses the delta in `current_energy_kwh` (decoded from the vehicle's own
`realtimePower` field, confirmed independently vehicle-reported and not derived from our
nameplate constant -- see battery_usage.py) between a cycle's start and end snapshots as the
kWh-delivered figure. This keeps the "v1 simple, SOC-based, not current x voltage x time
integration" spirit of the original fallback while actually being capable of detecting
degradation, since it doesn't bake the nameplate figure into both sides of the equation.
`basis="current_energy_kwh_delta"` on every stored row records which method computed it.

Uses `battery_usage.decode_uncorrected_current_energy_kwh` specifically, not
`decode_battery_usage`'s nameplate-corrected `current_energy_kwh` field: that correction_factor
is recomputed independently per snapshot from *that snapshot's own* self-reported
`totalBatteryCapacity`, so it's not guaranteed identical between a cycle's start and end
snapshot and can't be assumed to cancel out of the delta below.

Cycle detection (soh_methodology.md's Method step 1, unchanged): a full-charge cycle is a
contiguous run of `car_snapshot.is_charging = true` that starts below 30% SOC and reaches at
least 97% SOC (allowing for API rounding/lag) before charging stops or plateaus. Partial charges
(e.g. 40% -> 80%) don't reach 97% and are discarded, not stored. Manual/scheduled refresh means
gaps between snapshots are expected and tolerated -- this scans whatever history exists rather
than assuming continuous data.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime

from app.services.battery_usage import decode_uncorrected_current_energy_kwh

_LOW_SOC_THRESHOLD = 30.0
_FULL_SOC_THRESHOLD = 97.0


@dataclass(frozen=True)
class SnapshotForSoh:
    """The subset of a `car_snapshot` row detect_full_charge_cycles needs."""

    id: int
    soc_pct: float | None
    is_charging: bool | None
    raw_json: str


@dataclass(frozen=True)
class FullChargeCycle:
    start: SnapshotForSoh
    end: SnapshotForSoh


def detect_full_charge_cycles(rows: Sequence[SnapshotForSoh]) -> list[FullChargeCycle]:
    """`rows` must be sorted ascending by fetched_at (id order matches, per get_all_snapshots_ascending)."""
    cycles: list[FullChargeCycle] = []
    run_start: SnapshotForSoh | None = None

    for row in rows:
        if run_start is not None and row.soc_pct is not None and row.soc_pct >= _FULL_SOC_THRESHOLD:
            if run_start.soc_pct is not None and run_start.soc_pct < _LOW_SOC_THRESHOLD:
                cycles.append(FullChargeCycle(start=run_start, end=row))
            run_start = None
            continue
        if row.is_charging is True and run_start is None:
            run_start = row
        elif row.is_charging is False and run_start is not None:
            run_start = None  # Charging stopped before reaching 97% -- partial charge, discard.

    return cycles


def _current_energy_kwh(raw_json: str) -> float | None:
    """The vehicle's raw, uncorrected `realtimePower` reading (see
    battery_usage.decode_uncorrected_current_energy_kwh) -- deliberately *not*
    decode_battery_usage's nameplate-corrected `current_energy_kwh`, whose correction_factor
    is recomputed independently per snapshot and so isn't guaranteed equal at a cycle's start
    vs. end (see this module's top docstring)."""
    return decode_uncorrected_current_energy_kwh(json.loads(raw_json))


@dataclass(frozen=True)
class ComputedSohEstimate:
    computed_at: datetime
    cycle_start_snapshot_id: int
    cycle_end_snapshot_id: int
    soh_pct: float
    usable_kwh_estimate: float
    basis: str


def compute_new_soh_estimates(
    rows: Sequence[SnapshotForSoh],
    *,
    already_recorded_end_ids: set[int],
    nameplate_usable_kwh: float,
    now: datetime,
) -> list[ComputedSohEstimate]:
    """Detects full-charge cycles not already stored and computes a SOH estimate for each.

    Cycles where `current_energy_kwh` isn't available at the start or end snapshot (the
    vehicle didn't report `realtimePower` at that moment) are silently skipped -- there's no
    fallback that wouldn't reintroduce the circularity described in this module's docstring.
    """
    results: list[ComputedSohEstimate] = []
    for cycle in detect_full_charge_cycles(rows):
        if cycle.end.id in already_recorded_end_ids:
            continue
        start_kwh = _current_energy_kwh(cycle.start.raw_json)
        end_kwh = _current_energy_kwh(cycle.end.raw_json)
        if start_kwh is None or end_kwh is None:
            continue
        kwh_delivered = end_kwh - start_kwh
        soc_delta = (cycle.end.soc_pct or 0.0) - (cycle.start.soc_pct or 0.0)
        if kwh_delivered <= 0 or soc_delta <= 0:
            continue

        usable_kwh_estimate = round(kwh_delivered / soc_delta * 100, 2)
        soh_pct = round(usable_kwh_estimate / nameplate_usable_kwh * 100, 1)
        results.append(
            ComputedSohEstimate(
                computed_at=now,
                cycle_start_snapshot_id=cycle.start.id,
                cycle_end_snapshot_id=cycle.end.id,
                soh_pct=soh_pct,
                usable_kwh_estimate=usable_kwh_estimate,
                basis="current_energy_kwh_delta",
            )
        )
    return results
