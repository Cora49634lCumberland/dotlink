"""Tests for dotlink.hooks."""

import stat
from pathlib import Path

import pytest

from dotlink.hooks import (
    HookError,
    HookResult,
    find_hook,
    hooks_dir,
    list_hooks,
    run_hook,
)


@pytest.fixture()
def config(tmp_path):
    return {"repo_path": str(tmp_path)}


@pytest.fixture()
def hook_dir(config, tmp_path):
    d = tmp_path / ".dotlink" / "hooks"
    d.mkdir(parents=True)
    return d


def _write_hook(hook_dir: Path, name: str, script: str) -> Path:
    p = hook_dir / name
    p.write_text(script)
    p.chmod(p.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return p


def test_hooks_dir_uses_repo_path(config, tmp_path):
    expected = tmp_path / ".dotlink" / "hooks"
    assert hooks_dir(config) == expected


def test_find_hook_returns_none_when_absent(config):
    assert find_hook(config, "pre-link") is None


def test_find_hook_returns_path_when_present(config, hook_dir):
    _write_hook(hook_dir, "pre-link", "#!/bin/sh\nexit 0\n")
    result = find_hook(config, "pre-link")
    assert result is not None
    assert result.name == "pre-link"


def test_find_hook_raises_on_unknown_name(config):
    with pytest.raises(ValueError, match="Unknown hook"):
        find_hook(config, "not-a-hook")


def test_find_hook_ignores_non_executable(config, hook_dir):
    p = hook_dir / "pre-link"
    p.write_text("#!/bin/sh\nexit 0\n")
    p.chmod(0o644)  # not executable
    assert find_hook(config, "pre-link") is None


def test_run_hook_returns_none_when_absent(config):
    assert run_hook(config, "post-sync") is None


def test_run_hook_returns_result_on_success(config, hook_dir):
    _write_hook(hook_dir, "post-link", "#!/bin/sh\necho hello\n")
    result = run_hook(config, "post-link")
    assert isinstance(result, HookResult)
    assert result.success
    assert "hello" in result.stdout


def test_run_hook_raises_on_failure(config, hook_dir):
    _write_hook(hook_dir, "pre-sync", "#!/bin/sh\nexit 1\n")
    with pytest.raises(HookError, match="pre-sync"):
        run_hook(config, "pre-sync")


def test_list_hooks_empty_when_no_dir(config):
    assert list_hooks(config) == []


def test_list_hooks_returns_installed_hooks(config, hook_dir):
    _write_hook(hook_dir, "pre-link", "#!/bin/sh\n")
    _write_hook(hook_dir, "post-sync", "#!/bin/sh\n")
    result = list_hooks(config)
    assert "pre-link" in result
    assert "post-sync" in result


def test_list_hooks_ignores_unknown_names(config, hook_dir):
    _write_hook(hook_dir, "pre-link", "#!/bin/sh\n")
    unknown = hook_dir / "custom-script"
    unknown.write_text("#!/bin/sh\n")
    unknown.chmod(0o755)
    assert "custom-script" not in list_hooks(config)
