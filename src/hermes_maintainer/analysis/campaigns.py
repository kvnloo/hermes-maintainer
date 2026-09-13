from __future__ import annotations

import hashlib

from hermes_maintainer.db import Database
from hermes_maintainer.graph.store import GraphStore


def rebuild_campaigns(db: Database) -> dict[str, int]:
    graph = GraphStore(db)
    open_nodes = [r["id"] for r in db.rows(
        "SELECT id FROM nodes WHERE state='open' AND kind IN ('issue','pr')"
    )]
    relation_types = {
        "fixes", "supersedes", "duplicate_of", "same_root_cause", "possible_duplicate",
        "stacked_on", "incorporates_commit", "references_pr",
    }
    components = graph.connected_components(open_nodes, relation_types, minimum_confidence=0.77)
    meaningful = [c for c in components if len(c) > 1]
    with db.connect() as conn:
        conn.execute("DELETE FROM campaign_members")
        conn.execute("DELETE FROM campaigns")
        for component in sorted(meaningful, key=lambda x: (-len(x), sorted(x)[0])):
            digest = hashlib.sha1("|".join(sorted(component)).encode()).hexdigest()[:12]
            campaign_id = f"campaign:{digest}"
            members = db.rows(
                f"SELECT id,kind,number,title,state,updated_at FROM nodes WHERE id IN ({','.join('?' for _ in component)})",
                tuple(component),
            )
            issues = [m for m in members if m["kind"] == "issue"]
            prs = [m for m in members if m["kind"] == "pr"]
            canonical = None
            if prs:
                canonical = sorted(prs, key=lambda r: r.get("updated_at") or "", reverse=True)[0]
            elif issues:
                canonical = sorted(issues, key=lambda r: r.get("updated_at") or "", reverse=True)[0]
            title = (canonical or members[0])["title"]
            score = len(issues) * 100 + len(prs) * 15
            conn.execute(
                "INSERT INTO campaigns(id,title,canonical_node_id,score,summary) VALUES(?,?,?,?,?)",
                (campaign_id, title, canonical["id"] if canonical else None, score,
                 f"{len(issues)} issues, {len(prs)} PRs"),
            )
            for member in members:
                role = "canonical" if canonical and member["id"] == canonical["id"] else "member"
                conn.execute(
                    "INSERT INTO campaign_members(campaign_id,node_id,role,confidence) VALUES(?,?,?,?)",
                    (campaign_id, member["id"], role, 0.8),
                )
    return {"campaigns": len(meaningful), "members": sum(map(len, meaningful))}
