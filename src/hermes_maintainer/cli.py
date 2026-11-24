from __future__ import annotations

import asyncio
import json
import logging
import shutil
import subprocess
import sys
from pathlib import Path

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from hermes_maintainer.config import find_config, load_settings
from hermes_maintainer.db import Database
from hermes_maintainer.git.mirror import ensure_mirror
from hermes_maintainer.github.client import RateLimitError
from hermes_maintainer.github.ingest import deep_enrich_prs, fast_scan
from hermes_maintainer.graph.demo import import_seed_graph
from hermes_maintainer.optimizer.cpsat import solve_cpsat
from hermes_maintainer.optimizer.greedy import solve_greedy
from hermes_maintainer.scheduler.runner import analyze as run_analysis
from hermes_maintainer.scheduler.runner import daemon as run_daemon

app = typer.Typer(no_args_is_help=True, help="Hermes repository maintenance intelligence")
console = Console()


def settings():
    return load_settings()


@app.command()
def init(
    fetch_git: bool = typer.Option(
        True, help="Clone/fetch the full git mirror of the target repo (multi-GB for hermes-agent)"
    ),
    demo: bool = typer.Option(False, help="Load the bundled audit seed campaigns as demo data"),
):
    """Initialize the data directory, SQLite schema, and optionally the git mirror."""
    s = settings()
    s.paths.data_dir.mkdir(parents=True, exist_ok=True)
    db = Database(s.paths.database)
    db.initialize()
    if demo:
        counts = import_seed_graph(db, s.root, s.repo.name)
        console.print(f"[green]demo data[/green] {json.dumps(counts)}")
    if fetch_git:
        ensure_mirror(s.repo.clone_url, s.paths.mirror_dir)
    console.print(f"[green]initialized[/green] {s.paths.data_dir}")


@app.command()
def scan(
    mode: str = typer.Option("fast", help="fast or deep"),
    limit: int | None = typer.Option(
        None, min=1, help="Max issues and PRs (each) to fetch; keeps unauthenticated runs small"
    ),
    mirror: bool = typer.Option(False, help="Also clone/fetch the full git mirror first"),
):
    """Fetch repository state into the local graph (GitHub REST; GITHUB_TOKEN optional)."""
    s = settings()
    if mode not in {"fast", "deep"}:
        raise typer.BadParameter("mode must be fast or deep")
    if mirror:
        ensure_mirror(s.repo.clone_url, s.paths.mirror_dir)
    try:
        if mode == "fast":
            result = fast_scan(s, limit=limit)
        else:
            result = {"fast": fast_scan(s, limit=limit), "deep": deep_enrich_prs(s, limit=limit)}
    except RateLimitError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(2) from exc
    console.print_json(json.dumps(result))


@app.command()
def analyze():
    """Rebuild similarity edges, campaigns, fix atoms, and health metrics."""
    result = run_analysis(settings())
    console.print_json(json.dumps(result))


@app.command()
def optimize(
    method: str = typer.Option("greedy", help="greedy or cpsat"),
    max_atoms: int = typer.Option(30, min=1, max=500),
):
    """Propose a high-coverage fix-atom selection."""
    s = settings()
    db = Database(s.paths.database)
    db.initialize()
    result = solve_greedy(db, max_atoms) if method == "greedy" else solve_cpsat(db, max_atoms)
    console.print_json(json.dumps(result))


@app.command()
def serve(
    host: str | None = typer.Option(None),
    port: int | None = typer.Option(None),
):
    """Run the local dashboard and API."""
    s = settings()
    uvicorn.run("hermes_maintainer.api.app:create_app", factory=True, host=host or s.server.host, port=port or s.server.port)


@app.command()
def daemon():
    """Continuously run fast and deep batched scans."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    asyncio.run(run_daemon(settings()))


@app.command()
def doctor():
    """Validate local prerequisites and print repository-maintainer status."""
    s = settings()
    table = Table(title="hermes-maintainer doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")
    failed = False

    py_ok = sys.version_info >= (3, 11)
    failed |= not py_ok
    table.add_row("python", "OK" if py_ok else "FAIL", sys.version.split()[0] + " (need >= 3.11)")
    config_path = find_config()
    table.add_row("config", "OK" if config_path else "DEFAULT", str(config_path or "built-in defaults"))
    git = shutil.which("git")
    table.add_row("git", "OK" if git else "WARN", git or "only needed for `scan --mirror` / daemon")
    table.add_row(
        "GitHub token",
        "OK" if s.github_token else "WARN",
        "GITHUB_TOKEN set (5000 req/h)" if s.github_token
        else "unset: 60 req/h, use `scan --limit` or export GITHUB_TOKEN",
    )
    static = Path(__file__).parent / "ui" / "static"
    bundle_ok = (static / "graph-app.js").is_file() and (static / "index.html").is_file()
    failed |= not bundle_ok
    table.add_row("ui bundle", "OK" if bundle_ok else "FAIL", str(static / "graph-app.js")
                  if bundle_ok else "run scripts/build-ui.sh")
    seed = s.root / "seed" / "audit" / "campaign_seeds.json"
    table.add_row("seed data", "OK" if seed.is_file() else "WARN", str(seed))
    if s.paths.database.exists():
        db = Database(s.paths.database)
        db.initialize()
        total = db.scalar("SELECT COUNT(*) FROM nodes") or 0
        seeded = db.scalar(
            "SELECT COUNT(*) FROM nodes WHERE json_extract(metadata_json,'$.seed')=1"
        ) or 0
        table.add_row("database", "OK", f"{s.paths.database} ({total} nodes, {seeded} demo seed)")
    else:
        table.add_row("database", "NEW", f"{s.paths.database} (run `init --demo`)")
    table.add_row("mirror", "OK" if s.paths.mirror_dir.exists() else "NEW", str(s.paths.mirror_dir))
    if git and s.paths.mirror_dir.exists():
        p = subprocess.run(
            [git, "fsck", "--no-dangling"],
            cwd=s.paths.mirror_dir,
            capture_output=True,
            text=True,
            check=False,
        )
        table.add_row("git fsck", "OK" if p.returncode == 0 else "FAIL", (p.stderr or p.stdout).strip()[:140])
    console.print(table)
    if failed:
        raise typer.Exit(1)


@app.command("seed-audit")
def seed_audit():
    """Print the bundled initial audit path for agent handoff."""
    s = settings()
    path = s.root / "seed" / "audit" / "HERMES_TRIAGE_AUDIT.md"
    console.print(path)


if __name__ == "__main__":
    app()
