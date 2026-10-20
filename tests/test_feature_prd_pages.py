"""Static PRD-site contract checks (no browser, providers or network required)."""
from __future__ import annotations

import runpy
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURES = ROOT / "features"


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()
        self.urls: list[str] = []
        self.titles = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if data.get("id"):
            self.ids.add(data["id"] or "")
        if tag == "title":
            self.titles += 1
        for field in ("href", "src", "data"):
            if tag == "object" and field == "data" or field in ("href", "src"):
                if data.get(field):
                    self.urls.append(data[field] or "")


def parse_page(path: Path) -> PageParser:
    page = PageParser()
    page.feed(path.read_text(encoding="utf-8"))
    assert page.titles == 1
    return page


def test_feature_prd_has_all_required_sections() -> None:
    page = parse_page(FEATURES / "hermes-tern" / "index.html")
    required = {
        "overview", "requirements", "visual", "architecture", "reuse",
        "acceptance", "roadmap", "decisions", "references",
    }
    assert required.issubset(page.ids)
    assert "../../docs/assets/hermes-tern-overview.svg" in page.urls
    assert "../assets/prd.css" in page.urls
    assert "https://github.com/kvnloo/hermes-agent/issues/636" in page.urls
    assert "https://github.com/NousResearch/hermes-agent/pull/141923" in page.urls


def test_library_links_to_feature_and_supports_filtering() -> None:
    index = FEATURES / "index.html"
    page = parse_page(index)
    html = index.read_text(encoding="utf-8")
    assert "./hermes-tern/" in page.urls
    assert "./assets/prd.css" in page.urls
    assert "feature-search" in page.ids
    assert "addEventListener('input', filter)" in html
    assert "[hidden]{display:none!important;}" in (FEATURES / "assets" / "prd.css").read_text(encoding="utf-8")


def test_static_pages_builder_publishes_clean_feature_routes(tmp_path: Path) -> None:
    module = runpy.run_path(str(ROOT / "scripts" / "build-pages.py"))
    module["copy_feature_specs"](tmp_path)
    assert (tmp_path / "features" / "index.html").is_file()
    assert (tmp_path / "features" / "assets" / "prd.css").is_file()
    assert (tmp_path / "features" / "hermes-tern" / "index.html").is_file()
    assert (tmp_path / "features" / "README.md").is_file()
