"""Tests for dotlink.ignore."""

from __future__ import annotations

import pytest
from pathlib import Path

from dotlink.ignore import (
    IgnoreError,
    DEFAULT_PATTERNS,
    _ignore_path,
    load_patterns,
    save_patterns,
    add_pattern,
    remove_pattern,
    is_ignored,
)


@pytest.fixture()
def config(tmp_path: Path) -> dict:
    return {"repo_path": str(tmp_path)}


def test_load_patterns_returns_defaults_when_no_file(config):
    patterns = load_patterns(config)
    assert patterns == DEFAULT_PATTERNS


def test_save_and_load_roundtrip(config):
    patterns = ["*.log", ".env", "secret/"]
    save_patterns(config, patterns)
    loaded = load_patterns(config)
    assert loaded == patterns


def test_save_creates_dotignore_file(config):
    save_patterns(config, ["*.log"])
    ignore_file = _ignore_path(config)
    assert ignore_file.exists()
    assert "*.log" in ignore_file.read_text()


def test_load_ignores_comments_and_blank_lines(config):
    _ignore_path(config).write_text("# comment\n\n*.swp\n  \n.DS_Store\n")
    patterns = load_patterns(config)
    assert patterns == ["*.swp", ".DS_Store"]


def test_add_pattern_appends(config):
    patterns = add_pattern(config, "*.log")
    assert "*.log" in patterns


def test_add_pattern_raises_if_duplicate(config):
    add_pattern(config, "*.log")
    with pytest.raises(IgnoreError, match="already exists"):
        add_pattern(config, "*.log")


def test_remove_pattern_removes(config):
    save_patterns(config, ["*.log", ".env"])
    patterns = remove_pattern(config, "*.log")
    assert "*.log" not in patterns
    assert ".env" in patterns


def test_remove_pattern_raises_if_not_found(config):
    save_patterns(config, ["*.log"])
    with pytest.raises(IgnoreError, match="not found"):
        remove_pattern(config, "missing_pattern")


@pytest.mark.parametrize("name,patterns,expected", [
    ("file.swp", ["*.swp"], True),
    (".DS_Store", [".DS_Store"], True),
    ("notes.md", ["*.swp", ".git"], False),
    (".git", [".git"], True),
    ("README.md", ["*.log"], False),
])
def test_is_ignored(name, patterns, expected):
    assert is_ignored(name, patterns) == expected
