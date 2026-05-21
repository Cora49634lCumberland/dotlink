"""Health-check utilities for dotlink managed symlinks."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotlink.links import link_status


@dataclass
class DoctorResult:
    """Aggregated results from a health check run."""

    ok: List[str] = field(default_factory=list)
    broken: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)
    conflict: List[str] = field(default_factory=list)

    @property
    def healthy(self) -> bool:
        """Return True only when every tracked link is in good shape."""
        return not (self.broken or self.missing or self.conflict)

    def summary(self) -> str:
        lines: List[str] = []
        for target in self.ok:
            lines.append(f"  [OK]       {target}")
        for target in self.broken:
            lines.append(f"  [BROKEN]   {target}")
        for target in self.missing:
            lines.append(f"  [MISSING]  {target}")
        for target in self.conflict:
            lines.append(f"  [CONFLICT] {target}")
        status = "healthy" if self.healthy else "unhealthy"
        lines.append(f"\nStatus: {status} "
                     f"({len(self.ok)} ok, {len(self.broken)} broken, "
                     f"{len(self.missing)} missing, {len(self.conflict)} conflict)")
        return "\n".join(lines)


def run_doctor(config: dict) -> DoctorResult:
    """Check every link recorded in *config* and categorise its state.

    Parameters
    ----------
    config:
        Loaded dotlink configuration dict (see :func:`dotlink.config.load_config`).

    Returns
    -------
    DoctorResult
        Populated result object with each link placed in the appropriate bucket.
    """
    result = DoctorResult()
    links: dict = config.get("links", {})

    for target_str, source_str in links.items():
        target = Path(target_str).expanduser()
        source = Path(source_str).expanduser()
        status = link_status(source, target)

        if status == "ok":
            result.ok.append(target_str)
        elif status == "broken":
            result.broken.append(target_str)
        elif status == "missing":
            result.missing.append(target_str)
        else:  # "conflict" or anything unexpected
            result.conflict.append(target_str)

    return result
