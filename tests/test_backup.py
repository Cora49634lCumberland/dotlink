"""Tests for dotlink.backup."""

from __future__ import annotations

import pytest
from pathlib import Path

from dotlink.backup import (
    BackupError,
    backup_file,
    list_backups,
    restore_backup,
    _backup_dir,
)


@pytest.fixture()
def config(tmp_path: Path) -> dict:
    return {"backup_dir": str(tmp_path / "backups")}


@pytest.fixture()
def real_file(tmp_path: Path) -> Path:
    f = tmp_path / "real" / ".bashrc"
    f.parent.mkdir(parents=True)
    f.write_text("# bashrc\n")
    return f


def test_backup_dir_uses_config(config: dict, tmp_path: Path):
    assert _backup_dir(config) == tmp_path / "backups"


def test_backup_file_creates_copy(config: dict, real_file: Path):
    backup_path = backup_file(real_file, config)
    assert backup_path.exists()
    assert backup_path.read_text() == real_file.read_text()


def test_backup_file_creates_parent_dirs(config: dict, real_file: Path):
    backup_path = backup_file(real_file, config)
    assert backup_path.parent.exists()


def test_backup_file_raises_if_target_missing(config: dict, tmp_path: Path):
    missing = tmp_path / "ghost_file"
    with pytest.raises(BackupError, match="does not exist"):
        backup_file(missing, config)


def test_backup_file_works_for_symlink(config: dict, real_file: Path, tmp_path: Path):
    link = tmp_path / "link_to_bashrc"
    link.symlink_to(real_file)
    backup_path = backup_file(link, config)
    assert backup_path.exists()


def test_list_backups_empty_when_no_backups(config: dict):
    assert list_backups(config) == []


def test_list_backups_returns_sorted_dirs(config: dict, real_file: Path):
    # Create two backups; list_backups should return both sorted
    backup_file(real_file, config)
    backup_file(real_file, config)
    backups = list_backups(config)
    assert len(backups) >= 1
    assert backups == sorted(backups)


def test_restore_backup_places_file_at_destination(config: dict, real_file: Path, tmp_path: Path):
    backup_path = backup_file(real_file, config)
    destination = tmp_path / "restored" / ".bashrc"
    restore_backup(backup_path, destination)
    assert destination.exists()
    assert destination.read_text() == "# bashrc\n"


def test_restore_backup_removes_existing_symlink(config: dict, real_file: Path, tmp_path: Path):
    backup_path = backup_file(real_file, config)
    destination = tmp_path / "dest_link"
    # Place a symlink at destination first
    destination.symlink_to(real_file)
    assert destination.is_symlink()
    restore_backup(backup_path, destination)
    assert destination.exists()
    assert not destination.is_symlink()


def test_restore_backup_raises_if_backup_missing(tmp_path: Path):
    with pytest.raises(BackupError, match="does not exist"):
        restore_backup(tmp_path / "nonexistent", tmp_path / "dest")
