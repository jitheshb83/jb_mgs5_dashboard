"""Unit test: get_snapshots (backs GET /api/history) and get_latest_snapshot
(backs GET /api/latest) must agree on ordering for rows sharing an identical
fetched_at -- see api_contract.md's GET /api/history ordering note.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.db import repository
from app.db.database import get_connection, init_db


def test_history_and_latest_agree_on_tied_fetched_at(tmp_path: Path) -> None:
    db_path = tmp_path / "ties.db"
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        same_time = "2026-08-12T14:30:00+00:00"
        for soc in (10.0, 20.0, 30.0):
            conn.execute(
                "INSERT INTO car_snapshot (fetched_at, soc_pct, raw_json) VALUES (?, ?, ?)",
                (same_time, soc, "{}"),
            )
        conn.commit()

        latest = repository.get_latest_snapshot(conn)
        assert latest is not None
        assert latest["soc_pct"] == 30.0  # highest id wins the tie

        history = repository.get_snapshots(
            conn,
            from_dt=datetime(2026, 8, 12, tzinfo=UTC),
            to_dt=datetime(2026, 8, 13, tzinfo=UTC),
            limit=10,
        )
        # /api/history's first (most recent) row must be the SAME row
        # /api/latest reports as authoritative for the tied timestamp.
        assert history[0]["soc_pct"] == latest["soc_pct"]
        assert [row["soc_pct"] for row in history] == [30.0, 20.0, 10.0]
    finally:
        conn.close()
