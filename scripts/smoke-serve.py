#!/usr/bin/env python3
"""Start `hermes-maintainer serve` on a free loopback port, assert key routes, stop it.

usage: scripts/smoke-serve.py [path/to/hermes-maintainer]   (default: .venv/bin/hermes-maintainer)
Exit 0 only if /, /api/graph (with nodes), /llms.txt and /static/graph-app.js return 200.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def get(url: str) -> tuple[int, bytes]:
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, b""


def main() -> int:
    exe = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / ".venv" / "bin" / "hermes-maintainer")
    port = free_port()
    base = f"http://127.0.0.1:{port}"
    proc = subprocess.Popen(
        [exe, "serve", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT, env=os.environ.copy(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    failures: list[str] = []
    try:
        deadline = time.time() + 20
        while time.time() < deadline and proc.poll() is None:
            try:
                urllib.request.urlopen(base + "/api/health", timeout=1)
                break
            except OSError:
                time.sleep(0.2)
        if proc.poll() is not None:
            print(proc.stdout.read() if proc.stdout else "", file=sys.stderr)
            print(f"FAIL: server exited with {proc.returncode}", file=sys.stderr)
            return 1
        for path in ("/", "/api/graph", "/llms.txt", "/static/graph-app.js"):
            status, body = get(base + path)
            detail = f"{len(body)} bytes"
            if path == "/api/graph" and status == 200:
                nodes = len(json.loads(body).get("nodes") or [])
                detail += f", {nodes} nodes"
                if nodes == 0:
                    failures.append("/api/graph returned no nodes (run `hermes-maintainer init --demo`)")
            print(f"{status} {path} ({detail})")
            if status != 200:
                failures.append(f"{path} -> {status}")
    finally:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()
    for f in failures:
        print("FAIL:", f, file=sys.stderr)
    print("smoke-serve:", "OK" if not failures else "FAILED", f"(port {port})")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
