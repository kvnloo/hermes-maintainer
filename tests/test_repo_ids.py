from __future__ import annotations

from pathlib import Path

import pytest

from hermes_maintainer.config import (
    OptimizerConfig,
    PathsConfig,
    RepoConfig,
    ScanConfig,
    ServerConfig,
    Settings,
    SimilarityConfig,
    load_settings,
    with_repo,
)
from hermes_maintainer.db import Database
from hermes_maintainer.github.ids import make_node_id, node_kind, parse_repo
from hermes_maintainer.github.ingest import fast_scan
from hermes_maintainer.github.normalize import explicit_references, issue_node, pr_node


def test_parse_repo_accepts_owner_name_and_github_url():
    assert parse_repo("hyprwm/Hyprland") == "hyprwm/Hyprland"
    assert parse_repo("https://github.com/acme/widgets.git") == "acme/widgets"
    with pytest.raises(ValueError):
        parse_repo("not-a-repo")


def test_node_ids_include_owner_repo_and_do_not_collide():
    a = issue_node("acme/widgets", {"number": 1, "title": "one", "user": {}}, run_id=1)
    b = issue_node("other/lib", {"number": 1, "title": "one", "user": {}}, run_id=1)
    assert a["id"] == "acme/widgets:issue:1"
    assert b["id"] == "other/lib:issue:1"
    assert a["id"] != b["id"]
    pr = pr_node("acme/widgets", {"number": 7, "title": "fix", "user": {}, "head": {}, "base": {}}, run_id=1)
    assert pr["id"] == "acme/widgets:pr:7"
    assert make_node_id("acme/widgets", "issue", 1) == "acme/widgets:issue:1"
    assert node_kind("acme/widgets:issue:1") == "issue"
    assert node_kind("acme/widgets:pr:7") == "pr"
    assert node_kind("issue:1") == "issue"


def test_explicit_references_namespace_targets_by_repo():
    refs = explicit_references(
        "Fixes #10. See https://github.com/x/y/pull/13",
        default_repo="acme/widgets",
    )
    by = {(kind, num, repo) for kind, num, _conf, _ev, repo in refs}
    assert ("fixes", 10, "acme/widgets") in by
    assert ("references_pr", 13, "x/y") in by


def test_with_repo_overrides_clone_url_and_mirror_without_assuming_hermes():
    settings = load_settings()
    assert settings.repo.name == "NousResearch/hermes-agent"
    targeted = with_repo(settings, "hyprwm/Hyprland")
    assert targeted.repo.name == "hyprwm/Hyprland"
    assert targeted.repo.clone_url == "https://github.com/hyprwm/Hyprland.git"
    assert "Hyprland" in str(targeted.paths.mirror_dir)
    assert "hermes-agent" not in str(targeted.paths.mirror_dir)
    assert targeted.paths.database == settings.paths.database


def test_fast_scan_uses_repo_in_node_ids(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    class FakeClient:
        def __init__(self, token=None):
            self.token = token

        def close(self) -> None:
            return None

        def iter_issues(self, repo: str, *, max_pages=None):
            assert repo == "acme/widgets"
            yield {
                "number": 1,
                "title": "lock",
                "body": "Fixes #2",
                "user": {"login": "ada"},
                "state": "open",
                "html_url": "https://github.com/acme/widgets/issues/1",
                "labels": [],
                "created_at": None,
                "updated_at": "2026-01-01",
                "closed_at": None,
                "comments": 0,
                "locked": False,
                "author_association": "NONE",
            }
            yield {
                "number": 2,
                "title": "root",
                "body": "",
                "user": {"login": "ada"},
                "state": "open",
                "html_url": "https://github.com/acme/widgets/issues/2",
                "labels": [],
                "created_at": None,
                "updated_at": "2026-01-01",
                "closed_at": None,
                "comments": 0,
                "locked": False,
                "author_association": "NONE",
            }

        def iter_pulls(self, repo: str, *, max_pages=None):
            assert repo == "acme/widgets"
            return iter(())

    monkeypatch.setattr("hermes_maintainer.github.ingest.GitHubClient", FakeClient)
    settings = Settings(
        root=tmp_path,
        repo=RepoConfig(name="acme/widgets", clone_url="https://github.com/acme/widgets.git"),
        paths=PathsConfig(data_dir=tmp_path, mirror_dir=tmp_path / "mirror", database=tmp_path / "graph.db"),
        scan=ScanConfig(issue_pages_per_fast_scan=1, pr_pages_per_fast_scan=1),
        similarity=SimilarityConfig(),
        optimizer=OptimizerConfig(),
        server=ServerConfig(),
        github_token=None,
    )
    counts = fast_scan(settings)
    assert counts["issues"] == 2
    db = Database(settings.paths.database)
    ids = {row["id"] for row in db.rows("SELECT id FROM nodes")}
    assert ids == {"acme/widgets:issue:1", "acme/widgets:issue:2"}
    rels = db.rows("SELECT src_id, dst_id, relation_type FROM relations")
    assert rels == [
        {
            "src_id": "acme/widgets:issue:1",
            "dst_id": "acme/widgets:issue:2",
            "relation_type": "fixes",
        }
    ]
