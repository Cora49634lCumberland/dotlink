"""CLI commands for dotlink snapshot management."""

from __future__ import annotations

import datetime

import click

from dotlink.config import load_config
from dotlink.snapshot import (
    SnapshotError,
    list_snapshots,
    restore_snapshot,
    take_snapshot,
)


@click.group("snapshot")
def snapshot_cmd():
    """Manage link-state snapshots."""


@snapshot_cmd.command("take")
@click.option("--label", "-l", default="", help="Optional label for the snapshot.")
def take_cmd(label: str):
    """Capture the current link state as a snapshot."""
    try:
        config = load_config()
        snap = take_snapshot(config, label=label)
        ts = datetime.datetime.fromtimestamp(snap.created_at).strftime("%Y-%m-%d %H:%M:%S")
        tag = f" [{label}]" if label else ""
        click.echo(f"Snapshot taken at {ts}{tag} ({len(snap.links)} link(s)).")
    except SnapshotError as exc:
        raise click.ClickException(str(exc)) from exc


@snapshot_cmd.command("list")
def list_cmd():
    """List all saved snapshots."""
    try:
        config = load_config()
        snaps = list_snapshots(config)
        if not snaps:
            click.echo("No snapshots found.")
            return
        for i, snap in enumerate(snaps):
            ts = datetime.datetime.fromtimestamp(snap.created_at).strftime("%Y-%m-%d %H:%M:%S")
            label = ", ".join(snap.labels) if snap.labels else "(no label)"
            click.echo(f"[{i}] {ts}  {label}  ({len(snap.links)} link(s))")
    except SnapshotError as exc:
        raise click.ClickException(str(exc)) from exc


@snapshot_cmd.command("restore")
@click.argument("index", type=int)
def restore_cmd(index: int):
    """Restore links from snapshot INDEX (shown by 'list')."""
    try:
        config = load_config()
        snaps = list_snapshots(config)
        if not snaps:
            raise click.ClickException("No snapshots available.")
        if index < 0 or index >= len(snaps):
            raise click.ClickException(
                f"Index {index} out of range (0-{len(snaps) - 1})."
            )
        snap = snaps[index]
        link_map = restore_snapshot(config, snap)
        config["links"] = link_map
        from dotlink.config import save_config
        save_config(config)
        click.echo(
            f"Restored {len(link_map)} link(s) from snapshot [{index}]. "
            "Run 'dotlink sync' to reapply."
        )
    except SnapshotError as exc:
        raise click.ClickException(str(exc)) from exc
