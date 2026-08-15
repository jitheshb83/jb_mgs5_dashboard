"""POST /api/refresh -- see docs/architecture/api_contract.md."""

from __future__ import annotations

import logging
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
from app.services.soh import SnapshotForSoh, compute_new_soh_estimates

router = APIRouter()
logger = logging.getLogger(__name__)


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
    # The snapshot above is already committed -- a bug in SOH detection must not turn this
    # successful, already-persisted refresh into a client-visible failure (see api_contract.md's
    # 2026-08-15 correction's code-review follow-up).
    try:
        _record_soh_estimates_if_any(db, settings_raw=settings_raw, now=now)
    except Exception:
        logger.exception("SOH estimate detection failed after a successful refresh")
    return RefreshResponse(source="live", fetched_at=now, snapshot=row_to_snapshot(row))


def _record_soh_estimates_if_any(
    db: sqlite3.Connection, *, settings_raw: dict[str, str], now: datetime
) -> None:
    """Detects and persists any newly-completed full-charge cycles -- see
    docs/planning/soh_methodology.md. Runs on every live refresh (not on cache hits, since
    those write no new snapshot and so can't complete a new cycle).
    """
    nameplate_usable_kwh = float(settings_raw.get("battery_nameplate_kwh", "62.1"))
    rows = [
        SnapshotForSoh(
            id=r["id"],
            soc_pct=r["soc_pct"],
            is_charging=bool(r["is_charging"]) if r["is_charging"] is not None else None,
            raw_json=r["raw_json"],
        )
        for r in repository.get_all_snapshots_ascending(db)
    ]
    already_recorded = repository.get_existing_soh_cycle_end_ids(db)
    for estimate in compute_new_soh_estimates(
        rows,
        already_recorded_end_ids=already_recorded,
        nameplate_usable_kwh=nameplate_usable_kwh,
        now=now,
    ):
        repository.insert_soh_estimate(
            db,
            computed_at=estimate.computed_at,
            cycle_start_snapshot_id=estimate.cycle_start_snapshot_id,
            cycle_end_snapshot_id=estimate.cycle_end_snapshot_id,
            soh_pct=estimate.soh_pct,
            usable_kwh_estimate=estimate.usable_kwh_estimate,
            basis=estimate.basis,
        )
