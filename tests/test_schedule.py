"""Tests for dotlink.schedule."""
import json
from pathlib import Path

import pytest

from dotlink.schedule import (
    ScheduleError,
    Schedule,
    _schedule_path,
    load_schedule,
    save_schedule,
    set_schedule,
    disable_schedule,
    enable_schedule,
)


@pytest.fixture()
def config(tmp_path):
    return {"repo_path": str(tmp_path)}


def test_schedule_path_uses_repo(config, tmp_path):
    assert _schedule_path(config) == tmp_path / ".dotlink_schedule.json"


def test_load_schedule_returns_none_when_no_file(config):
    assert load_schedule(config) is None


def test_save_and_load_roundtrip(config):
    schedule = Schedule(interval_minutes=30, enabled=True, last_run="2024-01-01T00:00:00")
    save_schedule(config, schedule)
    loaded = load_schedule(config)
    assert loaded.interval_minutes == 30
    assert loaded.enabled is True
    assert loaded.last_run == "2024-01-01T00:00:00"


def test_load_schedule_raises_on_corrupt_file(config, tmp_path):
    path = _schedule_path(config)
    path.write_text("{not valid json")
    with pytest.raises(ScheduleError, match="Corrupt"):
        load_schedule(config)


def test_set_schedule_creates_new(config):
    schedule = set_schedule(config, 15)
    assert schedule.interval_minutes == 15
    assert schedule.enabled is True
    assert schedule.last_run is None


def test_set_schedule_preserves_last_run(config):
    existing = Schedule(interval_minutes=10, enabled=True, last_run="2024-06-01T12:00:00")
    save_schedule(config, existing)
    updated = set_schedule(config, 20)
    assert updated.interval_minutes == 20
    assert updated.last_run == "2024-06-01T12:00:00"


def test_set_schedule_raises_on_invalid_interval(config):
    with pytest.raises(ScheduleError, match="at least 1"):
        set_schedule(config, 0)


def test_disable_schedule(config):
    set_schedule(config, 60)
    schedule = disable_schedule(config)
    assert schedule.enabled is False


def test_disable_schedule_raises_when_none(config):
    with pytest.raises(ScheduleError, match="No schedule"):
        disable_schedule(config)


def test_enable_schedule(config):
    s = Schedule(interval_minutes=5, enabled=False)
    save_schedule(config, s)
    schedule = enable_schedule(config)
    assert schedule.enabled is True


def test_enable_schedule_raises_when_none(config):
    with pytest.raises(ScheduleError, match="No schedule"):
        enable_schedule(config)
