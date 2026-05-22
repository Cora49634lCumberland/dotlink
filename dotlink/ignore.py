"""Manage ignore patterns for dotlink — files/paths to exclude from linking."""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotlink.config import load_config


class IgnoreError(Exception):
    """Raised when an ignore operation fails."""


DEFAULT_PATTERNS: List[str] = [
    ".git",
    ".gitignore",
    "*.swp",
    "*.bak",
    ".DS_Store",
    "dotlink.toml",
]


def _ignore_path(config: dict) -> Path:
    """Return the path to the .dotignore file inside the repo."""
    return Path(config["repo_path"]) / ".dotignore"


def load_patterns(config: dict) -> List[str]:
    """Load ignore patterns from .dotignore; returns defaults if file absent."""
    path = _ignore_path(config)
    if not path.exists():
        return list(DEFAULT_PATTERNS)
    lines = path.read_text().splitlines()
    patterns = [ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")]
    return patterns


def save_patterns(config: dict, patterns: List[str]) -> None:
    """Persist ignore patterns to .dotignore."""
    path = _ignore_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "# dotlink ignore patterns\n" + "\n".join(patterns) + "\n"
    path.write_text(content)


def add_pattern(config: dict, pattern: str) -> List[str]:
    """Add a pattern; raises IgnoreError if it already exists."""
    patterns = load_patterns(config)
    if pattern in patterns:
        raise IgnoreError(f"Pattern already exists: {pattern}")
    patterns.append(pattern)
    save_patterns(config, patterns)
    return patterns


def remove_pattern(config: dict, pattern: str) -> List[str]:
    """Remove a pattern; raises IgnoreError if not found."""
    patterns = load_patterns(config)
    if pattern not in patterns:
        raise IgnoreError(f"Pattern not found: {pattern}")
    patterns.remove(pattern)
    save_patterns(config, patterns)
    return patterns


def is_ignored(name: str, patterns: List[str]) -> bool:
    """Return True if *name* matches any of the given glob patterns."""
    return any(fnmatch.fnmatch(name, p) for p in patterns)
