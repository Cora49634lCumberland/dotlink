"""Tests for dotlink.cli_tag."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from dotlink.cli_tag import tag_cmd


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def base_config(tmp_path: Path) -> dict:
    return {
        "repo_path": str(tmp_path),
        "links": {"bashrc": "~/.bashrc", "vimrc": "~/.vimrc"},
    }


def _patch(config: dict):
    return patch("dotlink.cli_tag.load_config", return_value=config), patch(
        "dotlink.cli_tag.find_config_path", return_value=".dotlink.json"
    )


def test_add_tag_success(runner: CliRunner, base_config: dict) -> None:
    p1, p2 = _patch(base_config)
    with p1, p2:
        result = runner.invoke(tag_cmd, ["add", "bashrc", "shell"])
    assert result.exit_code == 0
    assert "shell" in result.output


def test_add_tag_unknown_link(runner: CliRunner, base_config: dict) -> None:
    p1, p2 = _patch(base_config)
    with p1, p2:
        result = runner.invoke(tag_cmd, ["add", "ghost", "shell"])
    assert result.exit_code != 0
    assert "Unknown link" in result.output


def test_remove_tag_success(runner: CliRunner, base_config: dict) -> None:
    from dotlink.tag import add_tag
    add_tag(base_config, "vimrc", "editor")
    p1, p2 = _patch(base_config)
    with p1, p2:
        result = runner.invoke(tag_cmd, ["remove", "vimrc", "editor"])
    assert result.exit_code == 0
    assert "editor" in result.output


def test_remove_tag_not_found(runner: CliRunner, base_config: dict) -> None:
    p1, p2 = _patch(base_config)
    with p1, p2:
        result = runner.invoke(tag_cmd, ["remove", "bashrc", "ghost"])
    assert result.exit_code != 0


def test_list_no_tags(runner: CliRunner, base_config: dict) -> None:
    p1, p2 = _patch(base_config)
    with p1, p2:
        result = runner.invoke(tag_cmd, ["list", "bashrc"])
    assert result.exit_code == 0
    assert "No tags" in result.output


def test_list_with_tags(runner: CliRunner, base_config: dict) -> None:
    from dotlink.tag import add_tag
    add_tag(base_config, "bashrc", "shell")
    p1, p2 = _patch(base_config)
    with p1, p2:
        result = runner.invoke(tag_cmd, ["list", "bashrc"])
    assert "shell" in result.output


def test_filter_returns_matching_links(runner: CliRunner, base_config: dict) -> None:
    from dotlink.tag import add_tag
    add_tag(base_config, "bashrc", "shell")
    add_tag(base_config, "vimrc", "shell")
    p1, p2 = _patch(base_config)
    with p1, p2:
        result = runner.invoke(tag_cmd, ["filter", "shell"])
    assert "bashrc" in result.output
    assert "vimrc" in result.output


def test_filter_no_matches(runner: CliRunner, base_config: dict) -> None:
    p1, p2 = _patch(base_config)
    with p1, p2:
        result = runner.invoke(tag_cmd, ["filter", "nope"])
    assert "No links" in result.output
