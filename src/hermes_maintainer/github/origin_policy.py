from __future__ import annotations

import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from hermes_maintainer.github.ids import parse_repo

EXIT_ORIGIN_WRITES_REFUSED = 2

_HONEYPOT_RE = re.compile(r"ZAPI_VALIDATE", re.IGNORECASE)

_BAN_PATTERNS = (
    re.compile(r"ai.{0,80}must not\s+(submit|interact)", re.IGNORECASE | re.DOTALL),
    re.compile(
        r"not allowed to interact.{0,240}(github|pull request|issues?|prs?)",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(r"must not.{0,80}interact with pull requests", re.IGNORECASE | re.DOTALL),
    re.compile(r"using ai to directly interact with github", re.IGNORECASE),
    re.compile(r"ai-generated (pr|pull request|ticket|issue)", re.IGNORECASE),
)

_ALLOW_PATTERNS = (
    re.compile(r"ai agents may open (pull requests|issues)", re.IGNORECASE),
    re.compile(
        r"ai (?:agents?|models?) may (?:open|create|submit) (?:pull requests|issues|prs)",
        re.IGNORECASE,
    ),
    re.compile(r"origin writes? (?:are )?allowed", re.IGNORECASE),
)

POLICY_CANDIDATES = (
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    ".github/policies/AI_USAGE.md",
    "AI_USAGE.md",
    "docs/AI.md",
)

ORG_POLICY_CANDIDATES = (
    "policies/AI_USAGE.md",
    "AI_USAGE.md",
    "AGENTS.md",
)


@dataclass(frozen=True)
class OriginWriteAttestation:
    repo: str
    verdict: str
    reason: str
    origin_write_attempted: bool
    writes_permitted: bool
    sources: tuple[str, ...] = ()
    honeypot_ignored: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo": self.repo,
            "verdict": self.verdict,
            "reason": self.reason,
            "origin_write_attempted": self.origin_write_attempted,
            "writes_permitted": self.writes_permitted,
            "sources": list(self.sources),
            "honeypot_ignored": list(self.honeypot_ignored),
        }


class OriginWritesRefused(RuntimeError):
    exit_code = EXIT_ORIGIN_WRITES_REFUSED

    def __init__(self, attestation: OriginWriteAttestation):
        self.attestation = replace(
            attestation,
            origin_write_attempted=False,
            writes_permitted=False,
        )
        super().__init__(self.attestation.reason)


def load_policy_documents(policy_dir: Path) -> dict[str, str]:
    docs: dict[str, str] = {}
    root = Path(policy_dir)
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt", ".rst"}:
            continue
        docs[str(path.relative_to(root))] = path.read_text(encoding="utf-8")
    return docs


def _strip_honeypots(text: str) -> tuple[str, tuple[str, ...]]:
    ignored: list[str] = []
    kept: list[str] = []
    chunks = re.split(r"(?:\n\s*\n|\n(?=-\s))", text or "")
    for chunk in chunks:
        if _HONEYPOT_RE.search(chunk):
            ignored.append("ZAPI_VALIDATE")
            continue
        kept.append(chunk)
    return "\n\n".join(kept), tuple(dict.fromkeys(ignored))


def _matches_any(patterns: tuple[re.Pattern[str], ...], text: str) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def classify_origin_writes(repo: str, documents: dict[str, str]) -> OriginWriteAttestation:
    repo = parse_repo(repo)
    ignored: list[str] = []
    cleaned_parts: list[str] = []
    for text in documents.values():
        cleaned, honeypots = _strip_honeypots(text)
        ignored.extend(honeypots)
        cleaned_parts.append(cleaned)
    blob = "\n\n".join(cleaned_parts)
    if _matches_any(_BAN_PATTERNS, blob):
        verdict, reason = "forbidden", "origin_writes_forbidden"
    elif _matches_any(_ALLOW_PATTERNS, blob):
        verdict, reason = "allowed", "origin_writes_allowed"
    else:
        verdict, reason = "unknown", "origin_writes_unknown"
    permitted = verdict == "allowed"
    return OriginWriteAttestation(
        repo=repo,
        verdict=verdict,
        reason=reason,
        origin_write_attempted=False,
        writes_permitted=permitted,
        sources=tuple(documents.keys()),
        honeypot_ignored=tuple(dict.fromkeys(ignored)),
    )


def require_origin_writes(attestation: OriginWriteAttestation) -> OriginWriteAttestation:
    """Fail closed unless origin writes are explicitly allowed. Never marks an attempt."""
    if attestation.verdict != "allowed" or not attestation.writes_permitted:
        raise OriginWritesRefused(attestation)
    return attestation


def fetch_origin_policy_documents(client: Any, repo: str) -> dict[str, str]:
    """GET-only policy ingest. Never writes."""
    repo = parse_repo(repo)
    docs: dict[str, str] = {}
    for path in POLICY_CANDIDATES:
        text = client.get_text_file(repo, path)
        if text:
            docs[path] = text
    owner = repo.split("/", 1)[0]
    if not repo.endswith("/.github"):
        for path in ORG_POLICY_CANDIDATES:
            text = client.get_text_file(f"{owner}/.github", path)
            if text:
                docs[f"{owner}/.github:{path}"] = text
    return docs
