"""CLI commands for the dotlink watch feature."""

from __future__ import annotations

import click

from dotlink.config import find_config_path
from dotlink.watch import WatchEvent, poll_once, watch
from dotlink.config import load_config


@click.group("watch")
def watch_cmd() -> None:
    """Watch tracked symlinks for changes."""


@watch_cmd.command("once")
@click.option("--config", "config_path", default=None, help="Path to dotlink config.")
def once_cmd(config_path: str | None) -> None:
    """Run a single check and print any detected changes."""
    path = config_path or find_config_path()
    config = load_config(path)
    events, _ = poll_once(config, {})
    if not events:
        click.echo("All links look healthy.")
    else:
        for event in events:
            click.echo(str(event))


@watch_cmd.command("start")
@click.option("--config", "config_path", default=None, help="Path to dotlink config.")
@click.option(
    "--interval",
    default=2.0,
    show_default=True,
    help="Polling interval in seconds.",
)
def start_cmd(config_path: str | None, interval: float) -> None:
    """Start watching tracked links (press Ctrl+C to stop)."""
    path = config_path or find_config_path()
    click.echo(f"Watching links every {interval}s — press Ctrl+C to stop.")

    def _on_event(event: WatchEvent) -> None:
        click.echo(str(event))

    watch(config_path=path, interval=interval, callback=_on_event)
    click.echo("Watch stopped.")
