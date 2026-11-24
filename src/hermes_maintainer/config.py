from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


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


CONFIG_RELPATH = Path("config") / "hermes-maintainer.toml"
_DEFAULT_REPO = {
    "name": "NousResearch/hermes-agent",
    "clone_url": "https://github.com/NousResearch/hermes-agent.git",
}
_DEFAULT_PATHS = {
    "data_dir": ".data",
    "mirror_dir": ".data/repos/hermes-agent.git",
    "database": ".data/hermes-maintainer.db",
}


def _resolve(root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (root / path).resolve()


def _package_repo_root() -> Path | None:
    """Source checkout root when installed editable (src/hermes_maintainer -> repo)."""
    candidate = Path(__file__).resolve().parents[2]
    return candidate if (candidate / CONFIG_RELPATH).is_file() else None


def find_config() -> Path | None:
    """Config lookup: $HERMES_MAINTAINER_CONFIG, ./config/, then the source checkout."""
    explicit = os.environ.get("HERMES_MAINTAINER_CONFIG")
    if explicit:
        return Path(explicit).expanduser().resolve()
    local = Path.cwd() / CONFIG_RELPATH
    if local.is_file():
        return local.resolve()
    repo_root = _package_repo_root()
    return repo_root / CONFIG_RELPATH if repo_root else None


def load_settings(config_path: str | Path | None = None) -> Settings:
    path = Path(config_path).expanduser().resolve() if config_path else find_config()
    if path is None:
        # Installed without a checkout: built-in defaults, data under the current directory.
        root, raw = Path.cwd().resolve(), {}
    else:
        root = path.parent.parent if path.parent.name == "config" else Path.cwd().resolve()
        with path.open("rb") as fh:
            raw = tomllib.load(fh)

    repo = RepoConfig(**raw.get("repo", _DEFAULT_REPO))
    p = {**_DEFAULT_PATHS, **raw.get("paths", {})}
    data_override = os.environ.get("HERMES_MAINTAINER_DATA_DIR")
    if data_override:
        data_dir = _resolve(Path.cwd(), data_override)
        p = {
            "data_dir": str(data_dir),
            "mirror_dir": str(data_dir / "repos" / "hermes-agent.git"),
            "database": str(data_dir / "hermes-maintainer.db"),
        }
    paths = PathsConfig(
        data_dir=_resolve(root, p["data_dir"]),
        mirror_dir=_resolve(root, p["mirror_dir"]),
        database=_resolve(root, p["database"]),
    )
    return Settings(
        root=root,
        repo=repo,
        paths=paths,
        scan=ScanConfig(**raw.get("scan", {})),
        similarity=SimilarityConfig(**raw.get("similarity", {})),
        optimizer=OptimizerConfig(**raw.get("optimizer", {})),
        server=ServerConfig(**raw.get("server", {})),
        github_token=os.environ.get("GITHUB_TOKEN") or None,
    )
