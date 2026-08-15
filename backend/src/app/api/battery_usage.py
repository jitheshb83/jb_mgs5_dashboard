"""GET /api/latest/battery-usage -- see docs/architecture/api_contract.md.

Primarily decoded on demand from the latest snapshot's stored `raw_json`. Per the
2026-08-15 contract correction, whichever fields the vehicle itself reports as null fall back
to an estimate derived from `car_snapshot` history (last 30 days, same window as
`/api/history`) -- see `app.services.battery_usage.compute_derived_battery_usage`.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.deps import get_db
from app.api.serializers import no_snapshot_response, parse_fetched_at
from app.db import repository
from app.models.schemas import BatteryUsage, BatteryUsageResponse, ErrorResponse
from app.services.battery_usage import (
    SnapshotPoint,
    compute_derived_battery_usage,
    compute_efficiency_kwh_per_100km,
    decode_battery_usage,
)

router = APIRouter()

_DERIVABLE_FIELDS = (
    "power_usage_today_kwh",
    "power_usage_since_last_charge_kwh",
    "last_charge_added_kwh",
    "mileage_today_km",
    "mileage_since_last_charge_km",
)

# get_snapshots orders DESC then applies this limit before the route reverses to ascending --
# a small limit would silently drop the *oldest* rows of the documented 30-day window (not the
# newest), understating usage/mileage or losing the last-charge boundary if that window ever
# holds more rows than the limit. Generously large (rather than unbounded like
# get_all_snapshots_ascending) so a pathological refresh cadence still can't make a single
# request scan an unbounded amount of history -- 43_200 rows is a refresh every minute for the
# full 30 days, comfortably above anything this manual/scheduled-refresh app can produce.
_HISTORY_WINDOW_LIMIT = 50_000


@router.get(
    "/api/latest/battery-usage",
    response_model=BatteryUsageResponse,
    responses={404: {"model": ErrorResponse}},
)
async def latest_battery_usage(
    db: sqlite3.Connection = Depends(get_db),
) -> BatteryUsageResponse | JSONResponse:
    row = repository.get_latest_snapshot(db)
    if row is None:
        return no_snapshot_response()
    raw = json.loads(row["raw_json"])
    settings_raw = repository.get_all_settings(db)
    battery_nameplate_kwh = float(settings_raw.get("battery_nameplate_kwh", "62.1"))
    fields = decode_battery_usage(raw, battery_nameplate_kwh)

    estimated_fields: list[str] = []
    capacity_kwh = fields["total_battery_capacity_kwh"]
    if capacity_kwh is None:
        capacity_kwh = battery_nameplate_kwh
        fields["total_battery_capacity_kwh"] = capacity_kwh
        estimated_fields.append("total_battery_capacity_kwh")

    missing = [name for name in _DERIVABLE_FIELDS if fields[name] is None]  # type: ignore[literal-required]
    if missing:
        now = datetime.now(UTC)
        history_rows = repository.get_snapshots(
            db, from_dt=now - timedelta(days=30), to_dt=now, limit=_HISTORY_WINDOW_LIMIT
        )
        points = [
            SnapshotPoint(
                fetched_at=_ensure_utc(datetime.fromisoformat(r["fetched_at"])),
                soc_pct=r["soc_pct"],
                odometer_km=r["odometer_km"],
                is_charging=bool(r["is_charging"]) if r["is_charging"] is not None else None,
            )
            for r in reversed(history_rows)  # get_snapshots returns DESC; derivation needs ASC
        ]
        derived = compute_derived_battery_usage(points, now=now, capacity_kwh=capacity_kwh)
        for name in missing:
            derived_value = derived[name]  # type: ignore[literal-required]
            if derived_value is not None:
                fields[name] = derived_value  # type: ignore[literal-required]
                estimated_fields.append(name)

    efficiency_today = compute_efficiency_kwh_per_100km(
        fields["power_usage_today_kwh"], fields["mileage_today_km"]
    )
    if efficiency_today is not None and (
        "power_usage_today_kwh" in estimated_fields or "mileage_today_km" in estimated_fields
    ):
        estimated_fields.append("efficiency_today_kwh_per_100km")

    efficiency_since_last_charge = compute_efficiency_kwh_per_100km(
        fields["power_usage_since_last_charge_kwh"], fields["mileage_since_last_charge_km"]
    )
    if efficiency_since_last_charge is not None and (
        "power_usage_since_last_charge_kwh" in estimated_fields
        or "mileage_since_last_charge_km" in estimated_fields
    ):
        estimated_fields.append("efficiency_since_last_charge_kwh_per_100km")

    return BatteryUsageResponse(
        fetched_at=parse_fetched_at(row["fetched_at"]),
        battery_usage=BatteryUsage.model_validate(
            {
                **fields,
                "efficiency_today_kwh_per_100km": efficiency_today,
                "efficiency_since_last_charge_kwh_per_100km": efficiency_since_last_charge,
                "estimated_fields": estimated_fields,
            }
        ),
    )


def _ensure_utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)
