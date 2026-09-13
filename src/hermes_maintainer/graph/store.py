from __future__ import annotations

import json
from collections import defaultdict, deque
from typing import Iterable

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

    def export_json(self) -> dict:
        nodes = self.db.rows("SELECT * FROM nodes WHERE kind IN ('issue','pr')")
        relations = self.db.rows("SELECT * FROM relations")
        for node in nodes:
            node["labels"] = json.loads(node.pop("labels_json", "[]"))
            node["metadata"] = json.loads(node.pop("metadata_json", "{}"))
        return {"nodes": nodes, "relations": relations}
