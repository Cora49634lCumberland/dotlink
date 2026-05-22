"""Tests for dotlink.cli_ignore CLI commands."""

from __future__ import annotations

import pytest
from pathlib import Path
from click.testing import CliRunner

from dotlink.cli_ignore import ignore_cmd
from dotlink.ignore import save_patterns, _ignore_path


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def base_config(tmp_path: Path, monkeypatch):
    cfg_file = tmp_path / "dotlink.toml"
    cfg_file.write_text(
        f'[dotlink]\nrepo_path = "{tmp_path}"\nhome_path = "{tmp_path / "home"}"\n'
    )
    monkeypatch.chdir(tmp_path)
    return {"repo_path": str(tmp_path), "home_path": str(tmp_path / "home")}


def test_list_no_patterns_shows_defaults(runner, base_config):
    result = runner.invoke(ignore_cmd, ["list"])
    assert result.exit_code == 0
    assert ".git" in result.output


def test_list_with_saved_patterns(runner, base_config, tmp_path):
    save_patterns(base_config, ["*.log", ".env"])
    result = runner.invoke(ignore_cmd, ["list"])
    assert result.exit_code == 0
    assert "*.log" in result.output
    assert ".env" in result.output


def test_add_pattern(runner, base_config):
    result = runner.invoke(ignore_cmd, ["add", "*.log"])
    assert result.exit_code == 0
    assert "Added" in result.output
    assert "*.log" in _ignore_path(base_config).read_text()


def test_add_multiple_patterns(runner, base_config):
    """Adding several patterns in sequence should persist all of them."""
    for pattern in ["*.log", ".env", "*.swp"]:
        result = runner.invoke(ignore_cmd, ["add", pattern])
        assert result.exit_code == 0

    ignore_text = _ignore_path(base_config).read_text()
    assert "*.log" in ignore_text
    assert ".env" in ignore_text
    assert "*.swp" in ignore_text


def test_add_duplicate_pattern_fails(runner, base_config):
    runner.invoke(ignore_cmd, ["add", "*.log"])
    result = runner.invoke(ignore_cmd, ["add", "*.log"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_remove_pattern(runner, base_config):
    save_patterns(base_config, ["*.log", ".env"])
    result = runner.invoke(ignore_cmd, ["remove", "*.log"])
    assert result.exit_code == 0
    assert "Removed" in result.output
    assert "*.log" not in _ignore_path(base_config).read_text()


def test_remove_missing_pattern_fails(runner, base_config):
    save_patterns(base_config, [".env"])
    result = runner.invoke(ignore_cmd, ["remove", "*.log"])
    assert result.exit_code == 1
    assert "Error" in result.output


def test_check_ignored(runner, base_config):
    save_patterns(base_config, ["*.swp"])
    result = runner.invoke(ignore_cmd, ["check", "file.swp"])
    assert result.exit_code == 0
    assert "IGNORED" in result.output


def test_check_not_ignored(runner, base_config):
    save_patterns(base_config, ["*.swp"])
    result = runner.invoke(ignore_cmd, ["check", "README.md"])
    assert result.exit_code == 0
    assert "NOT ignored" in result.output
