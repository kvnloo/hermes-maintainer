#!/usr/bin/env python3
"""Build a static GitHub Pages snapshot of llms.txt, docs, and the dashboard.

The live FastAPI app is local-only. Pages serves the polished UI against audit
seed campaigns plus copied markdown. Does not merge. Does not write GitHub.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fastapi.testclient import TestClient

from hermes_maintainer.api.app import create_app
from hermes_maintainer.db import Database

ADAPTER_JS = """(() => {
  const orig = window.fetch.bind(window);
  function fileFor(url) {
    const raw = String(url);
    const [path, qs] = raw.split("?");
    const q = new URLSearchParams(qs || "");
    if (path === "/api/nodes" && q.get("kind") === "pr") return "./api/nodes-pr.json";
    if (path === "/api/nodes") return "./api/nodes-issue.json";
    if (path === "/api/optimizer/greedy") return "./api/optimizer-greedy.json";
    if (path === "/api/graph/demo" || path === "/api/graph") return "./api/graph-demo.json";
    if (path === "/api/campaigns") return "./api/campaigns.json";
    if (path.startsWith("/api/campaigns/") && path.endsWith("/graph")) return "./api/graph-demo.json";
    if (path.startsWith("/api/campaigns/")) return "./api/campaigns.json";
    const map = {
      "/api/health": "./api/health.json",
      "/api/root-causes": "./api/root-causes.json",
      "/api/filters": "./api/filters.json",
    };
    return map[path] || ("./api" + path.slice(4).replace(/\\/+$/, "") + ".json");
  }
  window.fetch = (url, opts) => {
    const s = typeof url === "string" ? url : (url && url.url) || String(url);
    if (typeof s === "string" && s.startsWith("/api/")) {
      return orig(fileFor(s), opts);
    }
    return orig(url, opts);
  };
})();
"""

BANNER = (
    '<p id="pages-banner" class="banner">'
    "GitHub Pages snapshot of the dashboard (audit seed campaigns). "
    "Live scans run locally via <code>hermes-maintainer serve</code>."
    "</p>"
)


def dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n", encoding="utf-8")


def snapshot_api(site: Path) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="hermes-pages-"))
    db = Database(tmp / "pages.db")
    db.initialize()
    client = TestClient(create_app(database=db))
    mapping = {
        "api/health.json": "/api/health",
        "api/campaigns.json": "/api/campaigns?limit=30",
        "api/root-causes.json": "/api/root-causes",
        "api/optimizer-greedy.json": "/api/optimizer/greedy?max_atoms=20",
        "api/nodes-issue.json": "/api/nodes?kind=issue&state=open&limit=250",
        "api/nodes-pr.json": "/api/nodes?kind=pr&state=open&limit=250",
        "api/filters.json": "/api/filters",
        "api/graph-demo.json": "/api/graph/demo",
    }
    for rel, url in mapping.items():
        response = client.get(url)
        if response.status_code != 200:
            raise SystemExit(f"snapshot failed {url}: {response.status_code}")
        dump_json(site / rel, response.json())


def rewrite_index(src: Path, dest: Path) -> None:
    html = src.read_text(encoding="utf-8")
    html = html.replace('href="/static/', 'href="./static/')
    html = html.replace('src="/static/', 'src="./static/')
    html = html.replace('href="/llms.txt"', 'href="./llms.txt"')
    html = html.replace('href="/README.md"', 'href="./README.md"')
    insert = (
        BANNER
        + "\n  <script src=\"./pages-adapter.js\"></script>\n"
        + '  <script>if (!location.hash) location.hash = "graph";</script>\n'
    )
    html = html.replace("<body>", "<body>\n  " + insert, 1)
    dest.write_text(html, encoding="utf-8")


def write_docs_index(docs_dir: Path, dest: Path) -> None:
    files = sorted(p.name for p in docs_dir.glob("*.md"))
    items = "\n".join(f'    <li><a href="./{name}">{name}</a></li>' for name in files)
    dest.write_text(
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\" />"
        "<title>hermes-maintainer docs</title></head><body>\n"
        "<h1>hermes-maintainer docs</h1>\n<ul>\n"
        f"{items}\n"
        "</ul>\n<p><a href=\"../\">Dashboard</a> · <a href=\"../llms.txt\">llms.txt</a></p>\n"
        "</body></html>\n",
        encoding="utf-8",
    )


def copy_markdown(site: Path) -> None:
    for name in ("llms.txt", "README.md", "GET_STARTED.md", "CONTRIBUTING.md", "SECURITY.md"):
        src = ROOT / name
        if src.is_file():
            shutil.copyfile(src, site / name)
    docs_src = ROOT / "docs"
    docs_dest = site / "docs"
    if docs_src.is_dir():
        if docs_dest.exists():
            shutil.rmtree(docs_dest)
        shutil.copytree(docs_src, docs_dest)
        write_docs_index(docs_src, docs_dest / "index.html")


def build(out: Path) -> Path:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / ".nojekyll").write_text("", encoding="utf-8")
    static_src = ROOT / "src" / "hermes_maintainer" / "ui" / "static"
    static_dest = out / "static"
    shutil.copytree(static_src, static_dest)
    rewrite_index(static_src / "index.html", out / "index.html")
    (out / "pages-adapter.js").write_text(ADAPTER_JS, encoding="utf-8")
    copy_markdown(out)
    snapshot_api(out)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build static GitHub Pages site/")
    parser.add_argument("--out", default=str(ROOT / "site"))
    args = parser.parse_args()
    out = Path(args.out).resolve()
    build(out)
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
