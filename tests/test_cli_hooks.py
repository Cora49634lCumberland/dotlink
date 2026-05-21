"""Tests for dotlink.cli_hooks CLI commands."""

import stat
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from dotlink.cli_hooks import hooks_cmd
from dotlink.hooks import HookError


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def base_config(tmp_path):
    return {"repo_path": str(tmp_path), "links": {}}


def test_list_no_hooks(runner, base_config):
    with patch("dotlink.cli_hooks.load_config", return_value=base_config):
        result = runner.invoke(hooks_cmd, ["list"])
    assert result.exit_code == 0
    assert "No hooks installed" in result.output


def test_list_with_hooks(runner, base_config):
    with patch("dotlink.cli_hooks.load_config", return_value=base_config), \
         patch("dotlink.cli_hooks.list_hooks", return_value=["pre-link", "post-sync"]):
        result = runner.invoke(hooks_cmd, ["list"])
    assert result.exit_code == 0
    assert "pre-link" in result.output
    assert "post-sync" in result.output


def test_install_hook(runner, base_config, tmp_path):
    script = tmp_path / "myhook.sh"
    script.write_text("#!/bin/sh\necho ok\n")
    script.chmod(0o755)

    with patch("dotlink.cli_hooks.load_config", return_value=base_config):
        result = runner.invoke(hooks_cmd, ["install", "pre-link", str(script)])

    assert result.exit_code == 0
    assert "Installed hook 'pre-link'" in result.output
    dest = Path(base_config["repo_path"]) / ".dotlink" / "hooks" / "pre-link"
    assert dest.exists()
    assert dest.stat().st_mode & stat.S_IEXEC


def test_remove_hook_present(runner, base_config, tmp_path):
    hook_dir = tmp_path / ".dotlink" / "hooks"
    hook_dir.mkdir(parents=True)
    hook_file = hook_dir / "post-link"
    hook_file.write_text("#!/bin/sh\n")
    hook_file.chmod(0o755)

    with patch("dotlink.cli_hooks.load_config", return_value=base_config):
        result = runner.invoke(hooks_cmd, ["remove", "post-link"])

    assert result.exit_code == 0
    assert "Removed hook 'post-link'" in result.output
    assert not hook_file.exists()


def test_remove_hook_absent(runner, base_config):
    with patch("dotlink.cli_hooks.load_config", return_value=base_config):
        result = runner.invoke(hooks_cmd, ["remove", "post-link"])
    assert result.exit_code == 0
    assert "not installed" in result.output


def test_run_hook_success(runner, base_config):
    mock_result = MagicMock(stdout="done\n", success=True)
    with patch("dotlink.cli_hooks.load_config", return_value=base_config), \
         patch("dotlink.cli_hooks.run_hook", return_value=mock_result):
        result = runner.invoke(hooks_cmd, ["run", "pre-sync"])
    assert result.exit_code == 0
    assert "completed successfully" in result.output


def test_run_hook_not_installed(runner, base_config):
    with patch("dotlink.cli_hooks.load_config", return_value=base_config), \
         patch("dotlink.cli_hooks.run_hook", return_value=None):
        result = runner.invoke(hooks_cmd, ["run", "pre-sync"])
    assert result.exit_code == 0
    assert "not installed" in result.output


def test_run_hook_failure(runner, base_config):
    with patch("dotlink.cli_hooks.load_config", return_value=base_config), \
         patch("dotlink.cli_hooks.run_hook", side_effect=HookError("script failed")):
        result = runner.invoke(hooks_cmd, ["run", "post-sync"])
    assert result.exit_code != 0
    assert "script failed" in result.output
