"""CLI commands for managing dotlink ignore patterns."""

from __future__ import annotations

import click

from dotlink.config import load_config, find_config_path
from dotlink.ignore import (
    IgnoreError,
    is_ignored,
    load_patterns,
    add_pattern,
    remove_pattern,
    DEFAULT_PATTERNS,
)


@click.group("ignore")
def ignore_cmd() -> None:
    """Manage ignore patterns (.dotignore)."""


@ignore_cmd.command("list")
def list_cmd() -> None:
    """List all active ignore patterns."""
    cfg_path = find_config_path()
    config = load_config(cfg_path)
    patterns = load_patterns(config)
    if not patterns:
        click.echo("No ignore patterns defined.")
        return
    for p in patterns:
        marker = "  [default]" if p in DEFAULT_PATTERNS else ""
        click.echo(f"  {p}{marker}")


@ignore_cmd.command("add")
@click.argument("pattern")
def add_cmd(pattern: str) -> None:
    """Add a glob PATTERN to .dotignore."""
    cfg_path = find_config_path()
    config = load_config(cfg_path)
    try:
        add_pattern(config, pattern)
        click.echo(f"Added ignore pattern: {pattern}")
    except IgnoreError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@ignore_cmd.command("remove")
@click.argument("pattern")
def remove_cmd(pattern: str) -> None:
    """Remove a glob PATTERN from .dotignore."""
    cfg_path = find_config_path()
    config = load_config(cfg_path)
    try:
        remove_pattern(config, pattern)
        click.echo(f"Removed ignore pattern: {pattern}")
    except IgnoreError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@ignore_cmd.command("check")
@click.argument("names", nargs=-1, required=True)
def check_cmd(names: tuple[str, ...]) -> None:
    """Check whether one or more NAMEs would be ignored."""
    cfg_path = find_config_path()
    config = load_config(cfg_path)
    patterns = load_patterns(config)
    for name in names:
        if is_ignored(name, patterns):
            click.echo(f"{name} is IGNORED")
        else:
            click.echo(f"{name} is NOT ignored")
