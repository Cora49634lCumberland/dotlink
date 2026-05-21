"""Tests for dotlink.cli_template."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from dotlink.cli_template import template_cmd
from dotlink.template import TEMPLATE_SUFFIX


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def base_config(tmp_path: Path) -> dict:
    repo = tmp_path / "repo"
    repo.mkdir()
    return {"repo_path": str(repo), "links": {}}


def _write(path: Path, content: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_list_no_templates(runner: CliRunner, base_config: dict):
    with patch("dotlink.cli_template.load_config", return_value=base_config):
        result = runner.invoke(template_cmd, ["list"])
    assert result.exit_code == 0
    assert "No templates" in result.output


def test_list_with_templates(runner: CliRunner, base_config: dict):
    repo = Path(base_config["repo_path"])
    _write(repo / f"bashrc{TEMPLATE_SUFFIX}", "")
    _write(repo / f"sub/vimrc{TEMPLATE_SUFFIX}", "")
    with patch("dotlink.cli_template.load_config", return_value=base_config):
        result = runner.invoke(template_cmd, ["list"])
    assert result.exit_code == 0
    assert f"bashrc{TEMPLATE_SUFFIX}" in result.output
    assert f"sub/vimrc{TEMPLATE_SUFFIX}" in result.output


def test_render_all(runner: CliRunner, base_config: dict):
    repo = Path(base_config["repo_path"])
    _write(repo / f"cfg{TEMPLATE_SUFFIX}", "user={{ USER }}")
    with patch("dotlink.cli_template.load_config", return_value=base_config):
        result = runner.invoke(template_cmd, ["render"])
    assert result.exit_code == 0
    assert "cfg" in result.output


def test_render_single_file(runner: CliRunner, base_config: dict, tmp_path: Path):
    src = _write(tmp_path / f"x{TEMPLATE_SUFFIX}", "val={{ HOME }}")
    with patch("dotlink.cli_template.load_config", return_value=base_config):
        result = runner.invoke(template_cmd, ["render", str(src)])
    assert result.exit_code == 0
    dest = src.with_suffix("")
    assert dest.exists()
    assert str(Path.home()) in dest.read_text()


def test_render_with_extra_var(runner: CliRunner, base_config: dict, tmp_path: Path):
    src = _write(tmp_path / f"t{TEMPLATE_SUFFIX}", "n={{ NAME }}")
    with patch("dotlink.cli_template.load_config", return_value=base_config):
        result = runner.invoke(template_cmd, ["render", str(src), "-v", "NAME=bob"])
    assert result.exit_code == 0
    assert (tmp_path / "t").read_text() == "n=bob"


def test_render_strict_fails_on_unknown(runner: CliRunner, base_config: dict, tmp_path: Path):
    src = _write(tmp_path / f"t{TEMPLATE_SUFFIX}", "{{ GHOST }}")
    with patch("dotlink.cli_template.load_config", return_value=base_config):
        result = runner.invoke(template_cmd, ["render", str(src), "--strict"])
    assert result.exit_code != 0
    assert "GHOST" in result.output


def test_render_bad_var_format(runner: CliRunner, base_config: dict, tmp_path: Path):
    src = _write(tmp_path / f"t{TEMPLATE_SUFFIX}", "x")
    with patch("dotlink.cli_template.load_config", return_value=base_config):
        result = runner.invoke(template_cmd, ["render", str(src), "-v", "NOEQUALS"])
    assert result.exit_code != 0
