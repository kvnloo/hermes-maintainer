from __future__ import annotations

import asyncio
import logging

from hermes_maintainer.analysis.campaigns import rebuild_campaigns
from hermes_maintainer.analysis.fix_atoms import rebuild_pr_atoms
from hermes_maintainer.analysis.health import snapshot_metrics
from hermes_maintainer.analysis.similarity import build_similarity_edges
from hermes_maintainer.config import Settings
from hermes_maintainer.db import Database
from hermes_maintainer.git.mirror import ensure_mirror
from hermes_maintainer.github.ingest import deep_enrich_prs, fast_scan

log = logging.getLogger(__name__)


def analyze(settings: Settings) -> dict:
    db = Database(settings.paths.database)
    db.initialize()
    return {
        "similarity": build_similarity_edges(settings),
        "campaigns": rebuild_campaigns(db),
        "atoms": rebuild_pr_atoms(settings),
        "metrics": snapshot_metrics(db),
    }


def run_fast_cycle(settings: Settings) -> dict:
    ensure_mirror(settings.repo.clone_url, settings.paths.mirror_dir)
    return {"scan": fast_scan(settings), "analysis": analyze(settings)}


def run_deep_cycle(settings: Settings) -> dict:
    ensure_mirror(settings.repo.clone_url, settings.paths.mirror_dir)
    return {
        "scan": fast_scan(settings),
        "deep": deep_enrich_prs(settings),
        "analysis": analyze(settings),
    }


async def daemon(settings: Settings) -> None:
    next_fast = 0.0
    next_deep = 0.0
    loop = asyncio.get_running_loop()
    while True:
        now = loop.time()
        try:
            if now >= next_deep:
                log.info("starting deep maintenance cycle")
                await asyncio.to_thread(run_deep_cycle, settings)
                next_deep = loop.time() + settings.scan.deep_interval_seconds
                next_fast = loop.time() + settings.scan.fast_interval_seconds
            elif now >= next_fast:
                log.info("starting fast maintenance cycle")
                await asyncio.to_thread(run_fast_cycle, settings)
                next_fast = loop.time() + settings.scan.fast_interval_seconds
        except Exception:
            log.exception("maintenance cycle failed; daemon will retry")
            next_fast = loop.time() + min(300, settings.scan.fast_interval_seconds)
        sleep_for = max(1.0, min(next_fast, next_deep) - loop.time())
        await asyncio.sleep(sleep_for)
