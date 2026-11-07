from __future__ import annotations

from dataclasses import dataclass, field


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
