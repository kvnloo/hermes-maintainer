from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from hermes_maintainer.cli import app
from hermes_maintainer.intake import decide, is_origin_hermes, package_gate
from hermes_maintainer.reports import ingest, list_reports, promote


def test_ingest_stays_local_draft_even_when_later_gates_would_pass():
    got = decide(
        {
            "action": "ingest",
            "reproduced": True,
            "in_scope": True,
            "human_or_policy_allow": True,
            "origin_policy": "allowed",
            "github_writes": True,
            "claimed": True,
            "has_receipt": True,
        }
    )
    assert got["disposition"] == "local_draft"
    assert got["origin_write_permitted"] is False


def test_promote_unknown_policy_fails_closed():
    got = decide(
        {
            "action": "promote_issue",
            "reproduced": True,
            "in_scope": True,
            "human_or_policy_allow": True,
            "origin_policy": "unknown",
            "github_writes": True,
        }
    )
    assert got["disposition"] == "origin_write_blocked"
    assert got["origin_write_permitted"] is False


def test_package_gate_blocks_origin_hermes_even_when_vol_would_allow():
    report = {
        "action": "promote_issue",
        "target_repo": "NousResearch/hermes-agent",
        "reproduced": True,
        "in_scope": True,
        "human_or_policy_allow": True,
        "origin_policy": "allowed",
        "github_writes": True,
    }
    assert is_origin_hermes(report["target_repo"])
    vol = decide(report)
    assert vol["origin_write_permitted"] is True
    gated = package_gate(report)
    assert gated["origin_write_permitted"] is False
    assert gated["performed_origin_write"] is False
    assert gated["disposition"] == "origin_write_blocked"


def test_package_gate_never_performs_writes_for_non_origin_repo():
    report = {
        "action": "promote_issue",
        "target_repo": "kvnloo/hermes-maintainer",
        "reproduced": True,
        "in_scope": True,
        "human_or_policy_allow": True,
        "origin_policy": "allowed",
        "github_writes": True,
    }
    gated = package_gate(report)
    assert gated["disposition"] == "origin_issue_allowed"
    assert gated["origin_write_permitted"] is True
    assert gated["performed_origin_write"] is False


def test_ingest_writes_only_local_json(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def boom(*_args, **_kwargs):
        raise AssertionError("GitHub HTTP must not run on ingest")

    monkeypatch.setattr(httpx.Client, "request", boom)
    monkeypatch.setattr(httpx.Client, "get", boom)
    monkeypatch.setattr(httpx.Client, "post", boom)
    record = ingest(tmp_path, title="chat pane froze", body="repro: open bots")
    assert record["intake"]["disposition"] == "local_draft"
    assert record["intake"]["performed_origin_write"] is False
    assert record["intake"]["origin_write_permitted"] is False
    stored = json.loads((tmp_path / "inbox" / f"{record['id']}.json").read_text(encoding="utf-8"))
    assert stored["title"] == "chat pane froze"
    assert list_reports(tmp_path)[0]["id"] == record["id"]


def test_promote_origin_hermes_does_not_write(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    def boom(*_args, **_kwargs):
        raise AssertionError("GitHub HTTP must not run on promote")

    monkeypatch.setattr(httpx.Client, "request", boom)
    monkeypatch.setattr(httpx.Client, "post", boom)
    record = ingest(tmp_path, title="need a github issue")
    updated = promote(
        tmp_path,
        record["id"],
        reproduced=True,
        in_scope=True,
        origin_policy="allowed",
        github_writes=True,
        human_or_policy_allow=True,
    )
    assert updated["intake"]["disposition"] == "origin_write_blocked"
    assert updated["intake"]["performed_origin_write"] is False
    assert "never writes NousResearch/hermes-agent" in " ".join(updated["intake"]["reasons"])


def test_cli_ingest_and_list_are_local_only(tmp_path: Path):
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "report",
            "ingest",
            "--title",
            "composer lost focus",
            "--body",
            "desktop only",
            "--data-dir",
            str(tmp_path),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["intake"]["disposition"] == "local_draft"
    listed = runner.invoke(app, ["report", "list", "--data-dir", str(tmp_path)])
    assert listed.exit_code == 0, listed.output
    rows = json.loads(listed.stdout)
    assert rows[0]["performed_origin_write"] is False
    assert rows[0]["disposition"] == "local_draft"
