"""Unit tests for the 30-minute minimum refresh gap gate.

Per docs/planning/testing_strategy.md: boundary cases at exactly 30, 29, and 31
minutes elapsed since the last fetch.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.services.rate_limit import should_fetch_live

NOW = datetime(2026, 8, 12, 14, 30, 0, tzinfo=UTC)


def test_no_prior_snapshot_always_fetches_live() -> None:
    assert should_fetch_live(last_fetched_at=None, now=NOW, min_gap_minutes=30) is True


def test_exactly_30_minutes_elapsed_fetches_live() -> None:
    last = NOW - timedelta(minutes=30)
    assert should_fetch_live(last_fetched_at=last, now=NOW, min_gap_minutes=30) is True


def test_29_minutes_elapsed_returns_cached() -> None:
    last = NOW - timedelta(minutes=29)
    assert should_fetch_live(last_fetched_at=last, now=NOW, min_gap_minutes=30) is False


def test_31_minutes_elapsed_fetches_live() -> None:
    last = NOW - timedelta(minutes=31)
    assert should_fetch_live(last_fetched_at=last, now=NOW, min_gap_minutes=30) is True


def test_zero_minutes_elapsed_returns_cached() -> None:
    assert should_fetch_live(last_fetched_at=NOW, now=NOW, min_gap_minutes=30) is False


def test_respects_configurable_gap_not_hardcoded_30() -> None:
    last = NOW - timedelta(minutes=10)
    assert should_fetch_live(last_fetched_at=last, now=NOW, min_gap_minutes=5) is True
    assert should_fetch_live(last_fetched_at=last, now=NOW, min_gap_minutes=15) is False
