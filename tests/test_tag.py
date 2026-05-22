"""Tests for dotlink.tag."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dotlink.tag import (
    TagError,
    _tags_path,
    add_tag,
    links_with_tag,
    load_tags,
    remove_tag,
    save_tags,
    tags_for_link,
)


@pytest.fixture()
def config(tmp_path: Path) -> dict:
    return {
        "repo_path": str(tmp_path),
        "links": {"bashrc": "~/.bashrc", "vimrc": "~/.vimrc"},
    }


def test_tags_path_uses_repo(config: dict, tmp_path: Path) -> None:
    assert _tags_path(config) == tmp_path / ".dotlink_tags.json"


def test_load_tags_empty_when_no_file(config: dict) -> None:
    assert load_tags(config) == {}


def test_save_and_load_roundtrip(config: dict) -> None:
    data = {"bashrc": ["shell", "home"]}
    save_tags(config, data)
    assert load_tags(config) == data


def test_load_tags_raises_on_corrupt_file(config: dict, tmp_path: Path) -> None:
    (tmp_path / ".dotlink_tags.json").write_text("not-json")
    with pytest.raises(TagError, match="Corrupt"):
        load_tags(config)


def test_add_tag_creates_entry(config: dict) -> None:
    tags = add_tag(config, "bashrc", "shell")
    assert "shell" in tags["bashrc"]


def test_add_tag_idempotent(config: dict) -> None:
    add_tag(config, "bashrc", "shell")
    tags = add_tag(config, "bashrc", "shell")
    assert tags["bashrc"].count("shell") == 1


def test_add_tag_raises_for_unknown_link(config: dict) -> None:
    with pytest.raises(TagError, match="Unknown link"):
        add_tag(config, "nonexistent", "shell")


def test_remove_tag_removes_entry(config: dict) -> None:
    add_tag(config, "vimrc", "editor")
    tags = remove_tag(config, "vimrc", "editor")
    assert "vimrc" not in tags


def test_remove_tag_raises_when_absent(config: dict) -> None:
    with pytest.raises(TagError, match="not found"):
        remove_tag(config, "bashrc", "ghost")


def test_links_with_tag_returns_correct_names(config: dict) -> None:
    add_tag(config, "bashrc", "shell")
    add_tag(config, "vimrc", "editor")
    add_tag(config, "vimrc", "shell")
    result = links_with_tag(config, "shell")
    assert set(result) == {"bashrc", "vimrc"}


def test_links_with_tag_empty_when_none_match(config: dict) -> None:
    assert links_with_tag(config, "nope") == []


def test_tags_for_link_returns_list(config: dict) -> None:
    add_tag(config, "bashrc", "a")
    add_tag(config, "bashrc", "b")
    assert set(tags_for_link(config, "bashrc")) == {"a", "b"}


def test_tags_for_link_empty_when_untagged(config: dict) -> None:
    assert tags_for_link(config, "bashrc") == []
