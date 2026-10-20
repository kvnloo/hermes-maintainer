"""Reproducible, public-only checks for the Hermes RFC feature PRD atlas."""
from __future__ import annotations

import runpy
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "features"
BUILDER = ROOT / "scripts" / "build_feature_atlas.py"


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: set[str] = set()
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag in ("a", "link") and values.get("href"):
            self.hrefs.add(values["href"] or "")
        if values.get("id"):
            self.ids.add(values["id"] or "")


def test_research_source_coverage_and_falsification() -> None:
    module = runpy.run_path(str(BUILDER))
    specs = module["load_specs"](FEATURES)
    assert len(specs) >= 30
    slugs = {s["slug"] for s in specs}
    assert len(slugs) == len(specs)
    assert "hermes-tern" not in slugs  # separately authored original PRD
    assert {"hermes-lab", "unified-memory", "semantic-computer-use", "bend-proof-verification"} <= slugs
    research = [s for s in specs if s["category"] == "Frontier Research"]
    assert len(research) == 10
    assert all(s["stage"] == "Research only" for s in research)
    for spec in research:
        assert "falsif" in " ".join(spec["acceptance"]).lower()
        assert len(spec["sources"]) >= 3


def test_every_source_is_public_and_author_credit_explicit() -> None:
    module = runpy.run_path(str(BUILDER))
    specs = module["load_specs"](FEATURES)
    for spec in specs:
        assert len(spec["sources"]) >= 3
        assert all(link["url"].startswith("https://github.com/") for link in spec["sources"])
        assert spec["credit"].strip()
        assert len(spec["phases"]) >= 3
        assert len(spec["acceptance"]) >= 3
        assert len(spec["metrics"]) >= 2


def test_full_static_pages_and_searchable_index(tmp_path: Path) -> None:
    import shutil

    feature_dir = tmp_path / "features"
    shutil.copytree(FEATURES, feature_dir)
    module = runpy.run_path(str(BUILDER))
    specs = module["load_specs"](FEATURES)
    pages = module["build_atlas"](feature_dir, FEATURES)
    assert len(pages) == len(specs)
    assert all(page.is_file() for page in pages)
    assert (feature_dir / "catalog.json").is_file()
    index = (feature_dir / "index.html").read_text(encoding="utf-8")
    assert "source-backed specs" in index
    assert 'id="feature-search"' in index
    assert "./hermes-tern/" in index
    for spec in specs:
        assert f'./{spec["slug"]}/' in index
        page = feature_dir / spec["slug"] / "index.html"
        html = page.read_text(encoding="utf-8")
        parsed = Links()
        parsed.feed(html)
        assert {"problem", "experience", "authority", "delivery", "evidence", "risks", "sources"} <= parsed.ids
        assert "../assets/prd.css" in parsed.hrefs
        assert all(ref["url"] in parsed.hrefs for ref in spec["sources"])
        assert "Snapshot · Oct 20, 2026" in html
        if spec["stage"] == "Research only":
            assert "not authorized implementation" in html
    assert not (feature_dir / "hermes-tern" / "index.html").read_text(encoding="utf-8").startswith("<!doctype generated")


def test_invalid_manifest_duplicate_slug_fails_closed(tmp_path: Path) -> None:
    import json

    folder = tmp_path / "specs"
    folder.mkdir()
    module = runpy.run_path(str(BUILDER))
    item = {
        "slug": "../wrong",
        "title": "Unsafe",
        "category": "Systems",
        "stage": "Research only",
        "tagline": "Not a real PRD",
        "problem": "A" * 70,
        "outcome": "B" * 70,
        "credit": "Unknown",
        "journeys": ["one", "two", "three"],
        "ownership": ["one", "two", "three"],
        "phases": ["one", "two", "three"],
        "acceptance": ["one", "two", "three"],
        "risks": ["one", "two"],
        "metrics": ["one", "two"],
        "sources": [
            {"url": "https://github.com/a/b", "label": "A"},
            {"url": "https://github.com/a/c", "label": "B"},
            {"url": "https://github.com/a/d", "label": "C"},
        ],
    }
    folder.joinpath("broken.json").write_text(
        json.dumps(
            {"schema": "hermes-maintainer.prd-atlas.v1", "snapshot": "2026-10-20", "items": [item]}
        ),
        encoding="utf-8",
    )
    from pytest import raises

    with raises(ValueError, match="slug"):
        module["load_specs"](tmp_path)
