"""Tests for dotlink.snapshot."""

import time
from pathlib import Path

import pytest

from dotlink.snapshot import (
    SnapshotError,
    Snapshot,
    take_snapshot,
    list_snapshots,
    restore_snapshot,
    _snapshots_dir,
)


@pytest.fixture
def config(tmp_path):
    return {
        "repo_path": str(tmp_path / "repo"),
        "links": {
            str(tmp_path / "home" / ".vimrc"): str(tmp_path / "repo" / "vimrc"),
            str(tmp_path / "home" / ".bashrc"): str(tmp_path / "repo" / "bashrc"),
        },
    }


def test_snapshots_dir_uses_repo_path(config, tmp_path):
    d = _snapshots_dir(config)
    assert d == Path(config["repo_path"]) / ".snapshots"


def test_take_snapshot_creates_file(config, tmp_path):
    snap = take_snapshot(config)
    snapshots_dir = _snapshots_dir(config)
    files = list(snapshots_dir.glob("*.json"))
    assert len(files) == 1


def test_take_snapshot_returns_snapshot_with_links(config):
    snap = take_snapshot(config)
    assert snap.links == config["links"]


def test_take_snapshot_stores_label(config):
    snap = take_snapshot(config, label="before-upgrade")
    assert "before-upgrade" in snap.labels


def test_take_snapshot_no_label_has_empty_labels(config):
    snap = take_snapshot(config)
    assert snap.labels == []


def test_list_snapshots_empty_when_no_dir(config):
    snaps = list_snapshots(config)
    assert snaps == []


def test_list_snapshots_returns_all(config):
    take_snapshot(config, label="first")
    time.sleep(0.01)
    take_snapshot(config, label="second")
    snaps = list_snapshots(config)
    assert len(snaps) == 2


def test_list_snapshots_sorted_oldest_first(config):
    take_snapshot(config, label="first")
    time.sleep(0.01)
    take_snapshot(config, label="second")
    snaps = list_snapshots(config)
    assert snaps[0].created_at < snaps[1].created_at


def test_restore_snapshot_returns_link_map(config):
    snap = take_snapshot(config)
    result = restore_snapshot(config, snap)
    assert result == config["links"]


def test_restore_snapshot_raises_on_invalid_data(config):
    bad_snap = Snapshot(created_at=time.time(), links="not-a-dict")
    with pytest.raises(SnapshotError):
        restore_snapshot(config, bad_snap)


def test_take_snapshot_creates_parent_dirs(tmp_path):
    cfg = {"repo_path": str(tmp_path / "deep" / "repo"), "links": {}}
    snap = take_snapshot(cfg)
    assert _snapshots_dir(cfg).exists()
