"""Tests for dotlink.links module."""

import pytest
from pathlib import Path

from dotlink.links import (
    create_link,
    remove_link,
    link_status,
    list_links,
    LinkError,
)


@pytest.fixture
def tmp_source(tmp_path):
    """Create a real source file in a temp directory."""
    src = tmp_path / "repo" / ".bashrc"
    src.parent.mkdir(parents=True)
    src.write_text("# bashrc content")
    return src


@pytest.fixture
def tmp_target(tmp_path):
    """Return a target path that does not yet exist."""
    return tmp_path / "home" / ".bashrc"


def test_create_link_creates_symlink(tmp_source, tmp_target):
    create_link(str(tmp_source), str(tmp_target))
    assert tmp_target.is_symlink()
    assert tmp_target.resolve() == tmp_source.resolve()


def test_create_link_creates_parent_dirs(tmp_source, tmp_path):
    deep_target = tmp_path / "home" / "nested" / "dir" / ".bashrc"
    create_link(str(tmp_source), str(deep_target))
    assert deep_target.is_symlink()


def test_create_link_raises_if_source_missing(tmp_path):
    with pytest.raises(LinkError, match="Source does not exist"):
        create_link(str(tmp_path / "nonexistent"), str(tmp_path / "target"))


def test_create_link_raises_if_target_exists(tmp_source, tmp_target):
    tmp_target.parent.mkdir(parents=True, exist_ok=True)
    tmp_target.write_text("existing")
    with pytest.raises(LinkError, match="Target already exists"):
        create_link(str(tmp_source), str(tmp_target))


def test_create_link_overwrite(tmp_source, tmp_target):
    tmp_target.parent.mkdir(parents=True, exist_ok=True)
    tmp_target.write_text("existing")
    create_link(str(tmp_source), str(tmp_target), overwrite=True)
    assert tmp_target.is_symlink()


def test_remove_link(tmp_source, tmp_target):
    create_link(str(tmp_source), str(tmp_target))
    remove_link(str(tmp_target))
    assert not tmp_target.exists()


def test_remove_link_raises_if_not_symlink(tmp_path):
    real_file = tmp_path / "real.txt"
    real_file.write_text("data")
    with pytest.raises(LinkError, match="not a symlink"):
        remove_link(str(real_file))


def test_link_status_linked(tmp_source, tmp_target):
    create_link(str(tmp_source), str(tmp_target))
    assert link_status(str(tmp_source), str(tmp_target)) == "linked"


def test_link_status_not_linked(tmp_source, tmp_target):
    assert link_status(str(tmp_source), str(tmp_target)) == "not_linked"


def test_link_status_missing_source(tmp_path):
    assert link_status(str(tmp_path / "ghost"), str(tmp_path / "target")) == "missing_source"


def test_link_status_conflict(tmp_source, tmp_target):
    tmp_target.parent.mkdir(parents=True, exist_ok=True)
    tmp_target.write_text("conflict")
    assert link_status(str(tmp_source), str(tmp_target)) == "conflict"


def test_list_links(tmp_source, tmp_target):
    create_link(str(tmp_source), str(tmp_target))
    result = list_links({str(tmp_source): str(tmp_target)})
    assert len(result) == 1
    assert result[0]["status"] == "linked"
    assert result[0]["source"] == str(tmp_source)
