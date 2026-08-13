"""POST /api/refresh -- see docs/architecture/api_contract.md."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.deps import get_db
from app.api.serializers import parse_fetched_at, row_to_snapshot
from app.config import get_settings
from app.db import repository
from app.models.schemas import ErrorResponse, RefreshResponse
from app.services.rate_limit import should_fetch_live
from app.services.saic_client import SaicClient, SaicClientError

router = APIRouter()


@router.post(
    "/api/refresh",
    response_model=RefreshResponse,
    responses={502: {"model": ErrorResponse}},
)
async def refresh(db: sqlite3.Connection = Depends(get_db)) -> RefreshResponse | JSONResponse:
    settings_raw = repository.get_all_settings(db)
    min_gap_minutes = int(settings_raw.get("min_refresh_gap_minutes", "30"))

    latest_row = repository.get_latest_snapshot(db)
    last_fetched_at = parse_fetched_at(latest_row["fetched_at"]) if latest_row is not None else None
    now = datetime.now(UTC)

    if latest_row is not None and not should_fetch_live(
        last_fetched_at=last_fetched_at, now=now, min_gap_minutes=min_gap_minutes
    ):
        return RefreshResponse(
            source="cached",
            fetched_at=last_fetched_at,  # type: ignore[arg-type]
            snapshot=row_to_snapshot(latest_row),
        )

    app_settings = get_settings()
    client = SaicClient(app_settings)
    try:
        fetched = await client.fetch_snapshot()
    except SaicClientError as exc:
        return JSONResponse(
            status_code=502,
            content=ErrorResponse(error=exc.error, detail=exc.detail).model_dump(),
        )

    row = repository.insert_snapshot(
        db,
        fetched_at=now,
        snapshot_fields=fetched.fields,
        raw_json=fetched.raw_json,
    )
    return RefreshResponse(source="live", fetched_at=now, snapshot=row_to_snapshot(row))
