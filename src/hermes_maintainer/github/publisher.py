from __future__ import annotations

from typing import Any

from hermes_maintainer.github.origin_policy import (
    OriginWriteAttestation,
    require_origin_writes,
)


def create_issue_comment(client: Any, attestation: OriginWriteAttestation, repo: str, number: int, body: str):
    return client.origin_write(
        attestation,
        "POST",
        f"/repos/{repo}/issues/{number}/comments",
        json={"body": body},
    )


def create_issue(client: Any, attestation: OriginWriteAttestation, repo: str, title: str, body: str):
    return client.origin_write(
        attestation,
        "POST",
        f"/repos/{repo}/issues",
        json={"title": title, "body": body},
    )


def create_pull(
    client: Any,
    attestation: OriginWriteAttestation,
    repo: str,
    *,
    title: str,
    head: str,
    base: str,
    body: str,
):
    return client.origin_write(
        attestation,
        "POST",
        f"/repos/{repo}/pulls",
        json={"title": title, "head": head, "base": base, "body": body},
    )


def run_gh(attestation: OriginWriteAttestation, argv: list[str]) -> OriginWriteAttestation:
    """Fail-closed gate in front of `gh pr` / issue / comment helpers. Does not spawn gh."""
    require_origin_writes(attestation)
    return attestation
