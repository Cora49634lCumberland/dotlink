"""Tests for dotlink.config module."""

import json
import pytest
from pathlib import Path

from dotlink.config import (
    DEFAULT_CONFIG_FILENAME,
    find_config_path,
    init_config,
    load_config,
    save_config,
)


def test_init_config_creates_file(tmp_path):
    config = init_config(tmp_path)
    config_file = tmp_path / DEFAULT_CONFIG_FILENAME
    assert config_file.exists()
    assert config["version"] == 1
    assert config["links"] == {}
    assert config["repo_root"] == str(tmp_path)


def test_init_config_raises_if_exists(tmp_path):
    init_config(tmp_path)
    with pytest.raises(FileExistsError):
        init_config(tmp_path)


def test_save_and_load_roundtrip(tmp_path):
    config_path = tmp_path / DEFAULT_CONFIG_FILENAME
    original = {"version": 1, "links": {"~/.bashrc": "bash/bashrc"}, "repo_root": str(tmp_path)}
    save_config(original, config_path)
    loaded = load_config(config_path)
    assert loaded["links"] == original["links"]
    assert loaded["version"] == 1


def test_load_config_missing_keys_filled_with_defaults(tmp_path):
    config_path = tmp_path / DEFAULT_CONFIG_FILENAME
    # Write a minimal config without all keys
    config_path.write_text(json.dumps({"version": 1}), encoding="utf-8")
    loaded = load_config(config_path)
    assert "links" in loaded
    assert loaded["links"] == {}


def test_load_config_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nonexistent.json")


def test_find_config_path_in_current_dir(tmp_path):
    config_path = tmp_path / DEFAULT_CONFIG_FILENAME
    config_path.write_text("{}", encoding="utf-8")
    found = find_config_path(tmp_path)
    assert found == config_path


def test_find_config_path_walks_up(tmp_path):
    config_path = tmp_path / DEFAULT_CONFIG_FILENAME
    config_path.write_text("{}", encoding="utf-8")
    nested = tmp_path / "a" / "b" / "c"
    nested.mkdir(parents=True)
    found = find_config_path(nested)
    assert found == config_path


def test_find_config_path_returns_none_when_missing(tmp_path):
    found = find_config_path(tmp_path)
    assert found is None


def test_save_config_creates_parent_dirs(tmp_path):
    config_path = tmp_path / "deep" / "nested" / DEFAULT_CONFIG_FILENAME
    save_config({"version": 1, "links": {}, "repo_root": None}, config_path)
    assert config_path.exists()
