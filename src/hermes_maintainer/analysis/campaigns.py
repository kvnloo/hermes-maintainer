from __future__ import annotations

import hashlib
from collections import defaultdict

from hermes_maintainer.db import Database
from hermes_maintainer.graph.store import GraphStore


def assign_member_roles(
    members: list[dict],
    relations: list[dict],
    canonical_id: str | None,
) -> dict[str, str]:
    by_id = {member["id"]: member for member in members}
    incoming: dict[str, set[str]] = defaultdict(set)
    outgoing: dict[str, set[str]] = defaultdict(set)
    for rel in relations:
        incoming[rel["dst_id"]].add(rel["relation_type"])
        outgoing[rel["src_id"]].add(rel["relation_type"])

    issues = [member for member in members if member["kind"] == "issue"]
    prs = [member for member in members if member["kind"] == "pr"]
    superseded = {member["id"] for member in members if "supersedes" in incoming[member["id"]]}

    canonical_issue = None
    if canonical_id and by_id.get(canonical_id, {}).get("kind") == "issue":
        canonical_issue = canonical_id
    elif issues:
        canonical_issue = max(
            issues,
            key=lambda member: (
                sum(
                    1
                    for rel in relations
                    if rel["dst_id"] == member["id"] and rel["relation_type"] == "fixes"
                ),
                member.get("updated_at") or "",
            ),
        )["id"]

    survivor = None
    open_prs = [
        member
        for member in prs
        if member.get("state") == "open" and member["id"] not in superseded
    ]
    if canonical_id and by_id.get(canonical_id, {}).get("kind") == "pr" and canonical_id not in superseded:
        survivor = canonical_id
    elif open_prs:
        survivor = max(open_prs, key=lambda member: member.get("updated_at") or "")["id"]

    roles: dict[str, str] = {}
    for member in members:
        node_id = member["id"]
        if canonical_issue and node_id == canonical_issue:
            roles[node_id] = "canonical_problem"
        elif survivor and node_id == survivor:
            roles[node_id] = "survivor"
        elif "stacked_on" in outgoing[node_id]:
            roles[node_id] = "stacked_child"
        elif member.get("state") in {"closed", "merged"}:
            roles[node_id] = "provenance"
        elif node_id in superseded:
            roles[node_id] = "superseded"
        elif "incorporates_commit" in outgoing[node_id] or "complements" in outgoing[node_id]:
            roles[node_id] = "donor"
        elif member["kind"] == "pr":
            roles[node_id] = "active_implementation"
        else:
            roles[node_id] = "member"
    return roles


def rebuild_campaigns(db: Database) -> dict[str, int]:
    graph = GraphStore(db)
    open_nodes = [
        r["id"]
        for r in db.rows("SELECT id FROM nodes WHERE state='open' AND kind IN ('issue','pr')")
    ]
    relation_types = {
        "fixes",
        "supersedes",
        "duplicate_of",
        "same_root_cause",
        "possible_duplicate",
        "stacked_on",
        "incorporates_commit",
        "references_pr",
    }
    components = graph.connected_components(open_nodes, relation_types, minimum_confidence=0.77)
    meaningful = [component for component in components if len(component) > 1]
    with db.connect() as conn:
        conn.execute("DELETE FROM campaign_members")
        conn.execute("DELETE FROM campaigns")
        for component in sorted(meaningful, key=lambda item: (-len(item), min(item))):
            digest = hashlib.sha1("|".join(sorted(component)).encode()).hexdigest()[:12]
            campaign_id = f"campaign:{digest}"
            members = db.rows(
                f"SELECT id,kind,number,title,state,updated_at FROM nodes WHERE id IN ({','.join('?' for _ in component)})",
                tuple(component),
            )
            relations = graph.relations_among(component)
            issues = [member for member in members if member["kind"] == "issue"]
            prs = [member for member in members if member["kind"] == "pr"]
            canonical = None
            if prs:
                canonical = max(prs, key=lambda row: row.get("updated_at") or "")
            elif issues:
                canonical = max(issues, key=lambda row: row.get("updated_at") or "")
            title = (canonical or members[0])["title"]
            score = len(issues) * 100 + len(prs) * 15
            conn.execute(
                "INSERT INTO campaigns(id,title,canonical_node_id,score,summary) VALUES(?,?,?,?,?)",
                (
                    campaign_id,
                    title,
                    canonical["id"] if canonical else None,
                    score,
                    f"{len(issues)} issues, {len(prs)} PRs",
                ),
            )
            roles = assign_member_roles(
                members, relations, canonical["id"] if canonical else None
            )
            for member in members:
                conn.execute(
                    "INSERT INTO campaign_members(campaign_id,node_id,role,confidence) VALUES(?,?,?,?)",
                    (campaign_id, member["id"], roles.get(member["id"], "member"), 0.8),
                )
    return {"campaigns": len(meaningful), "members": sum(map(len, meaningful))}
