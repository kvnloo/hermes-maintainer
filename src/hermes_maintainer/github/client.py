from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

import httpx


class GitHubClient:
    def __init__(self, token: str | None = None, timeout: float = 30.0):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "hermes-maintainer/0.1",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.client = httpx.Client(base_url="https://api.github.com", headers=headers, timeout=timeout)

    def close(self) -> None:
        self.client.close()

    def _get(self, path: str, params: dict[str, Any] | None = None) -> httpx.Response:
        response = self.client.get(path, params=params)
        if response.status_code == 403 and response.headers.get("x-ratelimit-remaining") == "0":
            reset = int(response.headers.get("x-ratelimit-reset", "0"))
            delay = max(0, reset - int(time.time()))
            raise RuntimeError(f"GitHub rate limit exhausted; resets in ~{delay}s")
        response.raise_for_status()
        return response

    def iter_pages(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        max_pages: int | None = None,
    ) -> Iterator[list[dict[str, Any]]]:
        page = 1
        base = dict(params or {})
        base.setdefault("per_page", 100)
        while True:
            if max_pages is not None and page > max_pages:
                return
            payload = self._get(path, {**base, "page": page}).json()
            if not isinstance(payload, list) or not payload:
                return
            yield payload
            if len(payload) < int(base["per_page"]):
                return
            page += 1

    def iter_issues(self, repo: str, *, max_pages: int | None = None) -> Iterator[dict[str, Any]]:
        for page in self.iter_pages(
            f"/repos/{repo}/issues",
            params={"state": "all", "sort": "updated", "direction": "desc"},
            max_pages=max_pages,
        ):
            for item in page:
                if "pull_request" not in item:
                    yield item

    def iter_pulls(self, repo: str, *, max_pages: int | None = None) -> Iterator[dict[str, Any]]:
        for page in self.iter_pages(
            f"/repos/{repo}/pulls",
            params={"state": "all", "sort": "updated", "direction": "desc"},
            max_pages=max_pages,
        ):
            yield from page

    def get_pull(self, repo: str, number: int) -> dict[str, Any]:
        return self._get(f"/repos/{repo}/pulls/{number}").json()

    def get_issue(self, repo: str, number: int) -> dict[str, Any]:
        return self._get(f"/repos/{repo}/issues/{number}").json()

    def get_pull_files(self, repo: str, number: int) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for page in self.iter_pages(f"/repos/{repo}/pulls/{number}/files"):
            out.extend(page)
        return out

    def get_pull_commits(self, repo: str, number: int) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for page in self.iter_pages(f"/repos/{repo}/pulls/{number}/commits"):
            out.extend(page)
        return out
