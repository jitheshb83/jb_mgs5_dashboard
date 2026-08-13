"""GET /api/latest/advanced -- see docs/architecture/api_contract.md.

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
from app.models.schemas import AdvancedInfo, AdvancedResponse, ErrorResponse
from app.services.advanced_info import decode_advanced_info

router = APIRouter()


@router.get(
    "/api/latest/advanced",
    response_model=AdvancedResponse,
    responses={404: {"model": ErrorResponse}},
)
async def latest_advanced(
    db: sqlite3.Connection = Depends(get_db),
) -> AdvancedResponse | JSONResponse:
    row = repository.get_latest_snapshot(db)
    if row is None:
        return no_snapshot_response()
    raw = json.loads(row["raw_json"])
    return AdvancedResponse(
        fetched_at=parse_fetched_at(row["fetched_at"]),
        advanced=AdvancedInfo.model_validate(decode_advanced_info(raw)),
    )
