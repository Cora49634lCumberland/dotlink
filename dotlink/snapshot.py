"""Snapshot: capture and restore the current state of all managed links."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

from dotlink.links import link_status


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


@dataclass
class Snapshot:
    created_at: float
    links: Dict[str, str]  # target -> source
    labels: List[str] = field(default_factory=list)


def _snapshots_dir(config: dict) -> Path:
    return Path(config["repo_path"]) / ".snapshots"


def take_snapshot(config: dict, label: str = "") -> Snapshot:
    """Record the current link state from config into a snapshot file."""
    links = config.get("links", {})
    snapshot = Snapshot(
        created_at=time.time(),
        links=dict(links),
        labels=[label] if label else [],
    )
    _save_snapshot(config, snapshot)
    return snapshot


def _save_snapshot(config: dict, snapshot: Snapshot) -> Path:
    snapshots_dir = _snapshots_dir(config)
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{int(snapshot.created_at)}.json"
    path = snapshots_dir / filename
    path.write_text(
        json.dumps(
            {
                "created_at": snapshot.created_at,
                "links": snapshot.links,
                "labels": snapshot.labels,
            },
            indent=2,
        )
    )
    return path


def list_snapshots(config: dict) -> List[Snapshot]:
    """Return all saved snapshots sorted oldest-first."""
    snapshots_dir = _snapshots_dir(config)
    if not snapshots_dir.exists():
        return []
    snapshots = []
    for p in sorted(snapshots_dir.glob("*.json")):
        data = json.loads(p.read_text())
        snapshots.append(
            Snapshot(
                created_at=data["created_at"],
                links=data["links"],
                labels=data.get("labels", []),
            )
        )
    return snapshots


def restore_snapshot(config: dict, snapshot: Snapshot) -> Dict[str, str]:
    """Return the link map from the snapshot (caller applies the links)."""
    if not isinstance(snapshot.links, dict):
        raise SnapshotError("Snapshot contains invalid link data.")
    return dict(snapshot.links)
