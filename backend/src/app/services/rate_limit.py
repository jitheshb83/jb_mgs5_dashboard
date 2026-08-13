"""Server-side enforcement of the minimum refresh gap (docs/planning/decisions_log.md).

30 minutes, applies to both manual and scheduled refresh triggers.
"""

from __future__ import annotations

from datetime import datetime, timedelta


def should_fetch_live(
    *,
    last_fetched_at: datetime | None,
    now: datetime,
    min_gap_minutes: int,
) -> bool:
    """Decide whether a refresh should call the live SAIC API.

    Returns True (call live) if there is no prior snapshot, or if at least
    `min_gap_minutes` have elapsed since `last_fetched_at`. At exactly the
    boundary (elapsed == min_gap_minutes) the gap is considered to have
    elapsed, so a live call is allowed.
    """
    if last_fetched_at is None:
        return True
    elapsed = now - last_fetched_at
    return elapsed >= timedelta(minutes=min_gap_minutes)
