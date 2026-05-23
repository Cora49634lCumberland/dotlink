"""Alias support: short names that map to link targets."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

from dotlink.config import load_config


class AliasError(Exception):
    """Raised when an alias operation fails."""


def _aliases_path(config: dict) -> Path:
    return Path(config["repo_path"]) / ".dotlink_aliases.json"


def load_aliases(config: dict) -> Dict[str, str]:
    """Return mapping of alias -> target path string."""
    path = _aliases_path(config)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise AliasError(f"Corrupt aliases file: {exc}") from exc


def save_aliases(config: dict, aliases: Dict[str, str]) -> None:
    path = _aliases_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(aliases, indent=2))


def add_alias(config: dict, name: str, target: str) -> None:
    """Register *name* as an alias for *target*."""
    aliases = load_aliases(config)
    if name in aliases:
        raise AliasError(f"Alias '{name}' already exists (points to '{aliases[name]}')")
    aliases[name] = target
    save_aliases(config, aliases)


def remove_alias(config: dict, name: str) -> None:
    """Remove alias *name*."""
    aliases = load_aliases(config)
    if name not in aliases:
        raise AliasError(f"Alias '{name}' not found")
    del aliases[name]
    save_aliases(config, aliases)


def resolve_alias(config: dict, name: str) -> str:
    """Return the target path for *name*, or raise AliasError."""
    aliases = load_aliases(config)
    if name not in aliases:
        raise AliasError(f"Unknown alias '{name}'")
    return aliases[name]
