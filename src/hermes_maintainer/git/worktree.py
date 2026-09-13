from __future__ import annotations

import subprocess
from pathlib import Path


def create_detached_worktree(mirror_dir: Path, destination: Path, ref: str) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(destination)],
            cwd=mirror_dir,
            check=False,
        )
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(destination), ref],
        cwd=mirror_dir,
        check=True,
    )
    return destination
