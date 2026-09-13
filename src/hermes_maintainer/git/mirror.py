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


def current_sha(mirror_dir: Path, ref: str = "refs/remotes/origin/main") -> str:
    try:
        return _run(["git", "rev-parse", ref], cwd=mirror_dir)
    except subprocess.CalledProcessError:
        return _run(["git", "rev-parse", "main"], cwd=mirror_dir)


def merge_base(mirror_dir: Path, a: str, b: str) -> str:
    return _run(["git", "merge-base", a, b], cwd=mirror_dir)


def is_ancestor(mirror_dir: Path, ancestor: str, descendant: str) -> bool:
    proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=mirror_dir,
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode == 0
