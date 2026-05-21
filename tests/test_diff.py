"""Tests for dotlink.diff."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from dotlink.diff import DiffResult, DiffError, diff_link, diff_all


@pytest.fixture()
def repo_file(tmp_path: Path) -> Path:
    f = tmp_path / "repo" / "vimrc"
    f.parent.mkdir(parents=True)
    f.write_text("set number\n")
    return f


@pytest.fixture()
def home_link(tmp_path: Path, repo_file: Path) -> Path:
    link = tmp_path / "home" / ".vimrc"
    link.parent.mkdir(parents=True)
    link.symlink_to(repo_file)
    return link


def test_diff_identical(repo_file: Path, home_link: Path):
    result = diff_link(str(repo_file), str(home_link))
    assert result.status == "identical"
    assert not result.has_diff
    assert result.unified_diff is None


def test_diff_differs(repo_file: Path, home_link: Path, tmp_path: Path):
    # Break the symlink so target points elsewhere but content differs
    modified = tmp_path / "home" / ".vimrc_modified"
    modified.write_text("set nonumber\n")
    result = diff_link(str(repo_file), str(modified))
    # modified is a plain file, not a symlink → not_symlink
    assert result.status == "not_symlink"


def test_diff_missing_source(tmp_path: Path, home_link: Path):
    missing = tmp_path / "no_such_file"
    result = diff_link(str(missing), str(home_link))
    assert result.status == "missing_source"


def test_diff_missing_target(repo_file: Path, tmp_path: Path):
    missing = tmp_path / "home" / ".no_such_link"
    result = diff_link(str(repo_file), str(missing))
    assert result.status == "missing_target"


def test_diff_not_symlink(repo_file: Path, tmp_path: Path):
    plain = tmp_path / "home" / "plain.txt"
    plain.parent.mkdir(parents=True, exist_ok=True)
    plain.write_text("set number\n")
    result = diff_link(str(repo_file), str(plain))
    assert result.status == "not_symlink"


def test_diff_raises_when_diff_missing(repo_file: Path, home_link: Path):
    with patch("dotlink.diff.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(DiffError, match="diff.*not found"):
            diff_link(str(repo_file), str(home_link))


def test_diff_all_returns_results(repo_file: Path, home_link: Path):
    config = {
        "links": [
            {"source": str(repo_file), "target": str(home_link)},
        ]
    }
    results = diff_all(config)
    assert len(results) == 1
    assert isinstance(results[0], DiffResult)


def test_diff_all_empty_links():
    results = diff_all({"links": []})
    assert results == []


def test_diff_result_has_diff_false_for_identical(repo_file: Path, home_link: Path):
    result = diff_link(str(repo_file), str(home_link))
    assert result.has_diff is False
