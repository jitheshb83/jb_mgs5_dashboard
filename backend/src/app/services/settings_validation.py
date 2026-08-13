"""Validation rules for PUT /api/settings (docs/architecture/api_contract.md)."""

from __future__ import annotations


def validate_schedule_interval(
    schedule_interval_minutes: int, min_refresh_gap_minutes: int
) -> str | None:
    """Return an error detail message if invalid, else None.

    Per the contract, schedule_interval_minutes must not be below
    min_refresh_gap_minutes.
    """
    if schedule_interval_minutes < min_refresh_gap_minutes:
        return (
            f"schedule_interval_minutes ({schedule_interval_minutes}) must be >= "
            f"min_refresh_gap_minutes ({min_refresh_gap_minutes})."
        )
    return None
