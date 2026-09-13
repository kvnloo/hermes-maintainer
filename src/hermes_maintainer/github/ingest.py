from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime

from hermes_maintainer.config import Settings
from hermes_maintainer.db import Database
from hermes_maintainer.github.client import GitHubClient
from hermes_maintainer.github.normalize import explicit_references, issue_node, pr_node


def _start_run(db: Database, mode: str) -> int:
    with db.connect() as conn:
        cur = conn.execute("INSERT INTO sync_runs(mode) VALUES(?)", (mode,))
        return int(cur.lastrowid)


def _finish_run(db: Database, run_id: int, status: str, notes: str = "") -> None:
    with db.connect() as conn:
        conn.execute(
            "UPDATE sync_runs SET finished_at=?, status=?, notes=? WHERE id=?",
            (datetime.now(UTC).isoformat(), status, notes, run_id),
        )


def _materialize_explicit_relations(db: Database, node_id: str, body: str) -> None:
    kind = node_id.split(":", 1)[0]
    for relation, number, confidence, evidence in explicit_references(body):
        target_kind = "pr" if relation == "references_pr" else "issue"
        if relation == "supersedes" and kind == "pr":
            target_kind = "pr"
        if relation in {"references", "related"}:
            # Ambiguous #N references are resolved issue-first and repaired later if needed.
            target_kind = "issue"
        target_id = f"{target_kind}:{number}"
        if db.scalar("SELECT 1 FROM nodes WHERE id=?", (target_id,)):
            db.add_relation(
                node_id,
                target_id,
                relation,
                confidence=confidence,
                evidence_level="reported",
                evidence=evidence,
                source="body_parser",
            )


def fast_scan(settings: Settings) -> dict[str, int]:
    db = Database(settings.paths.database)
    db.initialize()
    run_id = _start_run(db, "fast")
    client = GitHubClient(settings.github_token)
    counts = {"issues": 0, "prs": 0}
    try:
        for item in client.iter_issues(
            settings.repo.name, max_pages=settings.scan.issue_pages_per_fast_scan
        ):
            db.upsert_node(issue_node(settings.repo.name, item, run_id))
            counts["issues"] += 1
        for item in client.iter_pulls(
            settings.repo.name, max_pages=settings.scan.pr_pages_per_fast_scan
        ):
            db.upsert_node(pr_node(settings.repo.name, item, run_id))
            counts["prs"] += 1

        # Second pass so references can resolve to nodes ingested later in the scan.
        for row in db.rows("SELECT id, body FROM nodes WHERE last_seen_run=? AND kind IN ('issue','pr')", (run_id,)):
            _materialize_explicit_relations(db, row["id"], row.get("body") or "")
        _finish_run(db, run_id, "ok", json.dumps(counts))
        return counts
    except Exception as exc:
        _finish_run(db, run_id, "error", repr(exc))
        raise
    finally:
        client.close()


def deep_enrich_prs(settings: Settings, limit: int | None = None) -> dict[str, int]:
    db = Database(settings.paths.database)
    db.initialize()
    run_id = _start_run(db, "deep")
    client = GitHubClient(settings.github_token)
    limit = limit or settings.scan.max_deep_prs_per_scan
    rows = db.rows(
        """
        SELECT number FROM nodes
        WHERE kind='pr' AND state='open'
        ORDER BY COALESCE(updated_at,'') DESC
        LIMIT ?
        """,
        (limit,),
    )
    counts = {"prs": 0, "files": 0, "commits": 0}
    try:
        for row in rows:
            number = int(row["number"])
            detail = client.get_pull(settings.repo.name, number)
            db.upsert_node(pr_node(settings.repo.name, detail, run_id))
            pr_id = f"pr:{number}"
            files = client.get_pull_files(settings.repo.name, number)
            with db.connect() as conn:
                conn.execute("DELETE FROM pr_files WHERE pr_id=?", (pr_id,))
                for f in files:
                    patch = f.get("patch") or ""
                    conn.execute(
                        """
                        INSERT INTO pr_files(pr_id,path,status,additions,deletions,changes,patch_sha256)
                        VALUES(?,?,?,?,?,?,?)
                        """,
                        (
                            pr_id, f["filename"], f.get("status"), f.get("additions", 0),
                            f.get("deletions", 0), f.get("changes", 0),
                            hashlib.sha256(patch.encode()).hexdigest() if patch else None,
                        ),
                    )
            commits = client.get_pull_commits(settings.repo.name, number)
            with db.connect() as conn:
                conn.execute("DELETE FROM pr_commits WHERE pr_id=?", (pr_id,))
                for idx, c in enumerate(commits):
                    conn.execute(
                        "INSERT INTO pr_commits(pr_id,commit_sha,ordinal,message) VALUES(?,?,?,?)",
                        (pr_id, c["sha"], idx, (c.get("commit") or {}).get("message")),
                    )
            counts["prs"] += 1
            counts["files"] += len(files)
            counts["commits"] += len(commits)
        _finish_run(db, run_id, "ok", json.dumps(counts))
        return counts
    except Exception as exc:
        _finish_run(db, run_id, "error", repr(exc))
        raise
    finally:
        client.close()
