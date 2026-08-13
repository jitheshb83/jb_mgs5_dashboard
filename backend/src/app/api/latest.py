"""GET /api/latest -- see docs/architecture/api_contract.md."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.api.deps import get_db
from app.api.serializers import no_snapshot_response, parse_fetched_at, row_to_snapshot
from app.db import repository
from app.models.schemas import ErrorResponse, LatestResponse

router = APIRouter()


@router.get(
    "/api/latest",
    response_model=LatestResponse,
    responses={404: {"model": ErrorResponse}},
)
async def latest(db: sqlite3.Connection = Depends(get_db)) -> LatestResponse | JSONResponse:
    row = repository.get_latest_snapshot(db)
    if row is None:
        return no_snapshot_response()
    return LatestResponse(
        fetched_at=parse_fetched_at(row["fetched_at"]),
        snapshot=row_to_snapshot(row),
    )
