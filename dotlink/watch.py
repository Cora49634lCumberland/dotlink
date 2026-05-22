"""Watch tracked symlink sources for changes and report drift."""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

from dotlink.config import load_config
from dotlink.links import link_status


class WatchError(Exception):
    """Raised when the watcher encounters an unrecoverable error."""


@dataclass
class WatchEvent:
    """Describes a single change detected during a watch cycle."""

    source: str
    target: str
    kind: str  # 'changed' | 'broken' | 'missing'

    def __str__(self) -> str:
        return f"[{self.kind.upper()}] {self.source} -> {self.target}"


def _file_hash(path: Path) -> Optional[str]:
    """Return the SHA-256 hex digest of *path*, or None if unreadable."""
    try:
        data = path.read_bytes()
        return hashlib.sha256(data).hexdigest()
    except OSError:
        return None


def _snapshot_hashes(links: Dict[str, str]) -> Dict[str, Optional[str]]:
    """Return a mapping of source path -> current hash for all tracked links."""
    return {src: _file_hash(Path(src)) for src in links}


def poll_once(
    config: dict,
    previous: Dict[str, Optional[str]],
) -> tuple[List[WatchEvent], Dict[str, Optional[str]]]:
    """Compare current state against *previous* hashes.

    Returns a list of :class:`WatchEvent` objects and the updated hash map.
    """
    links: Dict[str, str] = config.get("links", {})
    current = _snapshot_hashes(links)
    events: List[WatchEvent] = []

    for src, tgt in links.items():
        status = link_status(src, tgt)
        if status == "broken":
            events.append(WatchEvent(src, tgt, "broken"))
        elif status == "missing":
            events.append(WatchEvent(src, tgt, "missing"))
        elif previous and previous.get(src) != current.get(src):
            if previous.get(src) is not None:
                events.append(WatchEvent(src, tgt, "changed"))

    return events, current


def watch(
    config_path: Optional[str] = None,
    interval: float = 2.0,
    callback: Optional[Callable[[WatchEvent], None]] = None,
    max_cycles: Optional[int] = None,
) -> None:
    """Continuously poll tracked links and invoke *callback* on changes.

    Blocks until interrupted (KeyboardInterrupt) or *max_cycles* is reached.
    """
    config = load_config(config_path)
    hashes: Dict[str, Optional[str]] = {}
    cycles = 0

    try:
        while max_cycles is None or cycles < max_cycles:
            events, hashes = poll_once(config, hashes)
            for event in events:
                if callback:
                    callback(event)
            cycles += 1
            if max_cycles is None or cycles < max_cycles:
                time.sleep(interval)
    except KeyboardInterrupt:
        pass
