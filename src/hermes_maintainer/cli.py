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
from hermes_maintainer.github.ingest import deep_enrich_prs, fast_scan
from hermes_maintainer.optimizer.cpsat import solve_cpsat
from hermes_maintainer.optimizer.greedy import solve_greedy
from hermes_maintainer.reports import ingest as ingest_report
from hermes_maintainer.reports import list_reports
from hermes_maintainer.reports import load as load_report
from hermes_maintainer.reports import promote as promote_report
from hermes_maintainer.scheduler.runner import analyze as run_analysis
from hermes_maintainer.scheduler.runner import daemon as run_daemon

app = typer.Typer(no_args_is_help=True, help="Hermes repository maintenance intelligence")
report_app = typer.Typer(no_args_is_help=True, help="Local complaint inbox. Never writes GitHub.")
app.add_typer(report_app, name="report")
console = Console()


def settings():
    return load_settings()


@app.command()
def init(fetch_git: bool = typer.Option(True, help="Clone/fetch the git mirror")):
    """Initialize the data directory, SQLite schema, and optionally the git mirror."""
    s = settings()
    s.paths.data_dir.mkdir(parents=True, exist_ok=True)
    db = Database(s.paths.database)
    db.initialize()
    if fetch_git:
        ensure_mirror(s.repo.clone_url, s.paths.mirror_dir)
    console.print(f"[green]initialized[/green] {s.paths.data_dir}")


@app.command()
def scan(mode: str = typer.Option("fast", help="fast or deep")):
    """Fetch repository state into the local graph."""
    s = settings()
    ensure_mirror(s.repo.clone_url, s.paths.mirror_dir)
    if mode == "fast":
        result = fast_scan(s)
    elif mode == "deep":
        result = {"fast": fast_scan(s), "deep": deep_enrich_prs(s)}
    else:
        raise typer.BadParameter("mode must be fast or deep")
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


@app.command("seed-audit")
def seed_audit():
    """Print the bundled initial audit path for agent handoff."""
    s = settings()
    path = s.root / "seed" / "audit" / "HERMES_TRIAGE_AUDIT.md"
    console.print(path)


def _data_dir(data_dir: Path | None):
    if data_dir is not None:
        return data_dir
    return settings().paths.data_dir


@report_app.command("ingest")
def report_ingest(
    title: Annotated[str, typer.Option(help="Short complaint title")],
    body: Annotated[str, typer.Option(help="Complaint body / repro notes")] = "",
    body_file: Annotated[Path | None, typer.Option(help="Read body from a file")] = None,
    target_repo: Annotated[str, typer.Option()] = "NousResearch/hermes-agent",
    duplicate_of: Annotated[str | None, typer.Option()] = None,
    competing_pr: Annotated[bool, typer.Option()] = False,
    data_dir: Annotated[Path | None, typer.Option(help="Inbox parent directory")] = None,
):
    """Capture a complaint as a local draft. Does not open GitHub issues."""
    text = body_file.read_text(encoding="utf-8") if body_file is not None else body
    record = ingest_report(
        _data_dir(data_dir),
        title=title,
        body=text,
        target_repo=target_repo,
        duplicate_of=duplicate_of,
        competing_pr=competing_pr,
    )
    console.print_json(json.dumps(record))


@report_app.command("list")
def report_list(
    data_dir: Annotated[Path | None, typer.Option()] = None,
):
    """List local drafts."""
    rows = list_reports(_data_dir(data_dir))
    console.print_json(
        json.dumps(
            [
                {
                    "id": row.get("id"),
                    "title": row.get("title"),
                    "disposition": (row.get("intake") or {}).get("disposition"),
                    "origin_write_permitted": (row.get("intake") or {}).get("origin_write_permitted"),
                    "performed_origin_write": (row.get("intake") or {}).get("performed_origin_write"),
                }
                for row in rows
            ]
        )
    )


@report_app.command("show")
def report_show(
    report_id: Annotated[str, typer.Argument()],
    data_dir: Annotated[Path | None, typer.Option()] = None,
):
    """Print one local report."""
    console.print_json(json.dumps(load_report(_data_dir(data_dir), report_id)))


@report_app.command("promote")
def report_promote(
    report_id: Annotated[str, typer.Argument()],
    action: Annotated[str, typer.Option()] = "promote_issue",
    reproduced: Annotated[bool, typer.Option()] = False,
    in_scope: Annotated[bool, typer.Option()] = False,
    origin_policy: Annotated[str, typer.Option()] = "unknown",
    github_writes: Annotated[bool, typer.Option()] = False,
    human_or_policy_allow: Annotated[bool, typer.Option()] = False,
    claimed: Annotated[bool, typer.Option()] = False,
    has_receipt: Annotated[bool, typer.Option()] = False,
    data_dir: Annotated[Path | None, typer.Option()] = None,
):
    """Reclassify a draft against the intake ladder. Still does not write GitHub."""
    record = promote_report(
        _data_dir(data_dir),
        report_id,
        action=action,
        reproduced=reproduced,
        in_scope=in_scope,
        origin_policy=origin_policy,
        github_writes=github_writes,
        human_or_policy_allow=human_or_policy_allow,
        claimed=claimed,
        has_receipt=has_receipt,
    )
    console.print_json(json.dumps(record))


if __name__ == "__main__":
    app()
