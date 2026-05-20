"""Tests for dotlink.sync."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from dotlink.sync import SyncError, git_pull, reapply_links, sync


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(tmp_path: Path, links: list | None = None) -> dict:
    return {
        "repo_path": str(tmp_path),
        "links": links or [],
    }


# ---------------------------------------------------------------------------
# git_pull
# ---------------------------------------------------------------------------

def test_git_pull_success(tmp_path: Path):
    with patch("dotlink.sync.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Already up to date."
        mock_run.return_value.stderr = ""
        output = git_pull(tmp_path)
    assert output == "Already up to date."
    mock_run.assert_called_once()


def test_git_pull_failure_raises(tmp_path: Path):
    with patch("dotlink.sync.subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "fatal: not a git repo"
        with pytest.raises(SyncError, match="git pull failed"):
            git_pull(tmp_path)


# ---------------------------------------------------------------------------
# reapply_links
# ---------------------------------------------------------------------------

def test_reapply_links_creates_missing(tmp_path: Path):
    source = tmp_path / "dotfiles" / ".bashrc"
    source.parent.mkdir()
    source.write_text("# bashrc")
    target = tmp_path / "home" / ".bashrc"

    config = _make_config(tmp_path, links=[{"source": str(source), "target": str(target)}])
    ok, errors = reapply_links(config)

    assert str(target) in ok
    assert errors == []
    assert target.is_symlink()


def test_reapply_links_skips_already_ok(tmp_path: Path):
    source = tmp_path / ".vimrc"
    source.write_text("set number")
    target = tmp_path / "link_vimrc"
    target.symlink_to(source)

    config = _make_config(tmp_path, links=[{"source": str(source), "target": str(target)}])
    ok, errors = reapply_links(config)

    assert str(target) in ok
    assert errors == []


def test_reapply_links_records_error_on_missing_source(tmp_path: Path):
    config = _make_config(
        tmp_path,
        links=[{"source": str(tmp_path / "ghost"), "target": str(tmp_path / "link")}],
    )
    ok, errors = reapply_links(config)

    assert ok == []
    assert len(errors) == 1
    assert errors[0][0] == str(tmp_path / "link")


def test_reapply_links_missing_fields_recorded_as_error(tmp_path: Path):
    config = _make_config(tmp_path, links=[{"source": "", "target": ""}])
    ok, errors = reapply_links(config)
    assert ok == []
    assert len(errors) == 1


# ---------------------------------------------------------------------------
# sync (integration)
# ---------------------------------------------------------------------------

def test_sync_returns_result_dict(tmp_path: Path):
    source = tmp_path / "dot" / ".tmux.conf"
    source.parent.mkdir()
    source.write_text("set -g mouse on")
    target = tmp_path / "home" / ".tmux.conf"

    config = {
        "repo_path": str(tmp_path),
        "links": [{"source": str(source), "target": str(target)}],
    }

    with patch("dotlink.sync.load_config", return_value=config), \
         patch("dotlink.sync.git_pull", return_value="Already up to date."):
        result = sync()

    assert result["pull_output"] == "Already up to date."
    assert str(target) in result["ok"]
    assert result["errors"] == []
