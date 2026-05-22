"""CLI commands for pin management."""

from __future__ import annotations

import click

from dotlink.config import load_config, find_config_path
from dotlink.pin import pin_link, unpin_link, load_pins, check_pin, PinError


@click.group("pin")
def pin_cmd() -> None:
    """Manage pinned file versions."""


@pin_cmd.command("add")
@click.argument("source")
@click.option("--label", default="", help="Optional label for this pin.")
def add_cmd(source: str, label: str) -> None:
    """Pin SOURCE to its current content hash."""
    config = load_config(find_config_path())
    try:
        p = pin_link(config, source, label=label)
        click.echo(f"Pinned {source} @ {p.sha256[:12]}")
    except PinError as exc:
        raise click.ClickException(str(exc))


@pin_cmd.command("remove")
@click.argument("source")
def remove_cmd(source: str) -> None:
    """Remove the pin for SOURCE."""
    config = load_config(find_config_path())
    try:
        unpin_link(config, source)
        click.echo(f"Unpinned {source}")
    except PinError as exc:
        raise click.ClickException(str(exc))


@pin_cmd.command("list")
def list_cmd() -> None:
    """List all pinned files."""
    config = load_config(find_config_path())
    pins = load_pins(config)
    if not pins:
        click.echo("No pins defined.")
        return
    for source, pin in pins.items():
        label = f" ({pin.label})" if pin.label else ""
        click.echo(f"{source}  {pin.sha256[:12]}{label}")


@pin_cmd.command("check")
@click.argument("source")
def check_cmd(source: str) -> None:
    """Check whether SOURCE matches its pinned hash."""
    config = load_config(find_config_path())
    result = check_pin(config, source)
    if result is None:
        click.echo(f"{source}: not pinned")
    elif result:
        click.echo(f"{source}: OK")
    else:
        click.echo(f"{source}: DRIFTED", err=True)
        raise SystemExit(1)
