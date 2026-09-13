from __future__ import annotations

from collections import Counter

from hermes_maintainer.analysis.similarity import tokens
from hermes_maintainer.db import Database


def recurring_mechanisms(db: Database, limit: int = 50) -> list[dict]:
    rows = db.rows("SELECT id,title,body FROM nodes WHERE state='open' AND kind='issue'")
    phrases = Counter()
    examples: dict[str, list[str]] = {}
    mechanism_terms = {
        "lock", "race", "retry", "backoff", "timeout", "cache", "stale", "leak", "permission",
        "oauth", "sqlite", "wal", "deadlock", "poll", "queue", "duplicate", "profile", "session",
        "windows", "sandbox", "credential", "refresh", "reconnect", "corrupt", "atomic",
    }
    for row in rows:
        ts = set(tokens((row.get("title") or "") + " " + (row.get("body") or "")))
        for term in mechanism_terms & ts:
            phrases[term] += 1
            examples.setdefault(term, []).append(row["id"])
    return [
        {"mechanism": term, "open_issue_count": count, "examples": examples[term][:8]}
        for term, count in phrases.most_common(limit)
    ]
