from __future__ import annotations

import subprocess
from pathlib import Path


def stable_patch_id(mirror_dir: Path, commit_sha: str) -> str | None:
    show = subprocess.Popen(
        ["git", "show", "--pretty=format:", "--no-ext-diff", commit_sha],
        cwd=mirror_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    patch = subprocess.run(
        ["git", "patch-id", "--stable"],
        cwd=mirror_dir,
        stdin=show.stdout,
        text=True,
        capture_output=True,
    )
    if show.stdout:
        show.stdout.close()
    show.wait()
    if show.returncode != 0 or patch.returncode != 0 or not patch.stdout.strip():
        return None
    return patch.stdout.split()[0]
