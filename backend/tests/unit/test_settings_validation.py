"""Unit tests for PUT /api/settings validation logic.

Per docs/planning/testing_strategy.md: rejects invalid values, e.g. schedule
interval below the minimum refresh gap.
"""

from __future__ import annotations

from app.services.settings_validation import validate_schedule_interval


def test_interval_equal_to_min_gap_is_valid() -> None:
    assert validate_schedule_interval(30, 30) is None


def test_interval_above_min_gap_is_valid() -> None:
    assert validate_schedule_interval(120, 30) is None


def test_interval_below_min_gap_is_rejected() -> None:
    error = validate_schedule_interval(20, 30)
    assert error is not None
    assert "20" in error
    assert "30" in error
