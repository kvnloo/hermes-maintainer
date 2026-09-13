from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict, deque
from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from hermes_maintainer.db import Database

STRONG_RELATIONS = {
    "fixes",
    "supersedes",
    "duplicate_of",
    "same_root_cause",
    "incorporates_commit",
    "stacked_on",
    "verified_fixed_on",
}

ALLOWED_KINDS = {"issue", "pr", "commit", "file", "campaign", "fix_atom"}
ALLOWED_STATES = {"open", "closed", "merged", "draft"}

PRIORITY_ALIASES = {
    "p0": ("p0", "priority/p0", "priority:p0"),
    "p1": ("p1", "priority/p1", "priority:p1"),
    "p2": ("p2", "priority/p2", "priority:p2"),
    "p3": ("p3", "priority/p3", "priority:p3"),
}

BLOCKER_LABELS = {
    "needs-repro",
    "needs_repro",
    "blocked",
    "blocker",
    "needs-maintainer",
    "needs-decision",
    "needs-platform",
    "waiting-for-maintainer",
    "needs-evidence",
}

_FTS_TOKEN = re.compile(r"[A-Za-z0-9_./:+-]+")


def parse_labels(raw: object) -> list[str]:
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return []
    return [str(x) for x in parsed] if isinstance(parsed, list) else []


def parse_metadata(raw: object) -> dict:
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def fts_query(q: str) -> str:
    parts = [t for t in _FTS_TOKEN.findall(q or "") if t]
    if not parts:
        return '""'
    return " OR ".join('"' + p.replace('"', "") + '"' for p in parts)


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _in_clause(ids: list[str]) -> tuple[str, tuple[str, ...]]:
    return ",".join("?" for _ in ids), tuple(ids)


class GraphStore:
    def __init__(self, db: Database):
        self.db = db

    def neighbors(self, node_id: str, relation_types: set[str] | None = None) -> list[dict]:
        params: list[object] = [node_id, node_id]
        predicate = ""
        if relation_types:
            qs = ",".join("?" for _ in relation_types)
            predicate = f" AND relation_type IN ({qs})"
            params.extend(sorted(relation_types))
        return self.db.rows(
            f"""
            SELECT * FROM relations
            WHERE (src_id=? OR dst_id=?){predicate}
            ORDER BY confidence DESC
            """,
            tuple(params),
        )

    def connected_components(
        self,
        node_ids: Iterable[str],
        relation_types: set[str] | None = None,
        minimum_confidence: float = 0.75,
    ) -> list[set[str]]:
        relation_types = relation_types or STRONG_RELATIONS
        rows = self.db.rows(
            "SELECT src_id,dst_id,relation_type,confidence FROM relations WHERE confidence>=?",
            (minimum_confidence,),
        )
        adjacency: dict[str, set[str]] = defaultdict(set)
        allowed = set(relation_types)
        nodes = set(node_ids)
        for row in rows:
            if row["relation_type"] not in allowed:
                continue
            a, b = row["src_id"], row["dst_id"]
            if a in nodes and b in nodes:
                adjacency[a].add(b)
                adjacency[b].add(a)

        seen: set[str] = set()
        out: list[set[str]] = []
        for start in nodes:
            if start in seen:
                continue
            component: set[str] = set()
            queue = deque([start])
            seen.add(start)
            while queue:
                cur = queue.popleft()
                component.add(cur)
                for nxt in adjacency[cur]:
                    if nxt not in seen:
                        seen.add(nxt)
                        queue.append(nxt)
            out.append(component)
        return out

    def relations_among(self, node_ids: Iterable[str]) -> list[dict]:
        ids = list(node_ids)
        if not ids:
            return []
        qs, params = _in_clause(ids)
        return self.db.rows(
            f"""
            SELECT * FROM relations
            WHERE src_id IN ({qs}) AND dst_id IN ({qs})
            ORDER BY confidence DESC
            """,
            params + params,
        )

    def _prefer_connected(self, candidate_ids: list[str], limit: int) -> list[str]:
        if len(candidate_ids) <= limit:
            return candidate_ids
        relations = self.relations_among(candidate_ids)
        parent = {node_id: node_id for node_id in candidate_ids}

        def find(node_id: str) -> str:
            while parent[node_id] != node_id:
                parent[node_id] = parent[parent[node_id]]
                node_id = parent[node_id]
            return node_id

        def union(left: str, right: str) -> None:
            root_left, root_right = find(left), find(right)
            if root_left != root_right:
                parent[root_right] = root_left

        for rel in relations:
            src, dst = rel["src_id"], rel["dst_id"]
            if src in parent and dst in parent:
                union(src, dst)

        groups: dict[str, list[str]] = defaultdict(list)
        for node_id in candidate_ids:
            groups[find(node_id)].append(node_id)
        ranked = sorted(groups.values(), key=lambda group: (-len(group), group[0]))
        filled: list[str] = []
        for group in ranked:
            for node_id in group:
                filled.append(node_id)
                if len(filled) >= limit:
                    return filled
        return filled

    def export_json(self, **filters) -> dict:
        return self.export_subgraph(**filters)

    def export_subgraph(
        self,
        *,
        campaign_id: str | None = None,
        kind: str | None = None,
        state: str | None = None,
        priority: str | None = None,
        component: str | None = None,
        blocker: str | None = None,
        updated_within_days: int | None = None,
        stale_days: int | None = None,
        evidence_level: str | None = None,
        q: str | None = None,
        scope: str = "campaign",
        limit: int = 250,
    ) -> dict:
        campaign = None
        role_map: dict[str, str] = {}
        candidate_ids: list[str] = []

        if not campaign_id and scope == "campaign":
            top = self.db.rows("SELECT id FROM campaigns ORDER BY score DESC LIMIT 1")
            if top:
                campaign_id = top[0]["id"]

        if campaign_id:
            campaign_rows = self.db.rows("SELECT * FROM campaigns WHERE id=?", (campaign_id,))
            campaign = campaign_rows[0] if campaign_rows else None
            members = self.db.rows(
                "SELECT node_id, role FROM campaign_members WHERE campaign_id=?",
                (campaign_id,),
            )
            candidate_ids = [m["node_id"] for m in members]
            role_map = {m["node_id"]: m["role"] for m in members}
        else:
            clauses = ["kind IN ('issue','pr')"]
            params: list[object] = []
            if state in ALLOWED_STATES:
                clauses.append("state=?")
                params.append(state)
            where = " WHERE " + " AND ".join(clauses)
            pool = max(limit * 4, limit)
            candidate_ids = [
                r["id"]
                for r in self.db.rows(
                    f"SELECT id FROM nodes{where} ORDER BY COALESCE(updated_at,'') DESC LIMIT ?",
                    tuple(params + [max(pool, 1)]),
                )
            ]

        if q and q.strip():
            try:
                hits = {
                    r["node_id"]
                    for r in self.db.rows(
                        "SELECT node_id FROM backlog_fts WHERE backlog_fts MATCH ? LIMIT 500",
                        (fts_query(q),),
                    )
                }
            except sqlite3.OperationalError:
                hits = set()
            candidate_ids = [node_id for node_id in candidate_ids if node_id in hits] if candidate_ids else list(hits)

        if kind in ALLOWED_KINDS:
            kind_ids = {
                r["id"]
                for r in self.db.rows("SELECT id FROM nodes WHERE kind=?", (kind,))
            }
            candidate_ids = [node_id for node_id in candidate_ids if node_id in kind_ids]

        if state in ALLOWED_STATES and campaign_id:
            state_ids = {
                r["id"]
                for r in self.db.rows("SELECT id FROM nodes WHERE state=?", (state,))
            }
            candidate_ids = [node_id for node_id in candidate_ids if node_id in state_ids]

        candidate_ids = (
            self._prefer_connected(candidate_ids, max(limit, 1))
            if not campaign_id
            else candidate_ids[: max(limit, 1)]
        )
        if not candidate_ids:
            return {
                "campaign": campaign,
                "nodes": [],
                "relations": [],
                "source": "live",
            }

        qs, params = _in_clause(candidate_ids)
        nodes = self.db.rows(f"SELECT * FROM nodes WHERE id IN ({qs})", params)
        now = datetime.now(UTC)
        filtered: list[dict] = []
        for node in nodes:
            labels = parse_labels(node.get("labels_json"))
            lowered = {label.lower() for label in labels}
            if priority:
                aliases = PRIORITY_ALIASES.get(priority.lower(), (priority.lower(),))
                if not lowered.intersection(aliases):
                    continue
            if component:
                needle = component.lower()
                if not any(
                    needle == label.lower()
                    or label.lower().startswith(f"area:{needle}")
                    or label.lower().startswith(f"component:{needle}")
                    or label.lower().endswith(f"/{needle}")
                    for label in labels
                ):
                    continue
            if blocker:
                if blocker.lower() == "any":
                    if not lowered.intersection(BLOCKER_LABELS):
                        continue
                elif blocker.lower() not in lowered:
                    continue
            updated = _parse_dt(node.get("updated_at"))
            if updated_within_days:
                cutoff = now - timedelta(days=updated_within_days)
                if not updated or updated < cutoff:
                    continue
            if stale_days:
                cutoff = now - timedelta(days=stale_days)
                if updated and updated >= cutoff:
                    continue
            node["labels"] = labels
            node["metadata"] = parse_metadata(node.pop("metadata_json", "{}"))
            node.pop("labels_json", None)
            node["role"] = role_map.get(node["id"], "member")
            if campaign_id:
                node["campaign_id"] = campaign_id
            filtered.append(node)

        kept_ids = [node["id"] for node in filtered]
        relations = self.relations_among(kept_ids)
        if evidence_level:
            relations = [rel for rel in relations if rel.get("evidence_level") == evidence_level]
        return {
            "campaign": campaign,
            "nodes": filtered,
            "relations": relations,
            "source": "live",
        }

    def filter_catalog(self) -> dict:
        label_rows = self.db.rows(
            "SELECT labels_json FROM nodes WHERE kind IN ('issue','pr') AND state='open'"
        )
        labels: set[str] = set()
        for row in label_rows:
            labels.update(parse_labels(row.get("labels_json")))
        priorities = sorted(
            label
            for label in labels
            if label.lower() in {alias for aliases in PRIORITY_ALIASES.values() for alias in aliases}
        )
        blockers = sorted(label for label in labels if label.lower() in BLOCKER_LABELS)
        skip = {label.lower() for label in priorities + blockers}
        skip.update({"duplicate", "invalid", "bug", "enhancement"})
        components = sorted(label for label in labels if label.lower() not in skip)
        relation_types = [r["relation_type"] for r in self.db.rows(
            "SELECT DISTINCT relation_type FROM relations ORDER BY relation_type"
        )]
        evidence_levels = [r["evidence_level"] for r in self.db.rows(
            "SELECT DISTINCT evidence_level FROM relations ORDER BY evidence_level"
        )]
        return {
            "priorities": priorities,
            "components": components[:80],
            "blockers": blockers,
            "relation_types": relation_types,
            "evidence_levels": evidence_levels,
            "roles": [
                "canonical_problem",
                "survivor",
                "donor",
                "provenance",
                "stacked_child",
                "superseded",
                "active_implementation",
                "member",
            ],
        }
