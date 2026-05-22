"""Tests for dotlink.cli_audit."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from click.testing import CliRunner
from dotlink.cli_audit import audit_cmd
from dotlink.audit import record


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def base_config(tmp_path: Path, monkeypatch):
    cfg_path = tmp_path / ".dotlink.json"
    config = {"repo_path": str(tmp_path), "links": {}}
    cfg_path.write_text(json.dumps(config))
    monkeypatch.chdir(tmp_path)
    return config


def test_list_no_entries(runner, base_config):
    result = runner.invoke(audit_cmd, ["list"])
    assert result.exit_code == 0
    assert "No audit entries" in result.output


def test_list_shows_entries(runner, base_config, tmp_path):
    record(base_config, "link_added", source="s", target="t")
    result = runner.invoke(audit_cmd, ["list"])
    assert result.exit_code == 0
    assert "link_added" in result.output
    assert "source=s" in result.output


def test_list_last_limits_output(runner, base_config):
    for i in range(5):
        record(base_config, f"op_{i}")
    result = runner.invoke(audit_cmd, ["list", "--last", "2"])
    assert result.exit_code == 0
    lines = [l for l in result.output.strip().splitlines() if l]
    assert len(lines) == 2
    assert "op_4" in lines[-1]


def test_clear_removes_entries(runner, base_config):
    record(base_config, "some_op")
    result = runner.invoke(audit_cmd, ["clear"], input="y\n")
    assert result.exit_code == 0
    assert "Cleared 1" in result.output


def test_clear_aborted_keeps_entries(runner, base_config):
    record(base_config, "some_op")
    result = runner.invoke(audit_cmd, ["clear"], input="n\n")
    assert result.exit_code != 0 or "Aborted" in result.output
    from dotlink.audit import load_entries
    assert len(load_entries(base_config)) == 1
