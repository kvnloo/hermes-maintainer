from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hermes_maintainer.db import Database


def snapshot_metrics(db: Database) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for kind in ("issue", "pr"):
        metrics[f"open_{kind}s"] = float(db.scalar(
            "SELECT COUNT(*) FROM nodes WHERE kind=? AND state='open'", (kind,)
        ) or 0)
    metrics["relations"] = float(db.scalar("SELECT COUNT(*) FROM relations") or 0)
    metrics["campaigns"] = float(db.scalar("SELECT COUNT(*) FROM campaigns") or 0)
    metrics["fix_atoms"] = float(db.scalar("SELECT COUNT(*) FROM fix_atoms") or 0)
    metrics["duplicate_labeled_open"] = float(db.scalar(
        "SELECT COUNT(*) FROM nodes WHERE state='open' AND labels_json LIKE '%duplicate%'"
    ) or 0)
    cutoff = (datetime.now(UTC) - timedelta(days=30)).isoformat()
    metrics["stale_open_30d"] = float(db.scalar(
        "SELECT COUNT(*) FROM nodes WHERE state='open' AND kind IN ('issue','pr') AND COALESCE(updated_at,'')<?",
        (cutoff,),
    ) or 0)
    with db.connect() as conn:
        for metric, value in metrics.items():
            conn.execute("INSERT INTO metrics(metric,value) VALUES(?,?)", (metric, value))
    return metrics
