"""Tests for dotlink.audit."""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from dotlink.audit import (
    AuditEntry,
    AuditError,
    _audit_path,
    load_entries,
    record,
    clear_log,
)


@pytest.fixture()
def config(tmp_path: Path):
    return {"repo_path": str(tmp_path)}


def test_audit_path_uses_repo(config, tmp_path):
    assert _audit_path(config) == tmp_path / ".dotlink_audit.json"


def test_load_entries_empty_when_no_file(config):
    assert load_entries(config) == []


def test_record_creates_entry(config):
    entry = record(config, "link_added", source="a", target="b")
    assert entry.operation == "link_added"
    assert entry.details["source"] == "a"
    assert entry.details["target"] == "b"
    assert entry.timestamp  # non-empty


def test_record_persists_to_disk(config, tmp_path):
    record(config, "link_removed", source="x")
    path = tmp_path / ".dotlink_audit.json"
    assert path.exists()
    data = json.loads(path.read_text())
    assert len(data) == 1
    assert data[0]["operation"] == "link_removed"


def test_multiple_records_accumulate(config):
    record(config, "op_a")
    record(config, "op_b")
    entries = load_entries(config)
    assert len(entries) == 2
    assert entries[0].operation == "op_a"
    assert entries[1].operation == "op_b"


def test_clear_log_removes_all_entries(config):
    record(config, "op_a")
    record(config, "op_b")
    count = clear_log(config)
    assert count == 2
    assert load_entries(config) == []


def test_clear_log_returns_zero_when_empty(config):
    assert clear_log(config) == 0


def test_load_entries_raises_on_corrupt_file(config, tmp_path):
    path = tmp_path / ".dotlink_audit.json"
    path.write_text("not valid json")
    with pytest.raises(AuditError):
        load_entries(config)


def test_audit_entry_roundtrip():
    entry = AuditEntry(timestamp="2024-01-01T00:00:00", operation="test", details={"k": "v"})
    assert AuditEntry.from_dict(entry.to_dict()) == entry
