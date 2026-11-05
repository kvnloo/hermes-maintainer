"""SPEC §10 intake ladder — same contract as verified-oss-loop/scripts/intake-gate.py.

Keep the dispositions aligned with that script. This module classifies reports.
It never performs GitHub writes (M6 publisher is later). Origin Hermes is refused.
"""
from __future__ import annotations

from typing import Any

ACTIONS = frozenset({"ingest", "promote_issue", "open_pr"})
POLICIES = frozenset({"allowed", "forbidden", "unknown"})
ORIGIN_HERMES = "nousresearch/hermes-agent"

DISPOSITIONS = frozenset(
    {
        "local_draft",
        "local_duplicate",
        "stop_covered",
        "needs_discussion",
        "origin_write_blocked",
        "origin_issue_allowed",
        "origin_pr_blocked",
        "origin_pr_allowed",
    }
)


def _bool(report: dict[str, Any], key: str, default: bool = False) -> bool:
    if key not in report:
        return default
    val = report[key]
    if not isinstance(val, bool):
        raise TypeError(f"{key} must be a boolean")
    return val


def decide(report: dict[str, Any]) -> dict[str, Any]:
    """Fail-closed intake. Default capture is a local draft, not a public issue."""
    action = report.get("action", "ingest")
    if action not in ACTIONS:
        raise ValueError(f"unknown action {action!r}")
    policy = report.get("origin_policy", "unknown")
    if policy not in POLICIES:
        raise ValueError(f"unknown origin_policy {policy!r}")

    competing = _bool(report, "competing_pr")
    duplicate = report.get("duplicate_of")
    has_dup = isinstance(duplicate, str) and bool(str(duplicate).strip())
    reproduced = _bool(report, "reproduced")
    in_scope = _bool(report, "in_scope")
    github_writes = _bool(report, "github_writes")
    claimed = _bool(report, "claimed")
    has_receipt = _bool(report, "has_receipt")
    human = _bool(report, "human_or_policy_allow")

    def result(disposition: str, origin_write_permitted: bool, *reasons: str) -> dict[str, Any]:
        if disposition not in DISPOSITIONS:
            raise ValueError(f"internal: bad disposition {disposition}")
        return {
            "disposition": disposition,
            "origin_write_permitted": origin_write_permitted,
            "reasons": list(reasons),
        }

    if competing:
        return result(
            "stop_covered",
            False,
            "competing PR or maintainer branch covers the scope",
        )
    if has_dup:
        return result("local_duplicate", False, "one canonical issue per problem")
    if action == "ingest":
        return result("local_draft", False, "ingest is local-only")
    if policy != "allowed":
        return result("origin_write_blocked", False, f"origin_policy={policy} fails closed")
    if not github_writes:
        return result("origin_write_blocked", False, "github_writes=0 until authorized")

    missing: list[str] = []
    if not reproduced:
        missing.append("not reproduced")
    if not in_scope:
        missing.append("not in_scope")
    if not human:
        missing.append("no human_or_policy_allow")
    if missing:
        return result("needs_discussion", False, *missing)
    if action == "promote_issue":
        return result("origin_issue_allowed", True, "issue promote gates passed")

    pr_missing: list[str] = []
    if not claimed:
        pr_missing.append("not claimed")
    if not has_receipt:
        pr_missing.append("no exact-head receipt")
    if pr_missing:
        return result("origin_pr_blocked", False, *pr_missing)
    return result("origin_pr_allowed", True, "pr gates passed")


def normalize_repo(value: str) -> str:
    text = value.strip()
    for prefix in ("https://github.com/", "http://github.com/", "git@github.com:"):
        if text.lower().startswith(prefix):
            text = text[len(prefix) :]
            break
    return text.removesuffix(".git").strip("/")


def is_origin_hermes(target_repo: str) -> bool:
    return normalize_repo(target_repo).lower() == ORIGIN_HERMES


def package_gate(report: dict[str, Any]) -> dict[str, Any]:
    """VOL decide() plus this package's write ban.

    performed_origin_write is always false: CONTRIBUTING forbids GitHub mutation
    in early milestones. Origin Hermes is refused even if protocol gates pass.
    """
    got = decide(report)
    target = str(report.get("target_repo") or "NousResearch/hermes-agent")
    reasons = list(got["reasons"])
    permitted = bool(got["origin_write_permitted"])
    disposition = str(got["disposition"])
    if is_origin_hermes(target) and permitted:
        permitted = False
        disposition = "origin_write_blocked"
        reasons.append("hermes-maintainer never writes NousResearch/hermes-agent")
    reasons.append("this package does not perform GitHub writes")
    return {
        "disposition": disposition,
        "origin_write_permitted": permitted,
        "performed_origin_write": False,
        "target_repo": target,
        "reasons": reasons,
    }
