"""Unit tests for advanced_info.py's decode helpers."""

from __future__ import annotations

from app.services.advanced_info import _decode_is_parked


def test_is_parked_none_when_both_signals_missing() -> None:
    assert _decode_is_parked(None, None) is None


def test_is_parked_uses_hand_brake_alone_when_engine_status_missing() -> None:
    # Regression test: engine_status is None must NOT force is_parked to True
    # via Python's `None != 1` evaluating True (the original bug) -- it should
    # fall back to whatever the hand brake alone says.
    assert _decode_is_parked(None, 0) is False  # hand brake off -> not parked
    assert _decode_is_parked(None, 1) is True  # hand brake on -> parked


def test_is_parked_uses_engine_status_alone_when_hand_brake_missing() -> None:
    assert _decode_is_parked(1, None) is False  # engine running -> not parked
    assert _decode_is_parked(0, None) is True  # engine not running -> parked


def test_is_parked_combines_both_signals_when_present() -> None:
    assert _decode_is_parked(1, 0) is False  # running, hand brake off
    assert _decode_is_parked(1, 1) is True  # running but hand brake on
    assert _decode_is_parked(0, 0) is True  # not running, hand brake off
