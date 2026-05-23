"""Remote management: track and switch between multiple git remote URLs."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


class RemoteError(Exception):
    """Raised when a remote operation fails."""


@dataclass
class Remote:
    name: str
    url: str


def _run(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def list_remotes(repo_path: Path) -> List[Remote]:
    """Return all configured git remotes for the repo."""
    result = _run(["git", "remote", "-v"], cwd=repo_path)
    if result.returncode != 0:
        raise RemoteError(f"Failed to list remotes: {result.stderr.strip()}")
    seen: dict[str, str] = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0] not in seen:
            seen[parts[0]] = parts[1]
    return [Remote(name=n, url=u) for n, u in seen.items()]


def add_remote(repo_path: Path, name: str, url: str) -> None:
    """Add a new git remote."""
    result = _run(["git", "remote", "add", name, url], cwd=repo_path)
    if result.returncode != 0:
        raise RemoteError(f"Failed to add remote '{name}': {result.stderr.strip()}")


def remove_remote(repo_path: Path, name: str) -> None:
    """Remove a git remote by name."""
    result = _run(["git", "remote", "remove", name], cwd=repo_path)
    if result.returncode != 0:
        raise RemoteError(f"Failed to remove remote '{name}': {result.stderr.strip()}")


def set_remote_url(repo_path: Path, name: str, url: str) -> None:
    """Update the URL of an existing remote."""
    result = _run(["git", "remote", "set-url", name, url], cwd=repo_path)
    if result.returncode != 0:
        raise RemoteError(f"Failed to set URL for remote '{name}': {result.stderr.strip()}")


def get_remote(repo_path: Path, name: str) -> Optional[Remote]:
    """Return a single remote by name, or None if not found."""
    for remote in list_remotes(repo_path):
        if remote.name == name:
            return remote
    return None
