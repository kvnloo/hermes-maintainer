"""Fresh-clone / agent-ready contract: config discovery, demo data, bounded scans, rate limits."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from typer.testing import CliRunner

from hermes_maintainer import cli, config
from hermes_maintainer.api.app import create_app
from hermes_maintainer.github import client as gh_client
from hermes_maintainer.github import ingest
from hermes_maintainer.graph.demo import import_seed_graph

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def clean_env(monkeypatch):
    monkeypatch.delenv("HERMES_MAINTAINER_CONFIG", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


def test_settings_resolve_repo_config_from_any_cwd(tmp_path, monkeypatch, clean_env):
    monkeypatch.chdir(tmp_path)
    s = config.load_settings()
    assert s.root == ROOT
    assert s.paths.database == ROOT / ".data" / "hermes-maintainer.db"
    assert (s.root / "llms.txt").is_file()


def test_settings_fall_back_to_defaults_without_any_config(tmp_path, monkeypatch, clean_env):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config, "_package_repo_root", lambda: None)
    s = config.load_settings()
    assert s.repo.name == "NousResearch/hermes-agent"
    assert s.root == tmp_path.resolve()
    assert s.paths.database == tmp_path.resolve() / ".data" / "hermes-maintainer.db"


def test_import_seed_graph_populates_dashboard_idempotently(db):
    first = import_seed_graph(db, ROOT)
    second = import_seed_graph(db, ROOT)
    assert first == second
    assert first["nodes"] > 0 and first["relations"] > 0 and first["campaigns"] > 0
    client = TestClient(create_app(database=db))
    graph = client.get("/api/graph").json()
    assert graph["nodes"], graph
    assert client.get("/api/campaigns").json()
    assert db.scalar("SELECT COUNT(*) FROM nodes") == first["nodes"]


def _fake_github(monkeypatch, handler):
    calls: list[httpx.Request] = []

    def wrapped(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return handler(request)

    real_init = gh_client.GitHubClient.__init__

    def init(self, token=None, timeout=30.0):
        real_init(self, token, timeout)
        self.client = httpx.Client(
            base_url="https://api.github.com",
            headers=self.client.headers,
            transport=httpx.MockTransport(wrapped),
        )

    monkeypatch.setattr(gh_client.GitHubClient, "__init__", init)
    monkeypatch.setattr(gh_client.time, "sleep", lambda _s: None)
    return calls


def _item(n: int, pr: bool) -> dict:
    out = {"number": n, "title": f"t{n}", "body": "", "state": "open", "labels": []}
    if pr:
        out["head"], out["base"] = {}, {}
    return out


def test_fast_scan_limit_caps_items_and_requests(tmp_path, monkeypatch, clean_env):
    def handler(request):
        per_page = int(request.url.params["per_page"])
        is_pr = request.url.path.endswith("/pulls")
        return httpx.Response(200, json=[_item(i, is_pr) for i in range(1, per_page + 1)])

    calls = _fake_github(monkeypatch, handler)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config, "_package_repo_root", lambda: None)
    counts = ingest.fast_scan(config.load_settings(), limit=5)
    assert counts == {"issues": 5, "prs": 5}
    assert len(calls) == 2
    assert all(c.url.params["per_page"] == "5" for c in calls)


def test_secondary_rate_limit_retries_after_header(monkeypatch):
    responses = [
        httpx.Response(429, headers={"retry-after": "1"}),
        httpx.Response(200, json=[]),
    ]
    calls = _fake_github(monkeypatch, lambda _r: responses.pop(0))
    c = gh_client.GitHubClient()
    assert list(c.iter_pages("/x")) == []
    assert len(calls) == 2


def test_primary_rate_limit_raises_clear_error(monkeypatch):
    def handler(_r):
        return httpx.Response(
            403,
            headers={"x-ratelimit-remaining": "0", "x-ratelimit-reset": "9999999999"},
            json={"message": "API rate limit exceeded"},
        )

    _fake_github(monkeypatch, handler)
    with pytest.raises(gh_client.RateLimitError, match="GITHUB_TOKEN"):
        gh_client.GitHubClient().get_pull("o/r", 1)


def test_scan_cli_skips_git_mirror_by_default(monkeypatch, tmp_path, clean_env):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(config, "_package_repo_root", lambda: None)

    def boom(*_a, **_k):
        raise AssertionError("mirror must be opt-in for scan")

    seen = {}
    monkeypatch.setattr(cli, "ensure_mirror", boom)
    monkeypatch.setattr(cli, "fast_scan", lambda s, limit=None: seen.setdefault("limit", limit) or {})
    result = CliRunner().invoke(cli.app, ["scan", "--mode", "fast", "--limit", "7"])
    assert result.exit_code == 0, result.output
    assert seen["limit"] == 7


def test_init_demo_without_git_and_doctor(monkeypatch, tmp_path, clean_env):
    monkeypatch.setenv("HERMES_MAINTAINER_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setattr(cli, "ensure_mirror", lambda *_a, **_k: pytest.fail("no mirror"))
    runner = CliRunner()
    result = runner.invoke(cli.app, ["init", "--no-fetch-git", "--demo"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "data" / "hermes-maintainer.db").is_file()
    doc = runner.invoke(cli.app, ["doctor"])
    assert doc.exit_code == 0, doc.output
    assert "ui bundle" in doc.output and "demo" in doc.output.lower()
