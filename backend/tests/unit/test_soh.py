"""Unit tests for SOH cycle detection and estimate computation (app.services.soh).

Per docs/planning/soh_methodology.md's 2026-08-15 correction: kWh delivered is the delta in
`current_energy_kwh` (decoded from realtimePower) between a cycle's start and end snapshot,
not derived from the nameplate constant (the originally-documented fallback formula was
circular -- see soh.py's module docstring).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from app.services.soh import SnapshotForSoh, compute_new_soh_estimates, detect_full_charge_cycles

NOW = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)


def _raw(realtime_power: int | None) -> str:
    return json.dumps(
        {
            "charging_management_data": {
                "rvsChargeStatus": {"realtimePower": realtime_power},
            }
        }
    )


def _row(id_: int, soc_pct: float | None, is_charging: bool | None, realtime_power: int | None = 0) -> SnapshotForSoh:
    return SnapshotForSoh(id=id_, soc_pct=soc_pct, is_charging=is_charging, raw_json=_raw(realtime_power))


def test_detects_a_genuine_low_to_full_cycle() -> None:
    rows = [
        _row(1, 20.0, False),
        _row(2, 20.0, True),  # charge start
        _row(3, 60.0, True),
        _row(4, 98.0, True),  # reaches full -> cycle end
        _row(5, 98.0, True),  # still charging (trickle) -- shouldn't start a second cycle
    ]
    cycles = detect_full_charge_cycles(rows)
    assert len(cycles) == 1
    assert cycles[0].start.id == 2
    assert cycles[0].end.id == 4


def test_partial_charge_that_never_reaches_full_is_discarded() -> None:
    rows = [
        _row(1, 40.0, True),
        _row(2, 80.0, True),
        _row(3, 80.0, False),  # stops well below 97% -- partial, discard
    ]
    assert detect_full_charge_cycles(rows) == []


def test_charge_starting_above_low_threshold_is_discarded_even_if_it_reaches_full() -> None:
    # Starts at 45% (not below the 30% low-SOC threshold) -- not a genuine low-to-full cycle.
    rows = [
        _row(1, 45.0, True),
        _row(2, 99.0, True),
    ]
    assert detect_full_charge_cycles(rows) == []


def test_still_mid_charge_with_no_end_point_yet_is_not_a_cycle() -> None:
    # Matches the real observed DB state (2026-08-15): charging, hasn't reached full yet.
    rows = [
        _row(1, 20.0, False),
        _row(2, 68.4, True),
        _row(3, 70.6, True),
    ]
    assert detect_full_charge_cycles(rows) == []


def test_two_consecutive_cycles_are_both_detected() -> None:
    rows = [
        _row(1, 20.0, True),
        _row(2, 98.0, True),  # cycle 1 end
        _row(3, 98.0, False),
        _row(4, 15.0, False),
        _row(5, 15.0, True),
        _row(6, 99.0, True),  # cycle 2 end
    ]
    cycles = detect_full_charge_cycles(rows)
    assert [(c.start.id, c.end.id) for c in cycles] == [(1, 2), (5, 6)]


def test_compute_new_soh_estimates_uses_current_energy_kwh_delta() -> None:
    rows = [
        _row(1, 20.0, True, realtime_power=2_000),  # 200.0 kWh raw -> /10 = 200.0 (contrived scale)
        _row(2, 98.0, True, realtime_power=2_620),  # delta 62.0 over 78 pct
    ]
    estimates = compute_new_soh_estimates(
        rows, already_recorded_end_ids=set(), nameplate_usable_kwh=62.1, now=NOW
    )
    assert len(estimates) == 1
    est = estimates[0]
    assert est.cycle_start_snapshot_id == 1
    assert est.cycle_end_snapshot_id == 2
    # kwh_delivered = 262.0 - 200.0 = 62.0, soc_delta = 78 -> usable_kwh_estimate = 62.0/78*100
    assert est.usable_kwh_estimate == round(62.0 / 78 * 100, 2)
    assert est.soh_pct == round(est.usable_kwh_estimate / 62.1 * 100, 1)
    assert est.basis == "current_energy_kwh_delta"


def test_compute_new_soh_estimates_skips_already_recorded_cycle() -> None:
    rows = [
        _row(1, 20.0, True, realtime_power=2_000),
        _row(2, 98.0, True, realtime_power=2_620),
    ]
    estimates = compute_new_soh_estimates(
        rows, already_recorded_end_ids={2}, nameplate_usable_kwh=62.1, now=NOW
    )
    assert estimates == []


def test_compute_new_soh_estimates_skips_cycle_missing_current_energy_kwh() -> None:
    rows = [
        _row(1, 20.0, True, realtime_power=None),
        _row(2, 98.0, True, realtime_power=2_620),
    ]
    estimates = compute_new_soh_estimates(
        rows, already_recorded_end_ids=set(), nameplate_usable_kwh=62.1, now=NOW
    )
    assert estimates == []


def test_compute_new_soh_estimates_skips_non_positive_kwh_delta() -> None:
    # A charge cycle that somehow ends with less reported energy than it started with --
    # shouldn't happen, but must not be reported as a garbage negative-degradation estimate.
    rows = [
        _row(1, 20.0, True, realtime_power=2_620),
        _row(2, 98.0, True, realtime_power=2_000),
    ]
    estimates = compute_new_soh_estimates(
        rows, already_recorded_end_ids=set(), nameplate_usable_kwh=62.1, now=NOW
    )
    assert estimates == []
