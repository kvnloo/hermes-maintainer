from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, replace
from pathlib import Path

from hermes_maintainer.github.ids import parse_repo


@dataclass(frozen=True)
class RepoConfig:
    name: str
    clone_url: str
    default_branch: str = "main"


@dataclass(frozen=True)
class PathsConfig:
    data_dir: Path
    mirror_dir: Path
    database: Path


@dataclass(frozen=True)
class ScanConfig:
    fast_interval_seconds: int = 900
    deep_interval_seconds: int = 21600
    issue_pages_per_fast_scan: int = 10
    pr_pages_per_fast_scan: int = 10
    max_deep_prs_per_scan: int = 250
    max_similarity_candidates_per_node: int = 40


@dataclass(frozen=True)
class SimilarityConfig:
    lexical_threshold: float = 0.58
    strong_threshold: float = 0.78
    minimum_shared_tokens: int = 4


@dataclass(frozen=True)
class OptimizerConfig:
    issue_weight: float = 100.0
    security_multiplier: float = 2.0
    p0_multiplier: float = 3.0
    p1_multiplier: float = 2.0
    p2_multiplier: float = 1.25
    pr_supersession_weight: float = 18.0
    conflict_penalty: float = 80.0
    changed_file_penalty: float = 0.35
    changed_line_penalty: float = 0.01
    new_dependency_penalty: float = 25.0


@dataclass(frozen=True)
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8766


@dataclass(frozen=True)
class Settings:
    root: Path
    repo: RepoConfig
    paths: PathsConfig
    scan: ScanConfig
    similarity: SimilarityConfig
    optimizer: OptimizerConfig
    server: ServerConfig
    github_token: str | None


def _resolve(root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (root / path).resolve()


def with_repo(settings: Settings, repo: str) -> Settings:
    """Retarget scan/toolkit paths at any GitHub owner/name. Does not assume hermes-agent."""
    name = parse_repo(repo)
    owner, repo_name = name.split("/", 1)
    return replace(
        settings,
        repo=RepoConfig(
            name=name,
            clone_url=f"https://github.com/{name}.git",
            default_branch=settings.repo.default_branch,
        ),
        paths=replace(
            settings.paths,
            mirror_dir=settings.paths.data_dir / "repos" / f"{owner}--{repo_name}.git",
        ),
    )


def load_settings(config_path: str | Path | None = None, *, repo: str | None = None) -> Settings:
    config_path = Path(
        config_path or os.environ.get("HERMES_MAINTAINER_CONFIG", "config/hermes-maintainer.toml")
    ).resolve()
    root = config_path.parent.parent if config_path.parent.name == "config" else Path.cwd().resolve()
    with config_path.open("rb") as fh:
        raw = tomllib.load(fh)

    repo_cfg = RepoConfig(**raw["repo"])
    p = raw["paths"]
    paths = PathsConfig(
        data_dir=_resolve(root, p["data_dir"]),
        mirror_dir=_resolve(root, p["mirror_dir"]),
        database=_resolve(root, p["database"]),
    )
    settings = Settings(
        root=root,
        repo=repo_cfg,
        paths=paths,
        scan=ScanConfig(**raw.get("scan", {})),
        similarity=SimilarityConfig(**raw.get("similarity", {})),
        optimizer=OptimizerConfig(**raw.get("optimizer", {})),
        server=ServerConfig(**raw.get("server", {})),
        github_token=os.environ.get("GITHUB_TOKEN") or None,
    )
    if repo:
        return with_repo(settings, repo)
    return settings
