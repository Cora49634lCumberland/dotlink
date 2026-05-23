"""Tests for dotlink.remote."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dotlink.remote import (
    Remote,
    RemoteError,
    add_remote,
    get_remote,
    list_remotes,
    remove_remote,
    set_remote_url,
)

REPO = Path("/fake/repo")


def _completed(stdout: str = "", stderr: str = "", returncode: int = 0):
    m = MagicMock()
    m.stdout = stdout
    m.stderr = stderr
    m.returncode = returncode
    return m


@patch("dotlink.remote._run")
def test_list_remotes_returns_remotes(mock_run):
    mock_run.return_value = _completed(
        stdout="origin\thttps://github.com/user/dots.git (fetch)\n"
               "origin\thttps://github.com/user/dots.git (push)\n"
               "backup\tgit@backup.host:dots.git (fetch)\n"
               "backup\tgit@backup.host:dots.git (push)\n"
    )
    remotes = list_remotes(REPO)
    assert len(remotes) == 2
    assert remotes[0] == Remote(name="origin", url="https://github.com/user/dots.git")
    assert remotes[1] == Remote(name="backup", url="git@backup.host:dots.git")


@patch("dotlink.remote._run")
def test_list_remotes_empty(mock_run):
    mock_run.return_value = _completed(stdout="")
    assert list_remotes(REPO) == []


@patch("dotlink.remote._run")
def test_list_remotes_raises_on_failure(mock_run):
    mock_run.return_value = _completed(stderr="not a git repo", returncode=128)
    with pytest.raises(RemoteError, match="not a git repo"):
        list_remotes(REPO)


@patch("dotlink.remote._run")
def test_add_remote_success(mock_run):
    mock_run.return_value = _completed()
    add_remote(REPO, "backup", "git@backup.host:dots.git")
    mock_run.assert_called_once_with(
        ["git", "remote", "add", "backup", "git@backup.host:dots.git"], cwd=REPO
    )


@patch("dotlink.remote._run")
def test_add_remote_raises_on_failure(mock_run):
    mock_run.return_value = _completed(stderr="already exists", returncode=3)
    with pytest.raises(RemoteError, match="already exists"):
        add_remote(REPO, "origin", "https://x.com/r.git")


@patch("dotlink.remote._run")
def test_remove_remote_success(mock_run):
    mock_run.return_value = _completed()
    remove_remote(REPO, "backup")
    mock_run.assert_called_once_with(["git", "remote", "remove", "backup"], cwd=REPO)


@patch("dotlink.remote._run")
def test_remove_remote_raises_on_failure(mock_run):
    mock_run.return_value = _completed(stderr="No such remote", returncode=2)
    with pytest.raises(RemoteError, match="No such remote"):
        remove_remote(REPO, "ghost")


@patch("dotlink.remote._run")
def test_set_remote_url_success(mock_run):
    mock_run.return_value = _completed()
    set_remote_url(REPO, "origin", "https://new.url/repo.git")
    mock_run.assert_called_once_with(
        ["git", "remote", "set-url", "origin", "https://new.url/repo.git"], cwd=REPO
    )


@patch("dotlink.remote._run")
def test_set_remote_url_raises_on_failure(mock_run):
    mock_run.return_value = _completed(stderr="no such remote", returncode=2)
    with pytest.raises(RemoteError, match="no such remote"):
        set_remote_url(REPO, "missing", "https://x.com")


@patch("dotlink.remote.list_remotes")
def test_get_remote_found(mock_list):
    mock_list.return_value = [
        Remote("origin", "https://github.com/u/r.git"),
        Remote("backup", "git@b.host:r.git"),
    ]
    r = get_remote(REPO, "backup")
    assert r == Remote("backup", "git@b.host:r.git")


@patch("dotlink.remote.list_remotes")
def test_get_remote_not_found_returns_none(mock_list):
    mock_list.return_value = [Remote("origin", "https://github.com/u/r.git")]
    assert get_remote(REPO, "missing") is None
