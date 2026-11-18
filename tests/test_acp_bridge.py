"""Hermes ACP wire tests: a fake agent process, not a mocked HTTP response.

They prove stdio initialization, session/new, streaming, one-time permissions,
and transport errors without needing real provider credentials.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from hermes_maintainer.acp_bridge import ACPConversation, acp_settings, orient_prompt
from hermes_maintainer.api.app import create_app

FAKE_ACP = r'''
import json
import sys


def emit(packet):
    sys.stdout.write(json.dumps(packet) + "\n")
    sys.stdout.flush()


for line in sys.stdin:
    msg = json.loads(line)
    method = msg.get("method")
    if method == "initialize":
        emit({"jsonrpc": "2.0", "id": msg["id"], "result": {
            "protocolVersion": 1, "agentCapabilities": {}
        }})
    elif method == "session/new":
        emit({"jsonrpc": "2.0", "id": msg["id"], "result": {
            "sessionId": "s1", "modes": {"currentModeId": "default"}
        }})
    elif method == "session/prompt":
        content = msg["params"]["prompt"][0]["text"]
        if "permission please" in content:
            emit({"jsonrpc": "2.0", "id": 900, "method": "session/request_permission",
                  "params": {"sessionId": "s1", "toolCall": {"toolCallId": "t1",
                            "title": "Run a command"}, "options": [
                      {"optionId": "allow_once", "kind": "allow_once", "name": "Allow once"},
                      {"optionId": "deny", "kind": "reject_once", "name": "Deny"},
                  ]}})
            answer = json.loads(sys.stdin.readline())
            assert answer["id"] == 900
            assert answer["result"]["outcome"] == {
                "outcome": "selected", "optionId": "allow_once"
            }
        emit({"jsonrpc": "2.0", "method": "session/update", "params": {
            "sessionId": "s1", "update": {
                "sessionUpdate": "agent_message_chunk", "content": {
                    "type": "text", "text": "Hello from Hermes"
                }
            }
        }})
        emit({"jsonrpc": "2.0", "id": msg["id"], "result": {"stopReason": "end_turn"}})
'''


def fake_command(tmp_path: Path) -> list[str]:
    fake = tmp_path / "fake_acp.py"
    fake.write_text(FAKE_ACP, encoding="utf-8")
    return [sys.executable, "-u", str(fake)]


def test_prompt_bootstrap_does_not_grant_upstream_writes(tmp_path: Path):
    prompt = orient_prompt(tmp_path, "contribute", "Find the fix")
    assert "Find the fix" in prompt
    assert "Never write to NousResearch/hermes-agent" in prompt
    assert str(tmp_path / "knowledge" / "START_HERE.md") in prompt
    with pytest.raises(ValueError):
        orient_prompt(tmp_path, "admin", "irrelevant")


def test_acp_opt_in_is_required(monkeypatch, tmp_path: Path):
    monkeypatch.delenv("HERMES_MAINTAINER_ACP_ENABLED", raising=False)
    assert acp_settings(tmp_path) is None
    monkeypatch.setenv("HERMES_MAINTAINER_ACP_ENABLED", "1")
    monkeypatch.setenv("HERMES_MAINTAINER_ACP_COMMAND", "nonexistent-hermes-binary-xyz")
    assert acp_settings(tmp_path) is None


def test_stdio_stream_and_explicit_permission(tmp_path: Path):
    async def run():
        chat = ACPConversation(fake_command(tmp_path), tmp_path)
        try:
            await chat.start()
            assert chat.session_id == "s1"
            task = asyncio.create_task(chat.run_turn("permission please"))
            for _ in range(100):
                if any(e["type"] == "permission" for e in chat.events):
                    break
                await asyncio.sleep(0.01)
            requests = [e for e in chat.events if e["type"] == "permission"]
            assert len(requests) == 1
            assert not chat.answer_permission(900, "allow_always")
            assert chat.answer_permission(900, "allow_once")
            assert not chat.answer_permission(900, "allow_once")
            await asyncio.wait_for(task, 5)
            assert any(e["type"] == "update" and
                       e["payload"]["content"]["text"] == "Hello from Hermes"
                       for e in chat.events)
            assert any(e["type"] == "turn_end" and e["stopReason"] == "end_turn"
                       for e in chat.events)
            assert chat.events_since(0)["cursor"] >= 4
            assert chat.events_since(chat.cursor)["events"] == []
        finally:
            await chat.close()
    asyncio.run(run())


def test_local_http_acl_and_dialogue(tmp_path: Path, monkeypatch, db):
    command = fake_command(tmp_path)
    monkeypatch.setenv("HERMES_MAINTAINER_ACP_ENABLED", "1")
    monkeypatch.setenv("HERMES_MAINTAINER_ACP_COMMAND", " ".join(command))
    monkeypatch.setenv("HERMES_MAINTAINER_ACP_WORKSPACE", str(tmp_path))
    headers = {"X-Hermes-Maintainer-UI": "1"}
    with TestClient(create_app(database=db)) as client:
        assert client.get("/api/chat/status").json()["enabled"] is True
        assert client.post("/api/chat", json={"prompt": "explain Hermes"}).status_code == 403
        assert client.post(
            "/api/chat", json={"prompt": "hello"}, headers={
                **headers, "Origin": "https://malicious.example"
            }
        ).status_code == 403
        res = client.post("/api/chat", json={"prompt": "What is ACP?", "mode": "learn"},
                          headers=headers)
        assert res.status_code == 201, res.text
        chat_id = res.json()["id"]
        assert len(chat_id) == 32
        for _ in range(100):
            events = client.get(f"/api/chat/{chat_id}/events", headers=headers).json()["events"]
            if any(e["type"] == "turn_end" for e in events):
                break
            import time
            time.sleep(0.01)
        assert any(e["type"] == "update" for e in events)
        assert any(e["type"] == "turn_end" for e in events)
        assert client.delete(f"/api/chat/{chat_id}", headers=headers).status_code == 200
        assert client.get(f"/api/chat/{chat_id}/events", headers=headers).status_code == 404
