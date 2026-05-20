"""Sync dotfiles repository — pull latest changes and reapply links."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Tuple

from dotlink.config import load_config
from dotlink.links import LinkError, create_link, link_status


class SyncError(Exception):
    """Raised when a sync operation fails."""


def git_pull(repo_path: Path) -> str:
    """Run `git pull` inside *repo_path* and return stdout.

    Raises SyncError on non-zero exit code.
    """
    result = subprocess.run(
        ["git", "pull"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SyncError(
            f"git pull failed in {repo_path}:\n{result.stderr.strip()}"
        )
    return result.stdout.strip()


def reapply_links(
    config: dict,
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """Reapply all links defined in *config*.

    Returns:
        ok      – list of target paths that were successfully linked.
        errors  – list of (target, error_message) tuples.
    """
    ok: List[str] = []
    errors: List[Tuple[str, str]] = []

    for entry in config.get("links", []):
        source = entry.get("source", "")
        target = entry.get("target", "")
        if not source or not target:
            errors.append((target or source, "missing source or target"))
            continue

        status = link_status(source, target)
        if status == "ok":
            ok.append(target)
            continue

        try:
            create_link(source, target, overwrite=True)
            ok.append(target)
        except LinkError as exc:
            errors.append((target, str(exc)))

    return ok, errors


def sync(config_path: Path | None = None) -> dict:
    """Pull the git repo and reapply all tracked symlinks.

    Returns a result dict with keys: ``pull_output``, ``ok``, ``errors``.
    """
    config = load_config(config_path)
    repo_path = Path(config["repo_path"]).expanduser()

    pull_output = git_pull(repo_path)
    ok, errors = reapply_links(config)

    return {"pull_output": pull_output, "ok": ok, "errors": errors}
