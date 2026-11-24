"""Opt-in real e2e: uvicorn on loopback -> real `hermes acp` -> one Learn turn, all permissions denied.

Run: HM_REAL_ACP="hermes -p <profile> acp" pytest -s tests/test_acp_real.py
Costs one real model turn on that profile. Prints a JSON receipt.
"""
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CMD = os.environ.get("HM_REAL_ACP", "")
pytestmark = pytest.mark.skipif(not CMD, reason="set HM_REAL_ACP to run against a real Hermes")
H = {"x-hermes-maintainer-ui": "1", "content-type": "application/json"}


def test_real_hermes_learn_turn():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    # Hermes' live-system guard refuses the real state.db under a pytest ancestor;
    # this opt-in test targets the real profile on purpose (documented child bypass).
    env = dict(os.environ, HERMES_STATE_DB_GUARD_BYPASS="1")
    env.update(HERMES_MAINTAINER_ACP_ENABLED="1", HERMES_MAINTAINER_ACP_COMMAND=CMD,
               HERMES_MAINTAINER_ACP_WORKSPACE=str(ROOT))
    srv = subprocess.Popen([sys.executable, "-m", "uvicorn", "hermes_maintainer.api.app:create_app",
                            "--factory", "--host", "127.0.0.1", "--port", str(port)], cwd=ROOT, env=env,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    base = f"http://127.0.0.1:{port}"

    def call(method, path, body=None):
        req = urllib.request.Request(base + path, method=method, headers=H,
                                     data=json.dumps(body).encode() if body is not None else None)
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read() or b"null")
        except urllib.error.HTTPError as exc:
            raise AssertionError(f"{method} {path} -> {exc.code} {exc.read()[:300]!r}") from exc

    receipt = {}
    try:
        for _ in range(150):
            try:
                assert call("GET", "/api/chat/status")["enabled"]; break
            except OSError:
                time.sleep(0.2)
        t0 = time.time()
        cid = call("POST", "/api/chat", {"mode": "learn", "prompt":
                   "In one sentence: what does knowledge/START_HERE.md tell a newcomer to do first? Do not edit anything."})["id"]
        receipt["create_s"] = round(time.time() - t0, 1)
        events, cursor = [], 0
        while time.time() - t0 < 600 and not any(e["type"] in ("turn_end", "error", "disconnected") for e in events):
            got = call("GET", f"/api/chat/{cid}/events?cursor={cursor}")
            events += got["events"]; cursor = got["cursor"]
            for e in got["events"]:
                if e["type"] == "permission":
                    call("POST", f"/api/chat/{cid}/permission", {"requestId": e["requestId"], "optionId": "deny"})
            time.sleep(1)
        receipt["turn_s"] = round(time.time() - t0, 1)
        receipt["event_types"] = sorted({e["type"] for e in events})
        receipt["session"] = next((e.get("sessionId") for e in events if e["type"] == "ready"), None)
        receipt["reply"] = "".join(e["payload"].get("content", {}).get("text", "") for e in events
                                   if e["type"] == "update" and e["payload"].get("sessionUpdate") == "agent_message_chunk")
        receipt["end"] = [e for e in events if e["type"] in ("turn_end", "error", "disconnected")][-1:]
        call("DELETE", f"/api/chat/{cid}")
    finally:
        os.killpg(srv.pid, 15)
        print(json.dumps(receipt, indent=1))
    assert receipt["end"] and receipt["end"][0]["type"] == "turn_end"
    assert receipt["reply"].strip()
