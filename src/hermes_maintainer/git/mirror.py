from __future__ import annotations

import subprocess
from pathlib import Path


def _run(args: list[str], cwd: Path | None = None) -> str:
    proc = subprocess.run(args, cwd=cwd, check=True, text=True, capture_output=True)
    return proc.stdout.strip()


def ensure_mirror(clone_url: str, mirror_dir: Path) -> None:
    mirror_dir.parent.mkdir(parents=True, exist_ok=True)
    if not mirror_dir.exists():
        _run(["git", "clone", "--mirror", clone_url, str(mirror_dir)])
    else:
        _run(["git", "remote", "update", "--prune"], cwd=mirror_dir)
