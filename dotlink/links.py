"""Manages symlink creation, removal, and status tracking for dotfiles."""

import os
from pathlib import Path
from typing import Optional


class LinkError(Exception):
    """Raised when a symlink operation fails."""
    pass


def resolve_path(path: str) -> Path:
    """Expand user home and environment variables in a path."""
    return Path(os.path.expandvars(os.path.expanduser(path)))


def link_status(source: str, target: str) -> str:
    """Return the status of a symlink pair.

    Returns one of: 'linked', 'missing_source', 'conflict', 'not_linked'
    """
    src = resolve_path(source)
    tgt = resolve_path(target)

    if not src.exists():
        return "missing_source"

    if tgt.is_symlink():
        if tgt.resolve() == src.resolve():
            return "linked"
        return "conflict"

    if tgt.exists():
        return "conflict"

    return "not_linked"


def create_link(source: str, target: str, overwrite: bool = False) -> None:
    """Create a symlink from target -> source.

    Args:
        source: The dotfile in the repo (link destination).
        target: The location in the home directory (link itself).
        overwrite: If True, remove an existing file/link at target.
    """
    src = resolve_path(source)
    tgt = resolve_path(target)

    if not src.exists():
        raise LinkError(f"Source does not exist: {src}")

    if tgt.is_symlink() or tgt.exists():
        if overwrite:
            tgt.unlink() if tgt.is_symlink() else tgt.unlink()
        else:
            raise LinkError(
                f"Target already exists: {tgt}. Use overwrite=True to replace."
            )

    tgt.parent.mkdir(parents=True, exist_ok=True)
    tgt.symlink_to(src)


def remove_link(target: str) -> None:
    """Remove a symlink at the given target path.

    Args:
        target: Path to the symlink to remove.
    """
    tgt = resolve_path(target)

    if not tgt.is_symlink():
        raise LinkError(f"Target is not a symlink: {tgt}")

    tgt.unlink()


def list_links(links: dict) -> list[dict]:
    """Return status info for all configured links.

    Args:
        links: Dict mapping source paths to target paths.

    Returns:
        List of dicts with keys: source, target, status.
    """
    return [
        {"source": src, "target": tgt, "status": link_status(src, tgt)}
        for src, tgt in links.items()
    ]
