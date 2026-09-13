"""Local complaint inbox. Files only. No GitHub mutation."""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from hermes_maintainer.intake import package_gate

_SLUG = re.compile(r"[^a-z0-9]+")


def inbox_dir(data_dir: Path) -> Path:
    path = Path(data_dir) / "inbox"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _slug(title: str) -> str:
    s = _SLUG.sub("-", title.lower()).strip("-")
    return (s[:40] or "report").strip("-")


def _new_id(title: str) -> str:
    return f"{_slug(title)}-{uuid.uuid4().hex[:8]}"


def report_path(data_dir: Path, report_id: str) -> Path:
    return inbox_dir(data_dir) / f"{report_id}.json"


def ingest(
    data_dir: Path,
    *,
    title: str,
    body: str = "",
    target_repo: str = "NousResearch/hermes-agent",
    duplicate_of: str | None = None,
    competing_pr: bool = False,
) -> dict[str, Any]:
    report_id = _new_id(title)
    record: dict[str, Any] = {
        "id": report_id,
        "title": title,
        "body": body,
        "target_repo": target_repo,
        "action": "ingest",
        "duplicate_of": duplicate_of,
        "competing_pr": competing_pr,
        "reproduced": False,
        "in_scope": False,
        "origin_policy": "unknown",
        "github_writes": False,
        "claimed": False,
        "has_receipt": False,
        "human_or_policy_allow": False,
    }
    record["intake"] = package_gate(record)
    dest = report_path(data_dir, report_id)
    dest.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def load(data_dir: Path, report_id: str) -> dict[str, Any]:
    path = report_path(data_dir, report_id)
    if not path.is_file():
        raise FileNotFoundError(report_id)
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError("report must be a JSON object")
    return data


def save(data_dir: Path, record: dict[str, Any]) -> dict[str, Any]:
    dest = report_path(data_dir, str(record["id"]))
    dest.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def list_reports(data_dir: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(inbox_dir(data_dir).glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            rows.append(data)
    return rows


def promote(
    data_dir: Path,
    report_id: str,
    *,
    action: str = "promote_issue",
    reproduced: bool | None = None,
    in_scope: bool | None = None,
    origin_policy: str | None = None,
    github_writes: bool | None = None,
    human_or_policy_allow: bool | None = None,
    claimed: bool | None = None,
    has_receipt: bool | None = None,
) -> dict[str, Any]:
    record = load(data_dir, report_id)
    record["action"] = action
    if reproduced is not None:
        record["reproduced"] = reproduced
    if in_scope is not None:
        record["in_scope"] = in_scope
    if origin_policy is not None:
        record["origin_policy"] = origin_policy
    if github_writes is not None:
        record["github_writes"] = github_writes
    if human_or_policy_allow is not None:
        record["human_or_policy_allow"] = human_or_policy_allow
    if claimed is not None:
        record["claimed"] = claimed
    if has_receipt is not None:
        record["has_receipt"] = has_receipt
    record["intake"] = package_gate(record)
    return save(data_dir, record)
