from __future__ import annotations

import asyncio
import json
import logging
import shutil
import subprocess
from pathlib import Path
from typing import Annotated

import typer
import uvicorn
from rich.console import Console
from rich.table import Table

from hermes_maintainer.config import load_settings
from hermes_maintainer.db import Database
from hermes_maintainer.git.mirror import ensure_mirror
from hermes_maintainer.github.client import GitHubClient
from hermes_maintainer.github.ingest import deep_enrich_prs, fast_scan
from hermes_maintainer.github.origin_policy import (
    EXIT_ORIGIN_WRITES_REFUSED,
    classify_origin_writes,
    fetch_origin_policy_documents,
    load_policy_documents,
)
from hermes_maintainer.optimizer.cpsat import solve_cpsat
from hermes_maintainer.optimizer.greedy import solve_greedy
from hermes_maintainer.scheduler.runner import analyze as run_analysis
from hermes_maintainer.scheduler.runner import daemon as run_daemon

app = typer.Typer(no_args_is_help=True, help="Repository maintenance intelligence for any GitHub repo")
console = Console()

RepoFlag = Annotated[
    str | None,
    typer.Option("--repo", help="GitHub owner/name (default: config [repo].name)"),
]
PolicyDirFlag = Annotated[
    Path | None,
    typer.Option(
        "--policy-dir",
        exists=True,
        file_okay=False,
        help="Offline policy documents (tests/fixtures). Default: GET from GitHub.",
    ),
]


def settings(repo: str | None = None):
    try:
        return load_settings(repo=repo)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


@app.command()
def init(
    fetch_git: bool = typer.Option(True, help="Clone/fetch the git mirror"),
    repo: RepoFlag = None,
):
    """Initialize the data directory, SQLite schema, and optionally the git mirror."""
    s = settings(repo)
    s.paths.data_dir.mkdir(parents=True, exist_ok=True)
    db = Database(s.paths.database)
    db.initialize()
    if fetch_git:
        ensure_mirror(s.repo.clone_url, s.paths.mirror_dir)
    console.print(f"[green]initialized[/green] {s.paths.data_dir} ({s.repo.name})")


@app.command()
def scan(
    mode: str = typer.Option("fast", help="fast or deep"),
    repo: RepoFlag = None,
):
    """Fetch repository state into the local graph."""
    s = settings(repo)
    ensure_mirror(s.repo.clone_url, s.paths.mirror_dir)
    if mode == "fast":
        result = fast_scan(s)
    elif mode == "deep":
        result = {"fast": fast_scan(s), "deep": deep_enrich_prs(s)}
    else:
        raise typer.BadParameter("mode must be fast or deep")
    console.print_json(json.dumps(result))


@app.command()
def analyze(repo: RepoFlag = None):
    """Rebuild similarity edges, campaigns, fix atoms, and health metrics."""
    result = run_analysis(settings(repo))
    console.print_json(json.dumps(result))


@app.command()
def optimize(
    method: str = typer.Option("greedy", help="greedy or cpsat"),
    max_atoms: int = typer.Option(30, min=1, max=500),
    repo: RepoFlag = None,
):
    """Propose a high-coverage fix-atom selection."""
    s = settings(repo)
    db = Database(s.paths.database)
    db.initialize()
    result = solve_greedy(db, max_atoms) if method == "greedy" else solve_cpsat(db, max_atoms)
    console.print_json(json.dumps(result))


@app.command()
def serve(
    host: str | None = typer.Option(None),
    port: int | None = typer.Option(None),
    repo: RepoFlag = None,
):
    """Run the local dashboard and API."""
    s = settings(repo)
    uvicorn.run("hermes_maintainer.api.app:create_app", factory=True, host=host or s.server.host, port=port or s.server.port)


@app.command()
def daemon(repo: RepoFlag = None):
    """Continuously run fast and deep batched scans."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    asyncio.run(run_daemon(settings(repo)))


@app.command()
def doctor(repo: RepoFlag = None):
    """Validate local prerequisites and print repository-maintainer status."""
    s = settings(repo)
    table = Table(title="hermes-maintainer doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Detail")

    table.add_row("repo", "OK", s.repo.name)
    git = shutil.which("git")
    table.add_row("git", "OK" if git else "MISSING", git or "install git")
    table.add_row("GitHub token", "OK" if s.github_token else "WARN", "configured" if s.github_token else "public API limits apply")
    table.add_row("database", "OK" if s.paths.database.exists() else "NEW", str(s.paths.database))
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


@app.command("origin-preflight")
def origin_preflight(
    repo: RepoFlag = None,
    policy_dir: PolicyDirFlag = None,
):
    """Fail-closed origin-write preflight. Exit 2 unless writes are explicitly allowed."""
    s = settings(repo)
    target = s.repo.name
    if policy_dir is not None:
        documents = load_policy_documents(policy_dir)
    else:
        client = GitHubClient(s.github_token)
        try:
            documents = fetch_origin_policy_documents(client, target)
        finally:
            client.close()
    attestation = classify_origin_writes(target, documents)
    # Plain JSON so receipts/tests are not wrapped in Rich markup.
    print(json.dumps(attestation.to_dict(), indent=2))
    if not attestation.writes_permitted:
        raise typer.Exit(EXIT_ORIGIN_WRITES_REFUSED)


@app.command("seed-audit")
def seed_audit():
    """Print the bundled initial audit path for agent handoff."""
    s = settings()
    path = s.root / "seed" / "audit" / "HERMES_TRIAGE_AUDIT.md"
    console.print(path)


if __name__ == "__main__":
    app()
