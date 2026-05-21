"""Tests for dotlink.profile."""

import json
import pytest
from pathlib import Path

from dotlink.profile import (
    ProfileError,
    load_profiles,
    save_profiles,
    create_profile,
    delete_profile,
    add_link_to_profile,
    get_profile,
    list_profiles,
)


@pytest.fixture
def config(tmp_path):
    return {"repo_path": str(tmp_path)}


def test_load_profiles_empty_when_no_file(config):
    assert load_profiles(config) == {}


def test_create_profile_creates_entry(config):
    create_profile(config, "work")
    assert "work" in load_profiles(config)


def test_create_profile_raises_if_exists(config):
    create_profile(config, "work")
    with pytest.raises(ProfileError, match="already exists"):
        create_profile(config, "work")


def test_delete_profile_removes_entry(config):
    create_profile(config, "home")
    delete_profile(config, "home")
    assert "home" not in load_profiles(config)


def test_delete_profile_raises_if_missing(config):
    with pytest.raises(ProfileError, match="not found"):
        delete_profile(config, "ghost")


def test_add_link_to_profile(config):
    create_profile(config, "work")
    add_link_to_profile(config, "work", "repo/vimrc", "~/.vimrc")
    links = get_profile(config, "work")
    assert {"source": "repo/vimrc", "target": "~/.vimrc"} in links


def test_add_link_raises_if_profile_missing(config):
    with pytest.raises(ProfileError, match="not found"):
        add_link_to_profile(config, "nope", "a", "b")


def test_add_link_raises_on_duplicate(config):
    create_profile(config, "work")
    add_link_to_profile(config, "work", "repo/vimrc", "~/.vimrc")
    with pytest.raises(ProfileError, match="already exists"):
        add_link_to_profile(config, "work", "repo/vimrc", "~/.vimrc")


def test_get_profile_raises_if_missing(config):
    with pytest.raises(ProfileError, match="not found"):
        get_profile(config, "missing")


def test_list_profiles_returns_sorted(config):
    create_profile(config, "work")
    create_profile(config, "home")
    create_profile(config, "server")
    assert list_profiles(config) == ["home", "server", "work")


def test_load_profiles_raises_on_malformed_json(config, tmp_path):
    profiles_path = tmp_path / "profiles.json"
    profiles_path.write_text("{invalid json")
    with pytest.raises(ProfileError, match="Malformed"):
        load_profiles(config)


def test_save_and_load_roundtrip(config):
    data = {"dev": [{"source": "s", "target": "t"}]}
    save_profiles(config, data)
    assert load_profiles(config) == data
