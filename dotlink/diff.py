"""Diff support: compare a tracked dotfile's symlink target against its repo source."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotlink.links import resolve_path, link_status


class DiffError(Exception):
    """Raised when a diff operation cannot be performed."""


@dataclass
class DiffResult:
    source: Path
    target: Path
    status: str          # 'identical', 'differs', 'missing_source', 'missing_target', 'not_symlink'
    unified_diff: Optional[str] = None

    @property
    def has_diff(self) -> bool:
        return self.status == "differs"


def diff_link(source_str: str, target_str: str) -> DiffResult:
    """Return a DiffResult comparing *source* (repo file) to *target* (symlink on disk)."""
    source = resolve_path(source_str)
    target = resolve_path(target_str)

    if not source.exists():
        return DiffResult(source=source, target=target, status="missing_source")

    if not target.exists():
        return DiffResult(source=source, target=target, status="missing_target")

    lst = link_status(source_str, target_str)
    if lst != "ok":
        return DiffResult(source=source, target=target, status="not_symlink")

    # Both exist and target is a valid symlink — compare content
    try:
        result = subprocess.run(
            ["diff", "-u", str(source), str(target)],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        raise DiffError("'diff' utility not found on PATH")

    if result.returncode == 0:
        return DiffResult(source=source, target=target, status="identical")
    elif result.returncode == 1:
        return DiffResult(
            source=source,
            target=target,
            status="differs",
            unified_diff=result.stdout,
        )
    else:
        raise DiffError(f"diff exited with code {result.returncode}: {result.stderr.strip()}")


def diff_all(config: dict) -> list[DiffResult]:
    """Run diff_link for every entry in config['links'] and return all results."""
    results: list[DiffResult] = []
    for entry in config.get("links", []):
        source = entry.get("source", "")
        target = entry.get("target", "")
        if source and target:
            results.append(diff_link(source, target))
    return results
