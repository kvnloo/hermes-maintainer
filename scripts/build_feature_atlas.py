#!/usr/bin/env python3
"""Build public, source-linked Hermes feature PRDs from versioned RFC manifests.

This is a static renderer, not an issue-status fetcher. Source facts are pinned
to the manifest snapshot and all GitHub links remain primary evidence.
"""
from __future__ import annotations

import html
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse

SCHEMA = "hermes-maintainer.prd-atlas.v1"
PUBLIC_BASE = "https://kvnloo.github.io/hermes-maintainer/features/"
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
GROUPS = (
    "Systems",
    "Intelligence",
    "Memory & Context",
    "Agents & Automation",
    "Interfaces",
    "Platform & Safety",
    "Reliability",
    "Public Impact",
    "Frontier Research",
)
REQUIRED_TEXT = ("slug", "title", "category", "stage", "tagline", "problem", "outcome", "credit")
REQUIRED_LISTS = ("journeys", "ownership", "phases", "acceptance", "risks", "metrics", "sources")


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_specs(root: Path) -> list[dict]:
    """Validate untrusted-looking source data before writing publishable HTML."""
    items: list[dict] = []
    seen: set[str] = set()
    for file in sorted((root / "specs").glob("*.json")):
        source = json.loads(file.read_text(encoding="utf-8"))
        if source.get("schema") != SCHEMA or source.get("snapshot") != "2026-10-20":
            raise ValueError(f"Invalid schema/snapshot: {file}")
        for item in source["items"]:
            for key in REQUIRED_TEXT:
                if not isinstance(item.get(key), str) or not item[key].strip():
                    raise ValueError(f"{file}: required text {key}")
            slug = item["slug"]
            if not SLUG.fullmatch(slug) or slug in seen or slug == "hermes-tern":
                raise ValueError(f"Duplicate or unsafe slug {slug!r}")
            if item["category"] not in GROUPS:
                raise ValueError(f"Unknown category: {slug}")
            for key in REQUIRED_LISTS:
                if not isinstance(item.get(key), list) or len(item[key]) < (2 if key in ("risks", "metrics") else 3):
                    raise ValueError(f"{slug}: insufficient {key}")
            for source_link in item["sources"]:
                url = source_link.get("url", "")
                parsed = urlparse(url)
                if parsed.scheme != "https" or parsed.hostname != "github.com" or not parsed.path.strip("/"):
                    raise ValueError(f"{slug}: untrusted source URL")
                if not source_link.get("label"):
                    raise ValueError(f"{slug}: unlabeled source")
            if item["category"] == "Frontier Research" and item["stage"] != "Research only":
                raise ValueError(f"{slug}: research cannot advertise production readiness")
            if len(item["problem"]) < 60 or len(item["outcome"]) < 65:
                raise ValueError(f"{slug}: missing real rationale")
            seen.add(slug)
            items.append(item)
    if not items:
        raise ValueError("No feature specs discovered")
    return items


def links(items: list[dict], class_name: str = "repo-link") -> str:
    return "\n".join(
        f'<a class="{class_name}" href="{esc(x["url"])}" target="_blank" rel="noopener noreferrer">'
        f'{esc(x["label"])} <span aria-hidden="true">↗</span></a>'
        for x in items
    )


def numbered(items: list[str], kind: str = "story") -> str:
    return "\n".join(
        f'<div class="{kind}"><span class="index" aria-hidden="true">{i:02}</span>'
        f'<div><p>{esc(text)}</p></div></div>'
        for i, text in enumerate(items, start=1)
    )


def cards(items: list[str], prefix: str) -> str:
    return "\n".join(
        f'<div class="card"><div class="num">{esc(prefix)} / {i:02}</div>'
        f'<p class="atlas-card-text">{esc(text)}</p></div>'
        for i, text in enumerate(items, start=1)
    )


def research_warning(item: dict) -> str:
    if item["stage"] != "Research only":
        return (
            '<div class="note" role="note"><strong>Evidence discipline.</strong> '
            'A prototype, merged fork branch and independently accepted upstream capability '
            'are different states. This PRD names intended behavior and links primary '
            'sources, not a claim that every stage is implemented.</div>'
        )
    return (
        '<div class="note research-warning" role="note">'
        '<strong>Research only · not authorized implementation.</strong> '
        'This RFC is a falsifiable hypothesis. Preserve the existing Hermes runtime, '
        'model permissions and human controls. No live agent rollout, product claim '
        'or merged feature follows from a positive toy experiment.</div>'
    )


def related_html(item: dict, all_items: list[dict]) -> str:
    siblings = [s for s in all_items if s["category"] == item["category"] and s["slug"] != item["slug"]][:4]
    if not siblings:
        return ""
    return (
        '<section class="section" aria-labelledby="related-title"><div class="section-head"><div>'
        '<span class="eyebrow">CONTINUE EXPLORING</span><h2 id="related-title" style="margin-top:10px">'
        'Related PRDs</h2></div></div><div class="atlas-related">'
        + "\n".join(
            f'<a class="card atlas-related-card" href="../{esc(s["slug"])}/">'
            f'<span class="eyebrow">{esc(s["category"])}</span>'
            f'<h3>{esc(s["title"])} <span aria-hidden="true">↗</span></h3>'
            f'<p>{esc(s["tagline"])}</p></a>'
            for s in siblings
        )
        + "</div></section>"
    )


def detail(item: dict, all_items: list[dict]) -> str:
    slug = esc(item["slug"])
    title = esc(item["title"])
    category = esc(item["category"])
    stage = esc(item["stage"])
    summary = esc(item["tagline"])
    source_count = len(item["sources"])
    badge = "amber" if item["stage"] == "Research only" else "gray"
    source_links = links(item["sources"])
    source_anchors = " ".join(
        f'<a href="{esc(link["url"])}">{esc(link["label"])}</a>'
        for link in item["sources"][:2]
    )
    phase_rows = "\n".join(
        f'<div class="timeline-item"><b>Phase {i} · {esc(text)}</b></div>'
        for i, text in enumerate(item["phases"], start=1)
    )
    acceptance_rows = "\n".join(
        '<div class="atlas-check"><span class="atlas-check-icon" aria-hidden="true">◇</span>'
        f'<span>{esc(text)}</span></div>' for text in item["acceptance"]
    )
    risk_rows = "\n".join(f'<li>{esc(risk)}</li>' for risk in item["risks"])
    metrics_rows = "\n".join(
        f'<li><span class="atlas-metric-dot" aria-hidden="true"></span>{esc(metric)}</li>'
        for metric in item["metrics"]
    )
    cards_owner = cards(item["ownership"], "BOUNDARY")
    journey_rows = numbered(item["journeys"])
    aside = (
        '<aside class="aside" aria-label="PRD navigation">'
        '<div class="paper navcard"><h3>Contents</h3>'
        '<a href="#problem">01 · Product problem</a><a href="#experience">02 · Use cases</a>'
        '<a href="#authority">03 · Architecture</a><a href="#delivery">04 · Work plan</a>'
        '<a href="#evidence">05 · Acceptance</a><a href="#risks">06 · Risks</a>'
        '<a href="#sources">07 · Sources & credits</a></div>'
        f'<div class="paper navcard"><h3>Primary sources</h3>{source_links}</div>'
        '<div class="note">Status is a dated source snapshot, not a live project tracker. '
        'Current decisions and reviews live in the linked issues and PRs.</div>'
        '</aside>'
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#f8f9fc">
<meta name="description" content="{summary}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title} · Hermes public PRD">
<meta property="og:description" content="{summary}">
<link rel="canonical" href="{PUBLIC_BASE}{slug}/">
<link rel="stylesheet" href="../assets/prd.css">
<title>{title} · Hermes feature PRD</title>
</head>
<body>
<header class="topbar"><div class="bar-inner">
<a class="brand" href="../../"><span class="mark" aria-hidden="true">H</span> hermes-maintainer
<span style="color:#a7afbb;font-weight:500;margin-left:3px">/ product</span></a>
<nav class="bar-links" aria-label="Global">
<a href="../../">Maintainer dashboard</a>
<a href="../" aria-current="page">Feature library</a>
<a class="top-cta" href="{esc(item["sources"][0]["url"])}">Source RFC ↗</a>
</nav></div></header>
<main class="wrap">
<div class="crumb"><a href="../../">Overview</a><span aria-hidden="true">/</span>
<a href="../">Features</a><span aria-hidden="true">/</span> {title}</div>
<section class="hero narrow" aria-labelledby="prd-title">
<div class="hero-line"><span class="kicker"><span class="dot"></span>{category.upper()} / RFC ATLAS</span>
<span class="pill {badge}">{stage}</span><span class="micro">Snapshot · Oct 20, 2026</span></div>
<h1 id="prd-title">{title}<span style="color:#87a9fb">.</span></h1>
<p class="lede">{summary}</p>
<div class="hero-actions"><a class="btn primary" href="#experience">Read the PRD <span aria-hidden="true">↘</span></a>
<a class="btn" href="{esc(item["sources"][0]["url"])}">Open primary RFC ↗</a>
<a class="btn" href="../">All Hermes initiatives ↗</a></div></section>
<div class="meta-grid" aria-label="Specification facts">
<div class="meta-item"><span>Domain</span><b>{category}</b></div>
<div class="meta-item"><span>Phase</span><b>{stage}</b></div>
<div class="meta-item"><span>Primary sources</span><b>{source_count} links</b></div>
<div class="meta-item"><span>Authority</span><b>Hermes + human</b></div>
</div>
<div class="layout"><article class="content">
<section class="section" id="problem"><div class="section-head"><div>
<span class="eyebrow">01 / PURPOSE</span><h2 style="margin-top:10px">The problem worth solving</h2>
</div></div><div class="paper panel">
<p class="atlas-lede">{esc(item["problem"])}</p>
<h3>Desired outcome</h3><p class="atlas-body">{esc(item["outcome"])}</p>
{research_warning(item)}
</div></section>
<section class="section" id="experience"><div class="section-head"><div>
<span class="eyebrow">02 / PEOPLE & USE CASES</span><h2 style="margin-top:10px">Experience contract</h2>
<p>Target journeys and observable behavior. These are product/research requirements, not claims of completed work.</p>
</div></div><div class="paper">{journey_rows}</div></section>
<section class="section" id="authority"><div class="section-head"><div>
<span class="eyebrow">03 / SYSTEM BOUNDARY</span><h2 style="margin-top:10px">What owns what?</h2>
<p>Keep security, authority and source provenance explicit as the design evolves.</p>
</div></div><div class="atlas-owners">{cards_owner}</div></section>
<section class="section" id="delivery"><div class="section-head"><div>
<span class="eyebrow">04 / EXECUTION PLAN</span><h2 style="margin-top:10px">Small steps with evidence</h2>
</div></div><div class="paper panel"><div class="timeline">{phase_rows}</div></div></section>
<section class="section" id="evidence"><div class="section-head"><div>
<span class="eyebrow">05 / VERIFICATION</span><h2 style="margin-top:10px">Definition of done</h2>
<p>Each criterion must be checked on an exact head, with independent outcome evidence where applicable.</p>
</div></div><div class="paper atlas-acceptance">{acceptance_rows}</div>
<div class="paper panel" style="margin-top:15px"><span class="eyebrow">SUCCESS SIGNALS</span>
<ul class="atlas-metrics">{metrics_rows}</ul></div></section>
<section class="section" id="risks"><div class="section-head"><div>
<span class="eyebrow">06 / TRADEOFFS</span><h2 style="margin-top:10px">What can go wrong</h2>
</div></div><div class="paper panel"><ul class="atlas-risks">{risk_rows}</ul>
<p class="small">Do not treat proposed improvements, historical benchmarks or downstream branches as upstream acceptance.</p>
</div></section>
<section class="section" id="sources"><div class="section-head"><div>
<span class="eyebrow">07 / TRACEABILITY</span><h2 style="margin-top:10px">Source RFCs and provenance</h2>
</div></div><div class="paper panel"><div class="atlas-source-links">{source_links}</div>
<h3 style="margin-top:20px">Credit & source ownership</h3><p class="atlas-body">{esc(item["credit"])}</p>
<p class="small">Start with {source_anchors}. GitHub remains the canonical source for live progress and reviewer decisions.</p>
</div></section>
{related_html(item,all_items)}
</article>{aside}</div>
<footer class="footer"><span>{title} · Public specification, not a deployed feature · Oct 20, 2026</span>
<span><a href="../">All initiatives</a> · <a href="https://github.com/kvnloo/hermes-maintainer">Source repository ↗</a></span></footer>
</main></body></html>
"""


def cards_index(items: list[dict]) -> str:
    """Generate a searchable, category-grouped feature list beside the Tern PRD."""
    by_group: dict[str, list[dict]] = defaultdict(list)
    for item in items:
        by_group[item["category"]].append(item)
    sections: list[str] = []
    for group in GROUPS:
        docs = by_group.get(group)
        if not docs:
            continue
        group_slug = re.sub(r"[^a-z0-9]+", "-", group.lower()).strip("-")
        rows: list[str] = []
        for item in sorted(docs, key=lambda d: d["title"].lower()):
            slug = esc(item["slug"])
            title = esc(item["title"])
            stage = esc(item["stage"])
            category = esc(item["category"])
            summary = esc(item["tagline"])
            search = esc(
                " ".join((item["title"], item["category"], item["tagline"], item["problem"], item["slug"]))
                .lower()
            )
            short = "".join(x[0] for x in item["title"].split()[:2]).upper()
            badge = "amber" if item["stage"] == "Research only" else "gray"
            rows.append(
                f'<article class="paper feature-row atlas-feature-row" data-search="{search}">'
                f'<div class="feature-mark atlas-feature-mark" aria-hidden="true">{esc(short)}</div>'
                f'<div><div class="tagline"><span class="pill {badge}">{stage}</span>'
                f'<span class="micro">{category} · Oct 20, 2026</span></div>'
                f'<h3><a href="./{slug}/">{title}</a></h3><p>{summary}</p></div>'
                f'<a href="./{slug}/" class="btn feature-cta">Read PRD ↗</a></article>'
            )
        sections.append(
            f'<section class="atlas-category" data-prd-category id="category-{group_slug}"'
            f' aria-labelledby="heading-{group_slug}">'
            f'<div class="atlas-category-heading"><h3 id="heading-{group_slug}">{esc(group)}</h3>'
            f'<span class="pill gray">{len(docs)} specifications</span></div>'
            + "\n".join(rows) + "</section>"
        )
    return "\n".join(sections)


def build_atlas(feature_dir: Path, source_dir: Path) -> list[Path]:
    """Write complete, direct-link HTML pages into the pre-copied Pages tree."""
    specs = load_specs(source_dir)
    output: list[Path] = []
    for item in specs:
        target = feature_dir / item["slug"] / "index.html"
        if target.exists():
            raise ValueError(f"Atlas collision with manually authored page: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(detail(item, specs), encoding="utf-8")
        output.append(target)
    index_path = feature_dir / "index.html"
    index = index_path.read_text(encoding="utf-8")
    anchor = '<p class="empty" id="search-empty"'
    if index.count(anchor) != 1:
        raise ValueError("Feature index injection anchor missing/duplicated")
    index = index.replace(anchor, cards_index(specs) + "\n      " + anchor, 1)
    index = index.replace("1 published spec", f"{len(specs)+1} source-backed specs")
    index_path.write_text(index, encoding="utf-8")
    catalogue = [
        {
            "slug": item["slug"],
            "title": item["title"],
            "category": item["category"],
            "stage": item["stage"],
            "path": f"./{item['slug']}/",
            "snapshot": "2026-10-20",
            "source_count": len(item["sources"]),
        }
        for item in specs
    ]
    (feature_dir / "catalog.json").write_text(
        json.dumps(catalogue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return output


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--source", type=Path, default=Path("features"))
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    build_atlas(args.out, args.source)
