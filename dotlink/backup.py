"""Backup and restore original files before symlinking."""

from __future__ import annotations

import shutil
import time
from pathlib import Path


class BackupError(Exception):
    """Raised when a backup or restore operation fails."""


def _backup_dir(config: dict) -> Path:
    """Return the backup directory, defaulting to ~/.dotlink/backups."""
    base = config.get("backup_dir", "~/.dotlink/backups")
    return Path(base).expanduser()


def backup_file(target: str | Path, config: dict) -> Path:
    """Copy *target* into the backup directory and return the backup path.

    The backup is stored as::

        <backup_dir>/<timestamp>/<original-absolute-path-flattened>

    Raises BackupError if *target* does not exist or cannot be copied.
    """
    target = Path(target).expanduser().resolve()
    if not target.exists() and not target.is_symlink():
        raise BackupError(f"Target does not exist: {target}")

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    # Flatten the absolute path: /home/user/.bashrc -> home_user_.bashrc
    flat_name = str(target).lstrip("/").replace("/", "_")
    backup_path = _backup_dir(config) / timestamp / flat_name

    try:
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() or target.is_file():
            shutil.copy2(target, backup_path)
        else:
            shutil.copytree(target, backup_path)
    except OSError as exc:
        raise BackupError(f"Failed to back up {target}: {exc}") from exc

    return backup_path


def list_backups(config: dict) -> list[Path]:
    """Return a sorted list of backup snapshot directories (oldest first)."""
    bdir = _backup_dir(config)
    if not bdir.exists():
        return []
    return sorted(p for p in bdir.iterdir() if p.is_dir())


def restore_backup(backup_path: str | Path, destination: str | Path) -> None:
    """Restore a single backup file/directory to *destination*.

    If *destination* is an existing symlink it is removed first so the real
    file can be placed back.

    Raises BackupError on failure.
    """
    backup_path = Path(backup_path)
    destination = Path(destination).expanduser()

    if not backup_path.exists():
        raise BackupError(f"Backup path does not exist: {backup_path}")

    try:
        if destination.is_symlink():
            destination.unlink()
        destination.parent.mkdir(parents=True, exist_ok=True)
        if backup_path.is_dir():
            shutil.copytree(backup_path, destination)
        else:
            shutil.copy2(backup_path, destination)
    except OSError as exc:
        raise BackupError(f"Failed to restore {backup_path} -> {destination}: {exc}") from exc
