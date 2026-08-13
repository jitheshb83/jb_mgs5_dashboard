"""GET /api/latest/battery-usage -- see docs/architecture/api_contract.md.

Decoded on demand from the latest snapshot's stored `raw_json` -- no new DB column, no extra
live SAIC call, no historical storage (reflects only the latest snapshot).
"""

from __future__ import annotations

import json
import sqlite3

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.deps import get_db
from app.api.serializers import no_snapshot_response, parse_fetched_at
from app.db import repository
from app.models.schemas import BatteryUsage, BatteryUsageResponse, ErrorResponse
from app.services.battery_usage import decode_battery_usage

router = APIRouter()


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
    return BatteryUsageResponse(
        fetched_at=parse_fetched_at(row["fetched_at"]),
        battery_usage=BatteryUsage.model_validate(
            decode_battery_usage(raw, battery_nameplate_kwh)
        ),
    )
