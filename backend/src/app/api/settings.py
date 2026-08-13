"""GET/PUT /api/settings -- see docs/architecture/api_contract.md."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.deps import get_db
from app.db import repository
from app.models.schemas import ErrorResponse, SettingsResponse, SettingsUpdateRequest
from app.services.settings_validation import validate_schedule_interval

router = APIRouter()


def _to_response(raw: dict[str, str]) -> SettingsResponse:
    return SettingsResponse(
        schedule_enabled=raw["schedule_enabled"].strip().lower() == "true",
        schedule_interval_minutes=int(raw["schedule_interval_minutes"]),
        min_refresh_gap_minutes=int(raw["min_refresh_gap_minutes"]),
        battery_nameplate_kwh=float(raw["battery_nameplate_kwh"]),
    )


@router.get("/api/settings", response_model=SettingsResponse)
async def get_settings_endpoint(db: sqlite3.Connection = Depends(get_db)) -> SettingsResponse:
    return _to_response(repository.get_all_settings(db))


@router.put(
    "/api/settings",
    response_model=SettingsResponse,
    responses={400: {"model": ErrorResponse}},
)
async def update_settings_endpoint(
    payload: SettingsUpdateRequest,
    db: sqlite3.Connection = Depends(get_db),
) -> SettingsResponse | JSONResponse:
    current = _to_response(repository.get_all_settings(db))

    new_schedule_enabled = (
        payload.schedule_enabled if payload.schedule_enabled is not None else current.schedule_enabled
    )
    new_schedule_interval = (
        payload.schedule_interval_minutes
        if payload.schedule_interval_minutes is not None
        else current.schedule_interval_minutes
    )
    new_min_gap = (
        payload.min_refresh_gap_minutes
        if payload.min_refresh_gap_minutes is not None
        else current.min_refresh_gap_minutes
    )
    new_nameplate = (
        payload.battery_nameplate_kwh
        if payload.battery_nameplate_kwh is not None
        else current.battery_nameplate_kwh
    )

    validation_error = validate_schedule_interval(new_schedule_interval, new_min_gap)
    if validation_error is not None:
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                error="schedule_interval_minutes below min_refresh_gap_minutes",
                detail=validation_error,
            ).model_dump(),
        )

    updates = {
        "schedule_enabled": "true" if new_schedule_enabled else "false",
        "schedule_interval_minutes": str(new_schedule_interval),
        "min_refresh_gap_minutes": str(new_min_gap),
        "battery_nameplate_kwh": str(new_nameplate),
    }
    repository.update_settings(db, updates)
    # `updates` already holds the complete written state (all 4 keys) --
    # building the response from it directly avoids a redundant re-SELECT.
    return _to_response(updates)
