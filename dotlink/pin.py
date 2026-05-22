"""Pin management: lock a link to a specific file version (by hash)."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

from dotlink.config import load_config


class PinError(Exception):
    """Raised when a pin operation fails."""


@dataclass
class Pin:
    source: str
    sha256: str
    label: str = ""


def _pins_path(config: dict) -> Path:
    return Path(config["repo_path"]) / ".dotlink_pins.json"


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def load_pins(config: dict) -> dict[str, Pin]:
    p = _pins_path(config)
    if not p.exists():
        return {}
    raw = json.loads(p.read_text())
    return {k: Pin(**v) for k, v in raw.items()}


def save_pins(config: dict, pins: dict[str, Pin]) -> None:
    p = _pins_path(config)
    p.write_text(json.dumps({k: asdict(v) for k, v in pins.items()}, indent=2))


def pin_link(config: dict, source: str, label: str = "") -> Pin:
    """Record the current hash of *source* as its pinned version."""
    src = Path(source).expanduser().resolve()
    if not src.exists():
        raise PinError(f"Source file not found: {src}")
    sha = _hash_file(src)
    pins = load_pins(config)
    pins[source] = Pin(source=source, sha256=sha, label=label)
    save_pins(config, pins)
    return pins[source]


def unpin_link(config: dict, source: str) -> None:
    """Remove the pin for *source*."""
    pins = load_pins(config)
    if source not in pins:
        raise PinError(f"No pin found for: {source}")
    del pins[source]
    save_pins(config, pins)


def check_pin(config: dict, source: str) -> Optional[bool]:
    """Return True if file matches pin, False if drifted, None if not pinned."""
    pins = load_pins(config)
    if source not in pins:
        return None
    src = Path(source).expanduser().resolve()
    if not src.exists():
        return False
    return _hash_file(src) == pins[source].sha256
