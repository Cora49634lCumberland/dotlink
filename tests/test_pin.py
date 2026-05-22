"""Tests for dotlink.pin."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dotlink.pin import (
    PinError,
    _pins_path,
    _hash_file,
    pin_link,
    unpin_link,
    load_pins,
    check_pin,
)


@pytest.fixture()
def config(tmp_path: Path) -> dict:
    repo = tmp_path / "repo"
    repo.mkdir()
    return {"repo_path": str(repo)}


@pytest.fixture()
def src_file(tmp_path: Path) -> Path:
    f = tmp_path / "vimrc"
    f.write_text("set number\n")
    return f


def test_pins_path_uses_repo(config: dict) -> None:
    p = _pins_path(config)
    assert p.parent == Path(config["repo_path"])
    assert p.name == ".dotlink_pins.json"


def test_hash_file_returns_hex(src_file: Path) -> None:
    h = _hash_file(src_file)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_pin_link_creates_entry(config: dict, src_file: Path) -> None:
    pin = pin_link(config, str(src_file))
    assert pin.source == str(src_file)
    assert len(pin.sha256) == 64


def test_pin_link_persists_to_disk(config: dict, src_file: Path) -> None:
    pin_link(config, str(src_file), label="my label")
    raw = json.loads(_pins_path(config).read_text())
    assert str(src_file) in raw
    assert raw[str(src_file)]["label"] == "my label"


def test_pin_link_raises_if_source_missing(config: dict, tmp_path: Path) -> None:
    missing = str(tmp_path / "ghost.txt")
    with pytest.raises(PinError, match="not found"):
        pin_link(config, missing)


def test_load_pins_empty_when_no_file(config: dict) -> None:
    assert load_pins(config) == {}


def test_unpin_removes_entry(config: dict, src_file: Path) -> None:
    pin_link(config, str(src_file))
    unpin_link(config, str(src_file))
    assert load_pins(config) == {}


def test_unpin_raises_if_not_pinned(config: dict) -> None:
    with pytest.raises(PinError, match="No pin found"):
        unpin_link(config, "/some/file.txt")


def test_check_pin_returns_none_when_not_pinned(config: dict, src_file: Path) -> None:
    assert check_pin(config, str(src_file)) is None


def test_check_pin_returns_true_when_unchanged(config: dict, src_file: Path) -> None:
    pin_link(config, str(src_file))
    assert check_pin(config, str(src_file)) is True


def test_check_pin_returns_false_when_drifted(config: dict, src_file: Path) -> None:
    pin_link(config, str(src_file))
    src_file.write_text("set relativenumber\n")
    assert check_pin(config, str(src_file)) is False


def test_check_pin_returns_false_when_file_deleted(config: dict, src_file: Path) -> None:
    pin_link(config, str(src_file))
    src_file.unlink()
    assert check_pin(config, str(src_file)) is False
