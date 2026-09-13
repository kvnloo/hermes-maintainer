from __future__ import annotations

import json

from hermes_maintainer.config import Settings
from hermes_maintainer.db import Database


def _priority_multiplier(labels: list[str], settings: Settings) -> float:
    if any(x.lower() in {"p0", "priority/p0"} for x in labels):
        return settings.optimizer.p0_multiplier
    if any(x.lower() in {"p1", "priority/p1"} for x in labels):
        return settings.optimizer.p1_multiplier
    if any(x.lower() in {"p2", "priority/p2"} for x in labels):
        return settings.optimizer.p2_multiplier
    return 1.0


def rebuild_pr_atoms(settings: Settings) -> dict[str, int]:
    db = Database(settings.paths.database)
    prs = db.rows(
        "SELECT id,number,title,changed_files,additions,deletions,labels_json,metadata_json FROM nodes "
        "WHERE kind='pr' AND state='open'"
    )
    with db.connect() as conn:
        conn.execute("DELETE FROM fix_atom_coverage")
        conn.execute("DELETE FROM fix_atoms")
    built = 0
    for pr in prs:
        labels = json.loads(pr.get("labels_json") or "[]")
        coverage = db.rows(
            "SELECT dst_id,relation_type,confidence FROM relations WHERE src_id=? AND relation_type IN ('fixes','supersedes')",
            (pr["id"],),
        )
        issue_coverage = [c for c in coverage if c["dst_id"].startswith("issue:")]
        pr_coverage = [c for c in coverage if c["dst_id"].startswith("pr:")]
        value = sum(
            settings.optimizer.issue_weight * _priority_multiplier(labels, settings)
            for _ in issue_coverage
        ) + len(pr_coverage) * settings.optimizer.pr_supersession_weight
        changed_files = pr.get("changed_files") or 0
        lines = (pr.get("additions") or 0) + (pr.get("deletions") or 0)
        cost = 1.0 + changed_files * settings.optimizer.changed_file_penalty + lines * settings.optimizer.changed_line_penalty
        atom_id = f"atom:{pr['number']}:pr"
        with db.connect() as conn:
            conn.execute(
                "INSERT INTO fix_atoms(id,pr_id,title,cost,value,metadata_json) VALUES(?,?,?,?,?,?)",
                (atom_id, pr["id"], pr["title"], cost, value, json.dumps({"labels": labels})),
            )
            for c in coverage:
                conn.execute(
                    "INSERT INTO fix_atom_coverage(atom_id,node_id,coverage_type,confidence) VALUES(?,?,?,?)",
                    (atom_id, c["dst_id"], c["relation_type"], c["confidence"]),
                )
        built += 1
    return {"atoms": built}
