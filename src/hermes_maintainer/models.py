from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BacklogNode:
    id: str
    kind: str
    number: int | None
    title: str
    body: str
    state: str
    labels: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RelationCandidate:
    src_id: str
    dst_id: str
    relation_type: str
    confidence: float
    evidence: str
    source: str = "analysis"


@dataclass
class FixAtom:
    id: str
    title: str
    pr_id: str | None
    cost: float
    value: float
    covers: set[str] = field(default_factory=set)
    supersedes: set[str] = field(default_factory=set)
    conflicts: set[str] = field(default_factory=set)
    requires: set[str] = field(default_factory=set)
