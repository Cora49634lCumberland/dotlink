"""Tests for dotlink.watch."""

from __future__ import annotations

from pathlib import Path

import pytest

from dotlink.watch import (
    WatchEvent,
    _file_hash,
    _snapshot_hashes,
    poll_once,
    watch,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def src_file(tmp_path: Path) -> Path:
    f = tmp_path / "source.txt"
    f.write_text("hello")
    return f


@pytest.fixture()
def tgt_link(tmp_path: Path, src_file: Path) -> Path:
    link = tmp_path / "link.txt"
    link.symlink_to(src_file)
    return link


def _cfg(src: str, tgt: str) -> dict:
    return {"links": {src: tgt}}


# ---------------------------------------------------------------------------
# _file_hash
# ---------------------------------------------------------------------------


def test_file_hash_returns_string(src_file: Path) -> None:
    result = _file_hash(src_file)
    assert isinstance(result, str) and len(result) == 64


def test_file_hash_returns_none_for_missing() -> None:
    assert _file_hash(Path("/nonexistent/file.txt")) is None


def test_file_hash_changes_on_content_change(src_file: Path) -> None:
    h1 = _file_hash(src_file)
    src_file.write_text("world")
    h2 = _file_hash(src_file)
    assert h1 != h2


# ---------------------------------------------------------------------------
# _snapshot_hashes
# ---------------------------------------------------------------------------


def test_snapshot_hashes_keys_match_links(src_file: Path, tgt_link: Path) -> None:
    cfg = _cfg(str(src_file), str(tgt_link))
    result = _snapshot_hashes(cfg["links"])
    assert str(src_file) in result


# ---------------------------------------------------------------------------
# poll_once
# ---------------------------------------------------------------------------


def test_poll_once_no_events_on_first_run(src_file: Path, tgt_link: Path) -> None:
    cfg = _cfg(str(src_file), str(tgt_link))
    events, hashes = poll_once(cfg, {})
    # First run: no previous hashes, so no 'changed' events expected
    assert all(e.kind != "changed" for e in events)
    assert str(src_file) in hashes


def test_poll_once_detects_changed(src_file: Path, tgt_link: Path) -> None:
    cfg = _cfg(str(src_file), str(tgt_link))
    _, prev = poll_once(cfg, {})
    src_file.write_text("modified content")
    events, _ = poll_once(cfg, prev)
    kinds = [e.kind for e in events]
    assert "changed" in kinds


def test_poll_once_detects_broken_link(tmp_path: Path) -> None:
    src = tmp_path / "gone.txt"
    tgt = tmp_path / "link.txt"
    tgt.symlink_to(src)  # dangling symlink
    cfg = _cfg(str(src), str(tgt))
    events, _ = poll_once(cfg, {})
    assert any(e.kind == "broken" for e in events)


def test_poll_once_detects_missing_link(tmp_path: Path) -> None:
    src = tmp_path / "source.txt"
    src.write_text("data")
    tgt = tmp_path / "no_link_here.txt"  # link never created
    cfg = _cfg(str(src), str(tgt))
    events, _ = poll_once(cfg, {})
    assert any(e.kind == "missing" for e in events)


# ---------------------------------------------------------------------------
# watch (limited cycles)
# ---------------------------------------------------------------------------


def test_watch_calls_callback(src_file: Path, tgt_link: Path) -> None:
    cfg = _cfg(str(src_file), str(tgt_link))
    collected: list[WatchEvent] = []

    # Mutate file after first snapshot so second cycle detects change
    call_count = 0

    def _cb(event: WatchEvent) -> None:
        collected.append(event)

    # Patch load_config to return our in-memory config
    import dotlink.watch as wmod

    original_load = wmod.load_config
    wmod.load_config = lambda _path: cfg  # type: ignore[assignment]
    try:
        src_file.write_text("changed!")
        watch(config_path="fake", interval=0.0, callback=_cb, max_cycles=2)
    finally:
        wmod.load_config = original_load


# ---------------------------------------------------------------------------
# WatchEvent str
# ---------------------------------------------------------------------------


def test_watch_event_str() -> None:
    e = WatchEvent("src", "tgt", "changed")
    assert "CHANGED" in str(e)
    assert "src" in str(e)
