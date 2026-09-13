from __future__ import annotations

import json
import re
from typing import Any

from hermes_maintainer.github.ids import make_node_id, parse_repo

_REF_RE = re.compile(r"(?<![\w/])#(?P<num>\d+)\b")
_FIX_RE = re.compile(r"\b(?:fix(?:e[sd])?|close[sd]?|resolve[sd]?)\s+#(?P<num>\d+)\b", re.IGNORECASE)
_SUPERSEDE_RE = re.compile(r"\b(?:supersedes?|replaces?)\s+#(?P<num>\d+)\b", re.IGNORECASE)
_RELATED_RE = re.compile(r"\b(?:related(?:\s+to)?|refs?|see)\s*:?[ ]*#(?P<num>\d+)\b", re.IGNORECASE)
_PR_URL_RE = re.compile(r"github\.com/(?P<repo>[^/]+/[^/]+)/pull/(?P<num>\d+)")
_ISSUE_URL_RE = re.compile(r"github\.com/(?P<repo>[^/]+/[^/]+)/issues/(?P<num>\d+)")


def _labels(item: dict[str, Any]) -> list[str]:
    labels = item.get("labels") or []
    return [x.get("name", "") if isinstance(x, dict) else str(x) for x in labels]


def issue_node(repo: str, item: dict[str, Any], run_id: int) -> dict[str, Any]:
    return {
        "id": make_node_id(repo, "issue", item["number"]),
        "repo": repo,
        "kind": "issue",
        "number": item["number"],
        "sha": None,
        "title": item.get("title") or "",
        "body": item.get("body") or "",
        "state": item.get("state"),
        "author": (item.get("user") or {}).get("login"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "closed_at": item.get("closed_at"),
        "url": item.get("html_url"),
        "labels_json": json.dumps(_labels(item)),
        "base_ref": None,
        "head_ref": None,
        "base_sha": None,
        "head_sha": None,
        "draft": 0,
        "mergeable": None,
        "changed_files": None,
        "additions": None,
        "deletions": None,
        "metadata_json": json.dumps({
            "comments": item.get("comments", 0),
            "locked": item.get("locked", False),
            "author_association": item.get("author_association"),
        }),
        "last_seen_run": run_id,
    }


def pr_node(repo: str, item: dict[str, Any], run_id: int) -> dict[str, Any]:
    head = item.get("head") or {}
    base = item.get("base") or {}
    return {
        "id": make_node_id(repo, "pr", item["number"]),
        "repo": repo,
        "kind": "pr",
        "number": item["number"],
        "sha": None,
        "title": item.get("title") or "",
        "body": item.get("body") or "",
        "state": item.get("state"),
        "author": (item.get("user") or {}).get("login"),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "closed_at": item.get("closed_at"),
        "url": item.get("html_url"),
        "labels_json": json.dumps(_labels(item)),
        "base_ref": base.get("ref"),
        "head_ref": head.get("ref"),
        "base_sha": base.get("sha"),
        "head_sha": head.get("sha"),
        "draft": int(bool(item.get("draft"))),
        "mergeable": str(item.get("mergeable")) if "mergeable" in item else None,
        "changed_files": item.get("changed_files"),
        "additions": item.get("additions"),
        "deletions": item.get("deletions"),
        "metadata_json": json.dumps({
            "merged_at": item.get("merged_at"),
            "commits": item.get("commits"),
            "review_comments": item.get("review_comments"),
            "comments": item.get("comments"),
            "head_repo": (head.get("repo") or {}).get("full_name"),
        }),
        "last_seen_run": run_id,
    }


def explicit_references(
    body: str, default_repo: str = ""
) -> list[tuple[str, int, float, str, str]]:
    """Return (relation_type, number, confidence, evidence, repo) tuples."""
    body = body or ""
    default = parse_repo(default_repo) if default_repo else ""
    found: dict[tuple[str, int, str], tuple[str, int, float, str, str]] = {}
    for regex, relation, confidence in (
        (_FIX_RE, "fixes", 0.99),
        (_SUPERSEDE_RE, "supersedes", 0.98),
        (_RELATED_RE, "related", 0.88),
    ):
        for m in regex.finditer(body):
            num = int(m.group("num"))
            key = (relation, num, default)
            found[key] = (relation, num, confidence, m.group(0), default)
    for regex, relation in ((_PR_URL_RE, "references_pr"), (_ISSUE_URL_RE, "references_issue")):
        for m in regex.finditer(body):
            num = int(m.group("num"))
            repo = parse_repo(m.group("repo"))
            key = (relation, num, repo)
            found.setdefault(key, (relation, num, 0.85, m.group(0), repo))
    for m in _REF_RE.finditer(body):
        num = int(m.group("num"))
        if not any(existing[1] == num for existing in found.values()):
            found[("references", num, default)] = ("references", num, 0.65, m.group(0), default)
    return list(found.values())
