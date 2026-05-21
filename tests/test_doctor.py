"""Tests for dotlink.doctor."""

from __future__ import annotations

from pathlib import Path

import pytest

from dotlink.doctor import DoctorResult, run_doctor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(links: dict) -> dict:
    return {"repo": "/tmp/repo", "links": links}


# ---------------------------------------------------------------------------
# DoctorResult unit tests
# ---------------------------------------------------------------------------

def test_doctor_result_healthy_when_all_ok():
    r = DoctorResult(ok=["/home/user/.bashrc"])
    assert r.healthy is True


def test_doctor_result_unhealthy_when_broken():
    r = DoctorResult(broken=["/home/user/.vimrc"])
    assert r.healthy is False


def test_doctor_result_summary_contains_labels():
    r = DoctorResult(
        ok=["/a"],
        broken=["/b"],
        missing=["/c"],
        conflict=["/d"],
    )
    summary = r.summary()
    assert "[OK]" in summary
    assert "[BROKEN]" in summary
    assert "[MISSING]" in summary
    assert "[CONFLICT]" in summary
    assert "unhealthy" in summary


def test_doctor_result_summary_healthy_label():
    r = DoctorResult(ok=["/x"])
    assert "healthy" in r.summary()


# ---------------------------------------------------------------------------
# run_doctor integration tests (use real filesystem via tmp_path)
# ---------------------------------------------------------------------------

def test_run_doctor_ok_link(tmp_path: Path):
    source = tmp_path / "source" / "bashrc"
    source.parent.mkdir(parents=True)
    source.write_text("# bashrc")
    target = tmp_path / "target" / ".bashrc"
    target.parent.mkdir(parents=True)
    target.symlink_to(source)

    config = _make_config({str(target): str(source)})
    result = run_doctor(config)

    assert str(target) in result.ok
    assert result.healthy is True


def test_run_doctor_missing_link(tmp_path: Path):
    source = tmp_path / "source" / "vimrc"
    source.parent.mkdir(parents=True)
    source.write_text("set nu")
    target = tmp_path / "target" / ".vimrc"  # symlink never created

    config = _make_config({str(target): str(source)})
    result = run_doctor(config)

    assert str(target) in result.missing
    assert result.healthy is False


def test_run_doctor_broken_link(tmp_path: Path):
    source = tmp_path / "gone" / "tmux.conf"
    target = tmp_path / "target" / ".tmux.conf"
    target.parent.mkdir(parents=True)
    target.symlink_to(source)  # dangling symlink — source does not exist

    config = _make_config({str(target): str(source)})
    result = run_doctor(config)

    assert str(target) in result.broken
    assert result.healthy is False


def test_run_doctor_conflict_link(tmp_path: Path):
    source = tmp_path / "source" / "gitconfig"
    source.parent.mkdir(parents=True)
    source.write_text("[user]")
    target = tmp_path / "target" / ".gitconfig"
    target.parent.mkdir(parents=True)
    target.write_text("# regular file, not a symlink")  # conflict

    config = _make_config({str(target): str(source)})
    result = run_doctor(config)

    assert str(target) in result.conflict
    assert result.healthy is False


def test_run_doctor_empty_links():
    config = _make_config({})
    result = run_doctor(config)
    assert result.healthy is True
    assert result.ok == []
