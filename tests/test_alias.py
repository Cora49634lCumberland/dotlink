"""Tests for dotlink.alias."""
import pytest

from dotlink.alias import (
    AliasError,
    _aliases_path,
    add_alias,
    load_aliases,
    remove_alias,
    resolve_alias,
    save_aliases,
)


@pytest.fixture()
def config(tmp_path):
    return {"repo_path": str(tmp_path)}


def test_aliases_path_uses_repo(config, tmp_path):
    assert _aliases_path(config) == tmp_path / ".dotlink_aliases.json"


def test_load_aliases_empty_when_no_file(config):
    assert load_aliases(config) == {}


def test_save_and_load_roundtrip(config):
    data = {"vim": "~/.vimrc", "zsh": "~/.zshrc"}
    save_aliases(config, data)
    assert load_aliases(config) == data


def test_load_aliases_raises_on_corrupt_file(config, tmp_path):
    (tmp_path / ".dotlink_aliases.json").write_text("not json")
    with pytest.raises(AliasError, match="Corrupt"):
        load_aliases(config)


def test_add_alias_creates_entry(config):
    add_alias(config, "vim", "~/.vimrc")
    assert load_aliases(config)["vim"] == "~/.vimrc"


def test_add_alias_raises_if_exists(config):
    add_alias(config, "vim", "~/.vimrc")
    with pytest.raises(AliasError, match="already exists"):
        add_alias(config, "vim", "~/.other")


def test_remove_alias_deletes_entry(config):
    add_alias(config, "vim", "~/.vimrc")
    remove_alias(config, "vim")
    assert "vim" not in load_aliases(config)


def test_remove_alias_raises_if_missing(config):
    with pytest.raises(AliasError, match="not found"):
        remove_alias(config, "nonexistent")


def test_resolve_alias_returns_target(config):
    add_alias(config, "zsh", "~/.zshrc")
    assert resolve_alias(config, "zsh") == "~/.zshrc"


def test_resolve_alias_raises_for_unknown(config):
    with pytest.raises(AliasError, match="Unknown alias"):
        resolve_alias(config, "ghost")
