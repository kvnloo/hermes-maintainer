from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from hermes_maintainer.db import Database

_ROLE_MAP = {
    "minimal_predicate_donor": "donor",
    "overlapping_predicate": "active_implementation",
    "composite_campaign_candidate": "survivor",
}


def _pr_entries(family: dict[str, Any]) -> list[dict[str, Any]]:
    raw = family.get("candidate_prs") or []
    out: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, int):
            out.append({"number": item, "role": None, "notes": ""})
        elif isinstance(item, dict) and item.get("number") is not None:
            out.append(item)
    return out


def seed_campaign_graph(root: Path, family_id: str | None = None) -> dict[str, Any]:
    path = root / "seed" / "audit" / "campaign_seeds.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    families = payload.get("families") or []
    if family_id:
        families = [family for family in families if family.get("id") == family_id]

    nodes: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_issue(number: int, title: str, campaign_id: str, role: str) -> None:
        node_id = f"issue:{number}"
        if node_id in seen:
            return
        seen.add(node_id)
        nodes.append({
            "id": node_id,
            "kind": "issue",
            "number": number,
            "title": title,
            "state": "open",
            "author": "seed",
            "url": f"https://github.com/NousResearch/hermes-agent/issues/{number}",
            "labels": [],
            "role": role,
            "campaign_id": campaign_id,
            "updated_at": None,
        })

    def add_pr(entry: dict[str, Any], campaign_id: str, fallback_role: str, title: str) -> None:
        number = int(entry["number"])
        node_id = f"pr:{number}"
        if node_id in seen:
            return
        seen.add(node_id)
        mapped = _ROLE_MAP.get(entry.get("role") or "", fallback_role)
        nodes.append({
            "id": node_id,
            "kind": "pr",
            "number": number,
            "title": title,
            "state": "open",
            "author": "seed",
            "url": f"https://github.com/NousResearch/hermes-agent/pull/{number}",
            "labels": [],
            "role": mapped,
            "campaign_id": campaign_id,
            "updated_at": None,
            "metadata": {"notes": entry.get("notes") or "", "seed_role": entry.get("role")},
        })

    for family in families:
        campaign_id = f"seed:{family['id']}"
        title = family.get("id", "seed-family").replace("-", " ")
        canonical = family.get("canonical_issue")
        related = family.get("related_issues") or []
        prs = _pr_entries(family)
        survivor = family.get("recorded_survivor")
        if canonical:
            add_issue(int(canonical), f"{title} (canonical)", campaign_id, "canonical_problem")
        for issue_number in related:
            role = "canonical_problem" if not canonical else "member"
            add_issue(int(issue_number), f"{title} related", campaign_id, role)
            if canonical:
                relations.append({
                    "src_id": f"issue:{issue_number}",
                    "dst_id": f"issue:{canonical}",
                    "relation_type": "same_root_cause",
                    "confidence": 0.72,
                    "evidence_level": family.get("evidence_level") or "reported",
                    "evidence": "seed related issue",
                    "source": "seed",
                })
        for index, entry in enumerate(prs):
            fallback = "survivor" if (survivor and entry["number"] == survivor) or (
                survivor is None and index == 0
            ) else "active_implementation"
            add_pr(entry, campaign_id, fallback, f"{title} candidate")
            target = canonical or (related[0] if related else None)
            if target:
                relations.append({
                    "src_id": f"pr:{entry['number']}",
                    "dst_id": f"issue:{target}",
                    "relation_type": "fixes",
                    "confidence": 0.8 if index == 0 else 0.64,
                    "evidence_level": family.get("evidence_level") or "reported",
                    "evidence": family.get("proposal") or "seed candidate",
                    "source": "seed",
                })
            if survivor and entry["number"] != survivor:
                relations.append({
                    "src_id": f"pr:{survivor}",
                    "dst_id": f"pr:{entry['number']}",
                    "relation_type": "supersedes",
                    "confidence": 0.6,
                    "evidence_level": "reported",
                    "evidence": "recorded survivor in audit seed",
                    "source": "seed",
                })

    campaign = None
    if len(families) == 1:
        family = families[0]
        campaign = {
            "id": f"seed:{family['id']}",
            "title": family.get("id"),
            "summary": family.get("proposal") or family.get("invariant") or "",
            "score": len(nodes),
            "status": "seed",
        }
    return {
        "campaign": campaign,
        "nodes": nodes,
        "relations": relations,
        "source": "seed",
        "families": [family.get("id") for family in families],
    }

def _seed_families(root: Path) -> list[str]:
    path = root / "seed" / "audit" / "campaign_seeds.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return [family["id"] for family in payload.get("families") or [] if family.get("id")]


def import_seed_graph(db: Database, root: Path, repo: str = "NousResearch/hermes-agent") -> dict:
    """Load the audit seed campaigns into the live graph so a fresh install has data.

    Idempotent: nodes/relations upsert and seed campaigns are replaced. Seed nodes carry
    ``metadata.seed = true``; a real scan overwrites them with live GitHub state, and
    ``analyze`` rebuilds campaigns from live relations.
    """
    db.initialize()
    node_ids: set[str] = set()
    relation_keys: set[tuple[str, str, str]] = set()
    campaigns = 0
    for family_id in _seed_families(root):
        graph = seed_campaign_graph(root, family_id)
        campaign = graph["campaign"]
        for node in graph["nodes"]:
            metadata = {**(node.get("metadata") or {}), "seed": True, "seed_family": family_id}
            db.upsert_node({
                "id": node["id"], "repo": repo, "kind": node["kind"], "number": node["number"],
                "title": node["title"], "body": metadata.get("notes", ""), "state": node["state"],
                "author": node["author"], "url": node["url"], "labels_json": "[]", "draft": 0,
                "metadata_json": json.dumps(metadata),
            })
            node_ids.add(node["id"])
        for rel in graph["relations"]:
            db.add_relation(
                rel["src_id"], rel["dst_id"], rel["relation_type"],
                confidence=rel["confidence"], evidence_level=rel["evidence_level"],
                evidence=rel["evidence"], source="seed",
            )
            relation_keys.add((rel["src_id"], rel["dst_id"], rel["relation_type"]))
        with db.connect() as conn:
            conn.execute("DELETE FROM campaigns WHERE id=?", (campaign["id"],))
            conn.execute(
                "INSERT INTO campaigns(id,title,status,score,summary) VALUES(?,?,?,?,?)",
                (campaign["id"], campaign["title"], "seed", campaign["score"], campaign["summary"]),
            )
            for node in graph["nodes"]:
                conn.execute(
                    "INSERT OR REPLACE INTO campaign_members(campaign_id,node_id,role,confidence) "
                    "VALUES(?,?,?,?)",
                    (campaign["id"], node["id"], node.get("role") or "member", 0.5),
                )
        campaigns += 1
    return {"nodes": len(node_ids), "relations": len(relation_keys), "campaigns": campaigns}
