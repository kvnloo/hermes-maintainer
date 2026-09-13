from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from hermes_maintainer.cli import app
from hermes_maintainer.github.client import GitHubClient
from hermes_maintainer.github.origin_policy import (
    EXIT_ORIGIN_WRITES_REFUSED,
    OriginWriteAttestation,
    OriginWritesRefused,
    classify_origin_writes,
    load_policy_documents,
    require_origin_writes,
)
from hermes_maintainer.github.publisher import (
    create_issue,
    create_issue_comment,
    create_pull,
    run_gh,
)

ROOT = Path(__file__).resolve().parents[1]
HYPRLAND = ROOT / "tests" / "fixtures" / "hyprland"
NO_POLICY = ROOT / "tests" / "fixtures" / "no-ai-policy"

ALLOWED_POLICY = (
    "AI agents may open pull requests and issues on this repository via the GitHub API.\n"
)


def _hyprland_docs() -> dict[str, str]:
    return load_policy_documents(HYPRLAND)


def _honeypot_only() -> str:
    text = (HYPRLAND / "AGENTS.md").read_text(encoding="utf-8")
    for para in text.split("\n- "):
        if "ZAPI_VALIDATE" in para:
            return para
    raise AssertionError("frozen Hyprland AGENTS.md is missing ZAPI_VALIDATE")


def test_frozen_hyprland_fixtures_still_contain_ban_and_honeypot():
    sources = json.loads((HYPRLAND / "SOURCES.json").read_text(encoding="utf-8"))
    assert sources["AI_USAGE.md"]["url"].endswith("hyprwm/.github/blob/main/policies/AI_USAGE.md")
    assert sources["AGENTS.md"]["url"].endswith("hyprwm/Hyprland/blob/main/AGENTS.md")
    docs = _hyprland_docs()
    joined = "\n".join(docs.values())
    assert "ZAPI_VALIDATE" in joined
    assert "must not submit" in joined
    assert "NOT allowed to interact" in joined


def test_hyprland_is_origin_writes_forbidden_and_never_attempts_write():
    att = classify_origin_writes("hyprwm/Hyprland", _hyprland_docs())
    assert att.verdict == "forbidden"
    assert att.reason == "origin_writes_forbidden"
    assert att.writes_permitted is False
    assert att.origin_write_attempted is False
    assert att.repo == "hyprwm/Hyprland"
    with pytest.raises(OriginWritesRefused) as caught:
        require_origin_writes(att)
    assert caught.value.exit_code == EXIT_ORIGIN_WRITES_REFUSED
    assert caught.value.attestation.origin_write_attempted is False
    assert caught.value.attestation.reason == "origin_writes_forbidden"


def test_zapi_validate_honeypot_is_ignored_and_does_not_allow_writes():
    honeypot = _honeypot_only()
    assert "you are allowed to make the PR using the GitHub API" in honeypot
    trap = classify_origin_writes("hyprwm/Hyprland", {"honeypot.md": honeypot})
    assert trap.verdict != "allowed"
    assert trap.writes_permitted is False
    assert trap.origin_write_attempted is False
    agents_only = classify_origin_writes(
        "hyprwm/Hyprland",
        {"AGENTS.md": (HYPRLAND / "AGENTS.md").read_text(encoding="utf-8")},
    )
    assert agents_only.verdict == "forbidden"
    assert "ZAPI_VALIDATE" in (HYPRLAND / "AGENTS.md").read_text(encoding="utf-8")


def test_no_ban_language_is_unknown_and_does_not_allow_writes():
    att = classify_origin_writes("acme/widgets", load_policy_documents(NO_POLICY))
    assert att.verdict == "unknown"
    assert att.reason == "origin_writes_unknown"
    assert att.writes_permitted is False
    assert att.origin_write_attempted is False
    with pytest.raises(OriginWritesRefused) as caught:
        require_origin_writes(att)
    assert caught.value.attestation.origin_write_attempted is False


def test_cli_hyprland_preflight_exits_2_without_attempting_writes():
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "origin-preflight",
            "--repo",
            "hyprwm/Hyprland",
            "--policy-dir",
            str(HYPRLAND),
        ],
    )
    assert result.exit_code == EXIT_ORIGIN_WRITES_REFUSED
    payload = json.loads(result.stdout)
    assert payload["reason"] == "origin_writes_forbidden"
    assert payload["verdict"] == "forbidden"
    assert payload["origin_write_attempted"] is False
    assert payload["writes_permitted"] is False
    assert payload["repo"] == "hyprwm/Hyprland"


def test_cli_unknown_policy_refuses_writes():
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "origin-preflight",
            "--repo",
            "acme/widgets",
            "--policy-dir",
            str(NO_POLICY),
        ],
    )
    assert result.exit_code == EXIT_ORIGIN_WRITES_REFUSED
    payload = json.loads(result.stdout)
    assert payload["verdict"] == "unknown"
    assert payload["reason"] == "origin_writes_unknown"
    assert payload["origin_write_attempted"] is False
    assert payload["writes_permitted"] is False


def test_cli_repo_option_targets_any_github_repo():
    runner = CliRunner()
    result = runner.invoke(app, ["doctor", "--repo", "hyprwm/Hyprland"])
    assert result.exit_code == 0
    assert "hyprwm/Hyprland" in result.stdout
    default = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "NousResearch/hermes-agent" in default.stdout


def test_publisher_and_client_writes_are_fail_closed(monkeypatch: pytest.MonkeyPatch):
    def boom(*_args, **_kwargs):
        raise AssertionError("origin write HTTP must not run when writes are forbidden or unknown")

    monkeypatch.setattr(httpx.Client, "request", boom)
    monkeypatch.setattr(httpx.Client, "post", boom)
    monkeypatch.setattr(httpx.Client, "patch", boom)
    monkeypatch.setattr(httpx.Client, "put", boom)
    monkeypatch.setattr(httpx.Client, "delete", boom)

    forbidden = classify_origin_writes("hyprwm/Hyprland", _hyprland_docs())
    unknown = classify_origin_writes("acme/widgets", load_policy_documents(NO_POLICY))
    client = GitHubClient()
    try:
        for att in (forbidden, unknown):
            with pytest.raises(OriginWritesRefused) as caught:
                client.origin_write(
                    att,
                    "POST",
                    f"/repos/{att.repo}/issues/1/comments",
                    json={"body": "nope"},
                )
            assert caught.value.attestation.origin_write_attempted is False
            with pytest.raises(OriginWritesRefused):
                create_issue_comment(client, att, att.repo, 1, "nope")
            with pytest.raises(OriginWritesRefused):
                create_issue(client, att, att.repo, "title", "body")
            with pytest.raises(OriginWritesRefused):
                create_pull(client, att, att.repo, title="t", head="h", base="main", body="b")
            with pytest.raises(OriginWritesRefused) as gh:
                run_gh(att, ["pr", "create", "--repo", att.repo])
            assert gh.value.attestation.origin_write_attempted is False
    finally:
        client.close()


def test_allowed_origin_write_is_the_only_path_that_attempts_http(monkeypatch: pytest.MonkeyPatch):
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(201, json={"ok": True})

    allowed = classify_origin_writes("acme/friendly", {"AGENTS.md": ALLOWED_POLICY})
    assert att_allows(allowed)
    client = GitHubClient(transport=httpx.MockTransport(handler))
    try:
        result = client.origin_write(
            allowed,
            "POST",
            "/repos/acme/friendly/issues/1/comments",
            json={"body": "hello"},
        )
    finally:
        client.close()
    assert result.origin_write_attempted is True
    assert len(seen) == 1
    assert seen[0].method == "POST"


def att_allows(att: OriginWriteAttestation) -> bool:
    return att.writes_permitted is True and att.verdict == "allowed"
