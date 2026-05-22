"""Audit log: records dotlink operations for traceability."""
from __future__ import annotations

import json
import datetime
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any


class AuditError(Exception):
    """Raised when audit log operations fail."""


@dataclass
class AuditEntry:
    timestamp: str
    operation: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "AuditEntry":
        return AuditEntry(
            timestamp=data["timestamp"],
            operation=data["operation"],
            details=data.get("details", {}),
        )


def _audit_path(config: Dict[str, Any]) -> Path:
    return Path(config["repo_path"]) / ".dotlink_audit.json"


def load_entries(config: Dict[str, Any]) -> List[AuditEntry]:
    path = _audit_path(config)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return [AuditEntry.from_dict(e) for e in data]
    except (json.JSONDecodeError, KeyError) as exc:
        raise AuditError(f"Corrupt audit log: {exc}") from exc


def _save_entries(config: Dict[str, Any], entries: List[AuditEntry]) -> None:
    path = _audit_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([e.to_dict() for e in entries], indent=2))


def record(config: Dict[str, Any], operation: str, **details: Any) -> AuditEntry:
    """Append a new audit entry and return it."""
    entries = load_entries(config)
    entry = AuditEntry(
        timestamp=datetime.datetime.utcnow().isoformat(),
        operation=operation,
        details=details,
    )
    entries.append(entry)
    _save_entries(config, entries)
    return entry


def clear_log(config: Dict[str, Any]) -> int:
    """Remove all audit entries. Returns count of removed entries."""
    entries = load_entries(config)
    count = len(entries)
    _save_entries(config, [])
    return count
