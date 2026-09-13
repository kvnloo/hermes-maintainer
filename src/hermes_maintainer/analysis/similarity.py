from __future__ import annotations

import re
from collections import Counter

from hermes_maintainer.config import Settings
from hermes_maintainer.db import Database

_TOKEN_RE = re.compile(r"[A-Za-z0-9_./:+-]{2,}")
_STOP = {
    "the", "and", "for", "with", "that", "this", "from", "into", "when", "where", "what",
    "does", "fix", "feat", "bug", "issue", "pull", "request", "hermes", "agent", "test",
}


def tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "") if t.lower() not in _STOP]


def _weighted_jaccard(a: Counter[str], b: Counter[str]) -> float:
    universe = set(a) | set(b)
    numerator = sum(min(a[t], b[t]) for t in universe)
    denominator = sum(max(a[t], b[t]) for t in universe)
    return numerator / denominator if denominator else 0.0


def _title_bonus(a: str, b: str) -> float:
    aa, bb = set(tokens(a)), set(tokens(b))
    if not aa or not bb:
        return 0.0
    overlap = len(aa & bb) / max(1, min(len(aa), len(bb)))
    return min(0.18, overlap * 0.18)


def lexical_similarity(a: dict, b: dict) -> tuple[float, int]:
    ta = Counter(tokens((a.get("title") or "") + " " + (a.get("body") or "")))
    tb = Counter(tokens((b.get("title") or "") + " " + (b.get("body") or "")))
    shared = len(set(ta) & set(tb))
    score = min(1.0, _weighted_jaccard(ta, tb) + _title_bonus(a.get("title", ""), b.get("title", "")))
    return score, shared


def build_similarity_edges(settings: Settings) -> dict[str, int]:
    db = Database(settings.paths.database)
    rows = db.rows(
        """
        SELECT id,kind,number,title,body,updated_at,labels_json
        FROM nodes
        WHERE state='open' AND kind IN ('issue','pr')
        ORDER BY COALESCE(updated_at,'') DESC
        """
    )
    # Candidate reduction by token inverted index. This is intentionally deterministic and cheap.
    index: dict[str, list[int]] = {}
    token_sets: list[set[str]] = []
    for idx, row in enumerate(rows):
        ts = set(tokens((row.get("title") or "") + " " + (row.get("body") or "")))
        token_sets.append(ts)
        for token in ts:
            index.setdefault(token, []).append(idx)

    pairs: set[tuple[int, int]] = set()
    for i, ts in enumerate(token_sets):
        candidate_counts: Counter[int] = Counter()
        for token in ts:
            for j in index.get(token, []):
                if j > i:
                    candidate_counts[j] += 1
        for j, shared in candidate_counts.most_common(settings.scan.max_similarity_candidates_per_node):
            if shared >= settings.similarity.minimum_shared_tokens:
                pairs.add((i, j))

    kept = 0
    strong = 0
    for i, j in pairs:
        score, shared = lexical_similarity(rows[i], rows[j])
        if score < settings.similarity.lexical_threshold:
            continue
        relation = "similar_to"
        if score >= settings.similarity.strong_threshold:
            relation = "possible_duplicate"
            strong += 1
        db.add_relation(
            rows[i]["id"],
            rows[j]["id"],
            relation,
            confidence=score,
            evidence_level="source_confirmed",
            evidence=f"lexical score={score:.3f}, shared_tokens={shared}",
            source="lexical_v1",
        )
        kept += 1
    return {"candidate_pairs": len(pairs), "kept": kept, "strong": strong}
