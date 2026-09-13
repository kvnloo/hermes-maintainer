from __future__ import annotations

import re

_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_GITHUB_PREFIXES = (
    "https://github.com/",
    "http://github.com/",
    "github.com/",
)


def parse_repo(value: str) -> str:
    """Return canonical GitHub `owner/name` from a flag, URL, or config value."""
    raw = (value or "").strip().rstrip("/")
    lowered = raw.lower()
    for prefix in _GITHUB_PREFIXES:
        if lowered.startswith(prefix):
            raw = raw[len(prefix) :]
            break
    raw = raw.removesuffix(".git")
    raw = raw.strip("/")
    if not _REPO_RE.fullmatch(raw):
        raise ValueError(f"repo must be owner/name, got {value!r}")
    return raw


def make_node_id(repo: str, kind: str, number: int) -> str:
    return f"{parse_repo(repo)}:{kind}:{int(number)}"


def node_kind(node_id: str) -> str | None:
    if not node_id:
        return None
    parts = node_id.split(":")
    if len(parts) >= 3 and "/" in parts[0]:
        return parts[1]
    return parts[0]
