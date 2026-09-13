from __future__ import annotations

from pathlib import Path

_PROMPT_DIR = Path(__file__).with_name("prompts")


def prompt(name: str) -> str:
    path = _PROMPT_DIR / f"{name}.md"
    if not path.exists():
        raise KeyError(name)
    return path.read_text(encoding="utf-8")


def available() -> list[str]:
    return sorted(p.stem for p in _PROMPT_DIR.glob("*.md"))
