"""Unit tests for the history-derived battery-usage fallback (compute_derived_battery_usage).

Per docs/architecture/api_contract.md's 2026-08-15 correction: this fills whichever fields
the vehicle itself reports as null (decode_battery_usage's job, tested separately in
test_battery_usage.py) using SOC deltas x capacity from `car_snapshot` history.

Timestamps are built relative to `now`'s own local-midnight boundary (not fixed clock
times) so these tests are deterministic regardless of the machine's local timezone --
mirrors exactly the boundary compute_derived_battery_usage itself uses.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.services.battery_usage import SnapshotPoint, compute_derived_battery_usage

NOW = datetime(2026, 8, 15, 12, 0, 0, tzinfo=UTC)
LOCAL_MIDNIGHT = NOW.astimezone().replace(hour=0, minute=0, second=0, microsecond=0)
TODAY = LOCAL_MIDNIGHT + timedelta(hours=6)
YESTERDAY = LOCAL_MIDNIGHT - timedelta(hours=6)
TWO_DAYS_AGO = LOCAL_MIDNIGHT - timedelta(days=1, hours=6)


def test_no_history_returns_all_null() -> None:
    result = compute_derived_battery_usage([], now=NOW, capacity_kwh=62.1)
    assert result == {
        "power_usage_today_kwh": None,
        "power_usage_since_last_charge_kwh": None,
        "last_charge_added_kwh": None,
        "mileage_today_km": None,
        "mileage_since_last_charge_km": None,
    }


def test_power_usage_today_sums_discharge_and_ignores_charge_increases() -> None:
    points = [
        SnapshotPoint(fetched_at=TODAY, soc_pct=80.0, odometer_km=100.0, is_charging=False),
        # Discharge: -10 pct.
        SnapshotPoint(
            fetched_at=TODAY + timedelta(hours=1), soc_pct=70.0, odometer_km=105.0, is_charging=False
        ),
        # A charge bump shouldn't be netted against the discharge above.
        SnapshotPoint(
            fetched_at=TODAY + timedelta(hours=2), soc_pct=90.0, odometer_km=105.0, is_charging=True
        ),
    ]
    result = compute_derived_battery_usage(points, now=NOW, capacity_kwh=62.1)
    # 10 pct of 62.1 kWh = 6.21
    assert result["power_usage_today_kwh"] == 6.21


def test_power_usage_today_zero_when_no_discharge_yet() -> None:
    points = [
        SnapshotPoint(fetched_at=TODAY, soc_pct=68.4, odometer_km=1678.0, is_charging=True),
        SnapshotPoint(
            fetched_at=TODAY + timedelta(hours=1), soc_pct=70.6, odometer_km=1678.0, is_charging=True
        ),
    ]
    result = compute_derived_battery_usage(points, now=NOW, capacity_kwh=62.1)
    assert result["power_usage_today_kwh"] == 0.0


def test_power_usage_today_null_when_no_snapshots_today() -> None:
    points = [
        SnapshotPoint(fetched_at=YESTERDAY, soc_pct=80.0, odometer_km=100.0, is_charging=False),
    ]
    result = compute_derived_battery_usage(points, now=NOW, capacity_kwh=62.1)
    assert result["power_usage_today_kwh"] is None
    assert result["mileage_today_km"] is None


def test_mileage_today_is_odometer_delta_since_local_midnight() -> None:
    points = [
        SnapshotPoint(fetched_at=YESTERDAY, soc_pct=80.0, odometer_km=1660.0, is_charging=False),
        SnapshotPoint(fetched_at=TODAY, soc_pct=75.0, odometer_km=1670.0, is_charging=False),
        SnapshotPoint(
            fetched_at=TODAY + timedelta(hours=1), soc_pct=70.0, odometer_km=1678.0, is_charging=False
        ),
    ]
    result = compute_derived_battery_usage(points, now=NOW, capacity_kwh=62.1)
    assert result["mileage_today_km"] == 8.0


def test_no_completed_charge_cycle_leaves_charge_fields_null() -> None:
    # Matches the real observed DB state (2026-08-15): charging started but hasn't
    # finished within the queried window, so there's no True -> False transition yet.
    points = [
        SnapshotPoint(fetched_at=TWO_DAYS_AGO, soc_pct=54.2, odometer_km=1669.0, is_charging=False),
        SnapshotPoint(fetched_at=YESTERDAY, soc_pct=68.4, odometer_km=1678.0, is_charging=True),
        SnapshotPoint(fetched_at=TODAY, soc_pct=70.6, odometer_km=1678.0, is_charging=True),
    ]
    result = compute_derived_battery_usage(points, now=NOW, capacity_kwh=62.1)
    assert result["last_charge_added_kwh"] is None
    assert result["power_usage_since_last_charge_kwh"] is None
    assert result["mileage_since_last_charge_km"] is None


def test_completed_charge_cycle_computes_added_since_and_mileage() -> None:
    points = [
        # Drove and discharged before the charge.
        SnapshotPoint(fetched_at=TWO_DAYS_AGO, soc_pct=60.0, odometer_km=1600.0, is_charging=False),
        # Charge session: 30 -> 90 pct.
        SnapshotPoint(fetched_at=YESTERDAY, soc_pct=30.0, odometer_km=1650.0, is_charging=True),
        SnapshotPoint(
            fetched_at=YESTERDAY + timedelta(hours=1),
            soc_pct=90.0,
            odometer_km=1650.0,
            is_charging=True,
        ),
        # Charge ends here (True -> False transition below).
        SnapshotPoint(fetched_at=TODAY, soc_pct=90.0, odometer_km=1650.0, is_charging=False),
        # Discharged since the charge ended.
        SnapshotPoint(
            fetched_at=TODAY + timedelta(hours=1), soc_pct=80.0, odometer_km=1670.0, is_charging=False
        ),
    ]
    result = compute_derived_battery_usage(points, now=NOW, capacity_kwh=62.1)
    # 90 - 30 = 60 pct of 62.1 kWh = 37.26
    assert result["last_charge_added_kwh"] == 37.26
    # 90 -> 80 = 10 pct of 62.1 kWh = 6.21
    assert result["power_usage_since_last_charge_kwh"] == 6.21
    # 1670 - 1650 = 20 km, measured from the charge-end snapshot.
    assert result["mileage_since_last_charge_km"] == 20.0


def test_negative_soc_delta_across_charge_cycle_is_not_reported_as_added() -> None:
    # A charge session that ends lower than it started (shouldn't happen, but the
    # function must not report a negative "added" figure) yields null, not garbage.
    points = [
        SnapshotPoint(fetched_at=YESTERDAY, soc_pct=90.0, odometer_km=1650.0, is_charging=True),
        SnapshotPoint(
            fetched_at=YESTERDAY + timedelta(hours=1),
            soc_pct=85.0,
            odometer_km=1650.0,
            is_charging=True,
        ),
        SnapshotPoint(fetched_at=TODAY, soc_pct=85.0, odometer_km=1650.0, is_charging=False),
    ]
    result = compute_derived_battery_usage(points, now=NOW, capacity_kwh=62.1)
    assert result["last_charge_added_kwh"] is None


def test_uses_the_most_recent_completed_cycle_when_several_exist() -> None:
    points = [
        # First completed cycle: 20 -> 60 pct.
        SnapshotPoint(fetched_at=TWO_DAYS_AGO, soc_pct=20.0, odometer_km=1000.0, is_charging=True),
        SnapshotPoint(
            fetched_at=TWO_DAYS_AGO + timedelta(hours=1),
            soc_pct=60.0,
            odometer_km=1000.0,
            is_charging=True,
        ),
        SnapshotPoint(
            fetched_at=TWO_DAYS_AGO + timedelta(hours=2),
            soc_pct=60.0,
            odometer_km=1000.0,
            is_charging=False,
        ),
        # Second, more recent completed cycle: 40 -> 95 pct.
        SnapshotPoint(fetched_at=YESTERDAY, soc_pct=40.0, odometer_km=1050.0, is_charging=True),
        SnapshotPoint(
            fetched_at=YESTERDAY + timedelta(hours=1),
            soc_pct=95.0,
            odometer_km=1050.0,
            is_charging=True,
        ),
        SnapshotPoint(fetched_at=TODAY, soc_pct=95.0, odometer_km=1050.0, is_charging=False),
    ]
    result = compute_derived_battery_usage(points, now=NOW, capacity_kwh=62.1)
    # 95 - 40 = 55 pct of 62.1 kWh = 34.155 -> rounds to 34.16 (not the first cycle's 24.84).
    assert result["last_charge_added_kwh"] == 34.16
