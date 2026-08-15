"""GET /api/soh -- see docs/architecture/api_contract.md and docs/planning/soh_methodology.md.

Read-only: new estimates are detected and persisted at refresh time (see
app.api.refresh._record_soh_estimates_if_any), not computed here. This route just reads what's
already stored in `soh_estimate`.
"""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends

from app.api.deps import get_db
from app.api.serializers import parse_fetched_at
from app.db import repository
from app.models.schemas import SohEstimateItem, SohResponse

router = APIRouter()


@router.get("/api/soh", response_model=SohResponse)
async def soh(db: sqlite3.Connection = Depends(get_db)) -> SohResponse:
    settings_raw = repository.get_all_settings(db)
    nameplate_usable_kwh = float(settings_raw.get("battery_nameplate_kwh", "62.1"))
    rows = repository.get_soh_estimates(db)
    return SohResponse(
        estimates=[
            SohEstimateItem(
                computed_at=parse_fetched_at(row["computed_at"]),
                soh_pct=row["soh_pct"],
                usable_kwh_estimate=row["usable_kwh_estimate"],
                basis=row["basis"],
            )
            for row in rows
        ],
        nameplate_usable_kwh=nameplate_usable_kwh,
    )
