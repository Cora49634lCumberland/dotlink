"""Sync dotfiles repo and reapply links."""

import subprocess
from pathlib import Path
from typing import List

from dotlink.links import LinkStatus, create_link, link_status


class SyncError(Exception):
    """Raised when a sync operation fails."""


def git_pull(repo_path: Path) -> str:
    """Run `git pull` in *repo_path* and return stdout."""
    result = subprocess.run(
        ["git", "pull"],
        cwd=repo_path,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise SyncError(
            f"git pull failed (exit {result.returncode}):\n{result.stderr.strip()}"
        )
    return result.stdout


def reapply_links(config: dict) -> List[str]:
    """Ensure every tracked link exists; return list of recreated link names."""
    recreated: List[str] = []
    for name, entry in config.get("links", {}).items():
        source = Path(entry["source"]).expanduser()
        target = Path(entry["target"]).expanduser()
        status = link_status(source, target)
        if status != LinkStatus.OK:
            create_link(source, target)
            recreated.append(name)
    return recreated


def sync(config: dict, run_hooks: bool = True) -> dict:
    """Pull latest changes and reapply links, running hooks when available."""
    from dotlink.hooks import HookError, run_hook  # local import to avoid cycles

    repo = Path(config.get("repo_path", "~/.dotfiles")).expanduser()

    if run_hooks:
        try:
            run_hook(config, "pre-sync")
        except HookError as exc:
            raise SyncError(f"pre-sync hook failed: {exc}") from exc

    pull_output = git_pull(repo)
    recreated = reapply_links(config)

    if run_hooks:
        try:
            run_hook(config, "post-sync")
        except HookError as exc:
            raise SyncError(f"post-sync hook failed: {exc}") from exc

    return {"pull_output": pull_output, "recreated": recreated}
