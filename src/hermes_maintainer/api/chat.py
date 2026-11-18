"""Local-only web routes for Hermes ACP chat and public, deterministic guide search."""
from __future__ import annotations

import ipaddress
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from hermes_maintainer.acp_bridge import ACPChats, ACPUnavailable, acp_settings


class NewChat(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)
    mode: str = Field(default="learn", pattern="^(learn|triage|contribute)$")


class NextPrompt(BaseModel):
    prompt: str = Field(min_length=1, max_length=8000)


class PermissionChoice(BaseModel):
    requestId: int
    optionId: str = Field(pattern="^(allow_once|deny)$")


def search_guides(root: Path, query: str, limit: int = 8) -> list[dict[str, str]]:
    """Search only reviewed public knowledge files; no arbitrary path traversal."""
    words = [w.casefold() for w in query.split() if len(w) > 1][:12]
    if not words:
        return []
    scored = []
    for path in sorted((root / "knowledge").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()
        title = next((line.lstrip("# ").strip() for line in lines if line.startswith("# ")), path.stem)
        lowered = text.casefold()
        score = sum(lowered.count(w) for w in words)
        if score:
            match = next((line.strip() for line in lines if any(w in line.casefold() for w in words)
                          and len(line.strip()) > 20), "")
            scored.append((score, {"title": title, "path": f"/knowledge/{path.name}",
                                   "excerpt": match[:300]}))
    scored.sort(key=lambda row: (-row[0], row[1]["path"]))
    return [item for _, item in scored[:limit]]


def require_local_ui(request: Request) -> None:
    """No cross-origin browser posts or network clients may drive a privileged ACP process."""
    address = request.client.host if request.client else ""
    try:
        local = ipaddress.ip_address(address).is_loopback
    except ValueError:
        local = address == "testclient"  # Starlette's in-process TestClient
    if not local or request.headers.get("x-hermes-maintainer-ui") != "1":
        raise HTTPException(403, "ACP is only available to the local UI")
    origin = request.headers.get("origin")
    if origin:
        parsed = urlsplit(origin)
        if parsed.scheme != request.url.scheme or parsed.netloc != request.url.netloc:
            raise HTTPException(403, "cross-origin ACP access denied")


def make_chat_router(root: Path) -> APIRouter:
    router = APIRouter()
    opts = acp_settings(root)
    chats = ACPChats(*opts, root=root) if opts else None

    def lookup(chat_id: str):
        if chats is None:
            raise HTTPException(503, "ACP disabled: run with HERMES_MAINTAINER_ACP_ENABLED=1")
        try:
            return chats.get(chat_id)
        except KeyError as exc:
            raise HTTPException(404, "chat not found") from exc

    @router.get("/api/chat/status")
    def status():
        return {"enabled": chats is not None,
                "message": "Local Hermes ACP ready" if chats else
                "Start the local server with HERMES_MAINTAINER_ACP_ENABLED=1 and install Hermes ACP"}

    @router.get("/api/knowledge/search")
    def knowledge(q: str = Query("", max_length=240)):
        return search_guides(root, q)

    @router.post("/api/chat", status_code=201)
    async def create(request: Request, body: NewChat):
        require_local_ui(request)
        if chats is None:
            raise HTTPException(503, "Hermes ACP is not enabled or configured")
        if not body.prompt.strip():
            raise HTTPException(422, "prompt must not be blank")
        try:
            chat = await chats.create(body.prompt.strip(), body.mode)
        except (ACPUnavailable, OSError, ValueError, KeyError) as exc:
            raise HTTPException(503, f"Could not start Hermes ACP: {str(exc)[:300]}") from exc
        return {"id": chat.id}

    @router.post("/api/chat/{chat_id}/prompt", status_code=202)
    async def prompt(request: Request, chat_id: str, body: NextPrompt):
        require_local_ui(request)
        chat = lookup(chat_id)
        if chat.busy:
            raise HTTPException(409, "a turn is still running")
        if not body.prompt.strip():
            raise HTTPException(422, "prompt must not be blank")
        import asyncio
        asyncio.create_task(chat.run_turn(body.prompt.strip()))
        return {"accepted": True}

    @router.get("/api/chat/{chat_id}/events")
    def events(request: Request, chat_id: str, cursor: int = Query(0, ge=0)):
        require_local_ui(request)
        return lookup(chat_id).events_since(cursor)

    @router.post("/api/chat/{chat_id}/permission")
    def permission(request: Request, chat_id: str, body: PermissionChoice):
        require_local_ui(request)
        if not lookup(chat_id).answer_permission(body.requestId, body.optionId):
            raise HTTPException(409, "permission request expired or option not offered")
        return {"accepted": True}

    @router.post("/api/chat/{chat_id}/cancel")
    async def cancel(request: Request, chat_id: str):
        require_local_ui(request)
        await lookup(chat_id).cancel()
        return {"accepted": True}

    @router.delete("/api/chat/{chat_id}")
    async def delete(request: Request, chat_id: str):
        require_local_ui(request)
        lookup(chat_id)
        await chats.remove(chat_id)
        return {"deleted": True}

    @router.on_event("shutdown")
    async def shutdown():
        if chats is not None:
            await chats.close()

    return router
