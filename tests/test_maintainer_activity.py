import importlib.util
import json
import pathlib
import sys

P = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "maintainer-activity.py"
spec = importlib.util.spec_from_file_location("ma", P); ma = importlib.util.module_from_spec(spec); spec.loader.exec_module(ma)


def pr(n, au, mb, files, reviews=(), comments=(), created="2026-11-01T00:00:00Z", merged="2026-11-01T10:00:00Z"):
    return {"number": n, "title": f"t{n}", "createdAt": created, "mergedAt": merged, "author": {"login": au}, "mergedBy": {"login": mb},
            "files": {"nodes": [{"path": f} for f in files]},
            "reviews": {"nodes": [{"author": {"login": u, "__typename": "Bot" if u.endswith("-apps") else "User"}, "state": s, "submittedAt": t} for u, s, t in reviews]},
            "comments": {"nodes": [{"author": {"login": u}, "createdAt": t} for u, t in comments]}}


def test_area_groups_tools_and_gateway_two_levels():
    assert ma.area("tools/browser/x.py") == "tools/browser"
    assert ma.area("gateway/platforms/telegram.py") == "gateway/platforms"
    assert ma.area("agent/loop.py") == "agent"
    assert ma.area("README.md") == "README.md"


def test_report_counts_mergers_reviewers_response_and_watch(tmp_path, monkeypatch):
    data = [pr(1, "alice", "teknium1", ["agent/a.py"], reviews=[("greptile-apps", "COMMENTED", "2026-11-01T00:05:00Z"), ("teknium1", "APPROVED", "2026-11-01T02:00:00Z")]),
            pr(2, "bob", "teknium1", ["tools/web/x.py"], comments=[("github-actions[bot]", "2026-11-01T00:10:00Z"), ("carol", "2026-11-01T04:00:00Z")]),
            pr(3, "carol", "carol", ["gateway/platforms/t.py"], reviews=[("carol", "COMMENTED", "2026-11-01T01:00:00Z")])]
    monkeypatch.setattr(ma, "fetch", lambda *a: data)
    monkeypatch.setattr(sys, "argv", ["x", "--days", "1", "--out", str(tmp_path)])
    ma.main()
    R = json.loads((tmp_path / "maintainers.json").read_text())
    assert R["merged_prs"] == 3 and R["self_merged"] == 1
    assert R["mergers"][0]["login"] == "teknium1" and R["mergers"][0]["merged"] == 2
    assert R["first_response"]["prs_with_response"] == 2          # bot comment, App review and self-review ignored
    assert "greptile-apps" not in [r["login"] for r in R["reviewers"]]
    assert R["first_response"]["external"]["prs"] == 2            # carol merges, so carol-authored #3 is internal
    assert R["first_response"]["median_hours"] == 3.0             # 2 h and 4 h
    assert R["watch"]["merged_count"] == 2 and R["watch"]["approved"] == 1
    assert "## teknium1" in (tmp_path / "MAINTAINERS-ACTIVITY.md").read_text()
