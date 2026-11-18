"""ACP bridge against a real child process (tests/fake_acp_agent.py), plus HTTP guard negatives."""
import asyncio
import os
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from hermes_maintainer.acp_bridge import ACPChats
from hermes_maintainer.api.app import create_app

AGENT = [sys.executable, str(Path(__file__).with_name("fake_acp_agent.py"))]
ROOT = Path(__file__).resolve().parents[1]
UI = {"x-hermes-maintainer-ui": "1"}


async def _until(chat, kind, timeout=10):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        hits = [e for e in chat.events if e["type"] == kind]
        if hits:
            return hits
        await asyncio.sleep(0.02)
    raise AssertionError(f"no {kind} event; got {[e['type'] for e in chat.events]}")


def _texts(chat):
    return [e["payload"]["content"]["text"] for e in chat.events
            if e["type"] == "update" and e["payload"].get("sessionUpdate") == "agent_message_chunk"]


@pytest.mark.parametrize("choice,expected", [("allow_once", "perm=allow_once"), ("deny", "perm=deny")])
def test_turn_streams_and_permission_round_trip(choice, expected):
    async def run():
        chats = ACPChats(AGENT, ROOT, ROOT)
        chat = await chats.create("how does the gateway work?", "learn")
        perm = (await _until(chat, "permission"))[0]
        # Only allow_once/deny are offered to the UI; allow_always is filtered out.
        assert {o["optionId"] for o in perm["options"]} == {"allow_once", "deny"}
        assert not chat.answer_permission(perm["requestId"], "allow_always")
        assert chat.answer_permission(perm["requestId"], choice)
        assert not chat.answer_permission(perm["requestId"], choice)  # exactly one reply
        await _until(chat, "turn_end")
        assert _texts(chat) == ["hello", expected]
        await chats.close()
    asyncio.run(run())


def test_agent_error_text_never_reaches_events():
    async def run():
        chats = ACPChats(AGENT, ROOT, ROOT)
        chat = await chats.create("secret", "learn")
        err = (await _until(chat, "error"))[0]
        assert "SENTINEL" not in err["message"] and "/home/" not in err["message"]
        assert "-32000" in err["message"]
        await chats.close()
    asyncio.run(run())


def test_close_kills_agent_process_group(tmp_path, monkeypatch):
    pidfile = tmp_path / "pid"
    monkeypatch.setenv("FAKE_ACP_PIDFILE", str(pidfile))

    async def run():
        chats = ACPChats(AGENT, ROOT, ROOT)
        chat = await chats.create("spawn", "learn")
        await _until(chat, "permission")
        grandchild = int(pidfile.read_text())
        os.kill(grandchild, 0)  # alive
        await chats.close()
        for _ in range(100):
            try:
                os.kill(grandchild, 0)
            except ProcessLookupError:
                return
            # reap if it became our zombie (it should not: it is the agent's child)
            await asyncio.sleep(0.05)
        raise AssertionError("grandchild survived bridge close")
    asyncio.run(run())


@pytest.fixture
def client(db, monkeypatch):
    monkeypatch.setenv("HERMES_MAINTAINER_ACP_ENABLED", "1")
    monkeypatch.setenv("HERMES_MAINTAINER_ACP_COMMAND", " ".join(AGENT))
    monkeypatch.setenv("HERMES_MAINTAINER_ACP_WORKSPACE", str(ROOT))
    with TestClient(create_app(database=db)) as c:
        yield c


def test_http_guards(client):
    assert client.get("/api/chat/status").json()["enabled"] is True
    body = {"prompt": "hi", "mode": "learn"}
    assert client.post("/api/chat", json=body).status_code == 403  # no UI header
    assert client.post("/api/chat", json=body, headers={**UI, "origin": "https://evil.example"}).status_code == 403
    # DNS rebinding: same-origin to itself, but Host is not loopback.
    rebound = {**UI, "host": "evil.example", "origin": "http://evil.example"}
    assert client.post("/api/chat", json=body, headers=rebound).status_code == 403
    assert client.post("/api/chat", json={"prompt": "hi", "mode": "root"}, headers=UI).status_code == 422


def test_http_chat_end_to_end(client):
    chat_id = client.post("/api/chat", json={"prompt": "hi", "mode": "triage"}, headers=UI).json()["id"]
    events, cursor = [], 0
    for _ in range(200):
        got = client.get(f"/api/chat/{chat_id}/events", params={"cursor": cursor}, headers=UI).json()
        events += got["events"]
        cursor = got["cursor"]
        perm = [e for e in events if e["type"] == "permission"]
        if perm and not any(e["type"] == "permission_resolved" for e in events):
            r = client.post(f"/api/chat/{chat_id}/permission", headers=UI,
                            json={"requestId": perm[0]["requestId"], "optionId": "deny"})
            assert r.status_code == 200
        if any(e["type"] == "turn_end" for e in events):
            break
        time.sleep(0.05)
    assert any(e["type"] == "turn_end" for e in events)
    assert client.delete(f"/api/chat/{chat_id}", headers=UI).json() == {"deleted": True}
