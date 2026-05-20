"""Configuration management for dotlink.

Handles loading and saving the dotlink configuration file (dotlink.json),
which tracks managed symlinks and repository settings.
"""

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_FILENAME = "dotlink.json"

DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    "links": {},  # Maps target path -> source path (relative to repo root)
    "repo_root": None,
}


def find_config_path(start_dir: Path | None = None) -> Path | None:
    """Walk up from start_dir to find a dotlink.json file."""
    current = (start_dir or Path.cwd()).resolve()
    for directory in [current, *current.parents]:
        candidate = directory / DEFAULT_CONFIG_FILENAME
        if candidate.exists():
            return candidate
    return None


def load_config(config_path: Path) -> dict[str, Any]:
    """Load and parse a dotlink config file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    # Merge with defaults to ensure all keys exist
    merged = {**DEFAULT_CONFIG, **data}
    return merged


def save_config(config: dict[str, Any], config_path: Path) -> None:
    """Write config dictionary to a dotlink.json file."""
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")


def init_config(repo_root: Path) -> dict[str, Any]:
    """Create and save a fresh config at the given repo root."""
    config_path = repo_root / DEFAULT_CONFIG_FILENAME
    if config_path.exists():
        raise FileExistsError(f"Config already exists at {config_path}")
    config = {**DEFAULT_CONFIG, "repo_root": str(repo_root)}
    save_config(config, config_path)
    return config
