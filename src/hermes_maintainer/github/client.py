from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

import httpx


class RateLimitError(RuntimeError):
    """GitHub primary rate limit exhausted; retrying now cannot succeed."""


MAX_RETRIES = 3
MAX_RETRY_SLEEP = 60.0


def _is_secondary_limit(response: httpx.Response) -> bool:
    if response.status_code == 429:
        return True
    if response.status_code != 403:
        return False
    if "retry-after" in response.headers:
        return True
    return "secondary rate limit" in response.text.lower()


class GitHubClient:
    def __init__(self, token: str | None = None, timeout: float = 30.0):
        self.authenticated = bool(token)
        self.rate_limit: dict[str, int] = {}
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
        for attempt in range(MAX_RETRIES + 1):
            response = self.client.get(path, params=params)
            for key in ("limit", "remaining", "reset"):
                value = response.headers.get(f"x-ratelimit-{key}")
                if value is not None and value.isdigit():
                    self.rate_limit[key] = int(value)
            if (
                response.status_code in (403, 429)
                and response.headers.get("x-ratelimit-remaining") == "0"
            ):
                reset = int(response.headers.get("x-ratelimit-reset", "0"))
                delay = max(0, reset - int(time.time()))
                hint = "" if self.authenticated else (
                    " Unauthenticated requests get 60/hour; export GITHUB_TOKEN for 5000/hour,"
                    " or lower --limit."
                )
                raise RateLimitError(f"GitHub rate limit exhausted; resets in ~{delay}s.{hint}")
            if _is_secondary_limit(response) and attempt < MAX_RETRIES:
                retry_after = response.headers.get("retry-after", "")
                wait = float(retry_after) if retry_after.isdigit() else 2.0 ** (attempt + 1)
                time.sleep(min(wait, MAX_RETRY_SLEEP))
                continue
            response.raise_for_status()
            return response
        raise AssertionError("unreachable")

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

    def iter_issues(
        self, repo: str, *, max_pages: int | None = None, per_page: int = 100
    ) -> Iterator[dict[str, Any]]:
        for page in self.iter_pages(
            f"/repos/{repo}/issues",
            params={"state": "all", "sort": "updated", "direction": "desc", "per_page": per_page},
            max_pages=max_pages,
        ):
            for item in page:
                if "pull_request" not in item:
                    yield item

    def iter_pulls(
        self, repo: str, *, max_pages: int | None = None, per_page: int = 100
    ) -> Iterator[dict[str, Any]]:
        for page in self.iter_pages(
            f"/repos/{repo}/pulls",
            params={"state": "all", "sort": "updated", "direction": "desc", "per_page": per_page},
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
