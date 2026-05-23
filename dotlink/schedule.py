"""Schedule periodic sync operations for dotlink."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from dotlink.config import load_config


class ScheduleError(Exception):
    """Raised when a schedule operation fails."""


@dataclass
class Schedule:
    interval_minutes: int
    enabled: bool = True
    last_run: Optional[str] = None  # ISO-8601 string


def _schedule_path(config: dict) -> Path:
    return Path(config["repo_path"]) / ".dotlink_schedule.json"


def load_schedule(config: dict) -> Optional[Schedule]:
    """Load the current schedule, or None if not configured."""
    path = _schedule_path(config)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return Schedule(
            interval_minutes=data["interval_minutes"],
            enabled=data.get("enabled", True),
            last_run=data.get("last_run"),
        )
    except (KeyError, json.JSONDecodeError) as exc:
        raise ScheduleError(f"Corrupt schedule file: {exc}") from exc


def save_schedule(config: dict, schedule: Schedule) -> None:
    """Persist a schedule to disk."""
    path = _schedule_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(schedule), indent=2))


def set_schedule(config: dict, interval_minutes: int) -> Schedule:
    """Create or update the sync schedule."""
    if interval_minutes < 1:
        raise ScheduleError("interval_minutes must be at least 1")
    existing = load_schedule(config)
    schedule = Schedule(
        interval_minutes=interval_minutes,
        enabled=existing.enabled if existing else True,
        last_run=existing.last_run if existing else None,
    )
    save_schedule(config, schedule)
    return schedule


def disable_schedule(config: dict) -> Schedule:
    """Disable the current schedule without removing it."""
    schedule = load_schedule(config)
    if schedule is None:
        raise ScheduleError("No schedule configured")
    schedule.enabled = False
    save_schedule(config, schedule)
    return schedule


def enable_schedule(config: dict) -> Schedule:
    """Re-enable a previously disabled schedule."""
    schedule = load_schedule(config)
    if schedule is None:
        raise ScheduleError("No schedule configured")
    schedule.enabled = True
    save_schedule(config, schedule)
    return schedule
