"""Tiny stdio ACP agent for tests: one session, one streamed reply, one permission round-trip.

Prompt "secret" returns a JSON-RPC error whose text must never reach the browser.
Prompt "spawn" starts a grandchild and writes its pid to $FAKE_ACP_PIDFILE.
"""
import json
import os
import subprocess
import sys


def send(msg):
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def read():
    line = sys.stdin.readline()
    if not line:
        sys.exit(0)
    return json.loads(line)


while True:
    msg = read()
    method, rid = msg.get("method"), msg.get("id")
    if method == "initialize":
        send({"jsonrpc": "2.0", "id": rid, "result": {"protocolVersion": 1, "agentCapabilities": {}}})
    elif method == "session/new":
        send({"jsonrpc": "2.0", "id": rid,
              "result": {"sessionId": "s1", "modes": {"currentModeId": "default"}}})
    elif method == "session/prompt":
        text = msg["params"]["prompt"][0]["text"]
        if "secret" in text.split("User request:")[-1]:
            send({"jsonrpc": "2.0", "id": rid,
                  "error": {"code": -32000, "message": "boom /home/someone/.token=SENTINEL-123"}})
            continue
        if "spawn" in text.split("User request:")[-1]:
            child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
            with open(os.environ["FAKE_ACP_PIDFILE"], "w") as fh:
                fh.write(str(child.pid))
        send({"jsonrpc": "2.0", "method": "session/update", "params": {"sessionId": "s1", "update": {
            "sessionUpdate": "agent_message_chunk", "content": {"type": "text", "text": "hello"}}}})
        send({"jsonrpc": "2.0", "id": 900, "method": "session/request_permission", "params": {
            "sessionId": "s1", "toolCall": {"toolCallId": "t1", "title": "edit README"},
            "options": [{"optionId": "allow_once", "name": "Allow", "kind": "allow_once"},
                        {"optionId": "allow_always", "name": "Always", "kind": "allow_always"},
                        {"optionId": "deny", "name": "Deny", "kind": "reject_once"}]}})
        reply = read()
        outcome = reply["result"]["outcome"]
        decision = outcome.get("optionId", outcome["outcome"])
        send({"jsonrpc": "2.0", "method": "session/update", "params": {"sessionId": "s1", "update": {
            "sessionUpdate": "agent_message_chunk", "content": {"type": "text", "text": f"perm={decision}"}}}})
        send({"jsonrpc": "2.0", "id": rid, "result": {"stopReason": "end_turn"}})
    elif rid is not None:
        send({"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": "nope"}})
