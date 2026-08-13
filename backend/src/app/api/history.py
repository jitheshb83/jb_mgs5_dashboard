"""GET /api/history -- see docs/architecture/api_contract.md."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_db
from app.api.serializers import parse_fetched_at, row_to_snapshot
from app.db import repository
from app.models.schemas import HistoryResponse, HistorySnapshot

router = APIRouter()


def _ensure_utc(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


@router.get("/api/history", response_model=HistoryResponse)
async def history(
    db: sqlite3.Connection = Depends(get_db),
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    limit: int = Query(default=500, gt=0),
) -> HistoryResponse:
    now = datetime.now(UTC)
    to_dt = _ensure_utc(to) if to is not None else now
    from_dt = _ensure_utc(from_) if from_ is not None else to_dt - timedelta(days=30)

    rows = repository.get_snapshots(db, from_dt=from_dt, to_dt=to_dt, limit=limit)
    return HistoryResponse(
        snapshots=[
            HistorySnapshot(fetched_at=parse_fetched_at(row["fetched_at"]), snapshot=row_to_snapshot(row))
            for row in rows
        ]
    )
