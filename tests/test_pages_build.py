from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _build(out: Path):
    path = ROOT / "scripts" / "build-pages.py"
    spec = importlib.util.spec_from_file_location("hermes_build_pages", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.build(out)


def test_pages_snapshot_has_llms_and_seed_graph(tmp_path: Path):
    site = _build(tmp_path / "site")
    llms = (site / "llms.txt").read_text(encoding="utf-8")
    assert llms.startswith("# hermes-maintainer")
    html = (site / "index.html").read_text(encoding="utf-8")
    assert "pages-adapter.js" in html
    assert 'href="./static/styles.css"' in html
    assert 'href="/static/' not in html
    demo = json.loads((site / "api" / "graph-demo.json").read_text(encoding="utf-8"))
    assert demo["source"] == "seed"
    assert demo["nodes"]
    assert (site / "static" / "graph-app.js").is_file()
    assert (site / ".nojekyll").is_file()
    assert (site / "docs" / "PRD.md").is_file()
    assert (site / "docs" / "COMMUNITY_AUTODEVELOP.md").is_file()
