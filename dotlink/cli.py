"""Main CLI entry-point for dotlink."""

from __future__ import annotations

import click

from dotlink.config import find_config_path, load_config, init_config
from dotlink.links import link_status, create_link, remove_link, list_links, LinkError
from dotlink.sync import sync, SyncError
from dotlink.cli_hooks import hooks_cmd
from dotlink.cli_profile import profile_cmd
from dotlink.cli_template import template_cmd
from dotlink.cli_snapshot import snapshot_cmd
from dotlink.cli_ignore import ignore_cmd


@click.group()
def cli() -> None:
    """dotlink — a simple dotfile manager."""


@cli.command()
@click.option("--repo", required=True, help="Path to the dotfiles git repo.")
@click.option("--home", default=None, help="Home directory (defaults to ~).")
def init(repo: str, home: str | None) -> None:
    """Initialise a new dotlink config."""
    try:
        path = init_config(repo_path=repo, home_path=home)
        click.echo(f"Initialised dotlink config at {path}")
    except FileExistsError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@cli.command("add")
@click.argument("source")
@click.argument("target")
def add_link(source: str, target: str) -> None:
    """Create a symlink TARGET -> SOURCE and record it."""
    cfg_path = find_config_path()
    config = load_config(cfg_path)
    try:
        create_link(config, source, target)
        click.echo(f"Linked {target} -> {source}")
    except LinkError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@cli.command("remove")
@click.argument("target")
def remove_link_cmd(target: str) -> None:
    """Remove a recorded symlink."""
    cfg_path = find_config_path()
    config = load_config(cfg_path)
    try:
        remove_link(config, target)
        click.echo(f"Removed link: {target}")
    except LinkError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@cli.command()
def status() -> None:
    """Show the status of all tracked symlinks."""
    cfg_path = find_config_path()
    config = load_config(cfg_path)
    links = list_links(config)
    if not links:
        click.echo("No links tracked.")
        return
    for src, tgt in links.items():
        state = link_status(config, src, tgt)
        click.echo(f"  [{state}] {tgt} -> {src}")


@cli.command()
def sync_cmd() -> None:
    """Pull latest changes and reapply all links."""
    cfg_path = find_config_path()
    config = load_config(cfg_path)
    try:
        sync(config)
        click.echo("Sync complete.")
    except SyncError as exc:
        click.echo(f"Sync failed: {exc}", err=True)
        raise SystemExit(1)


cli.add_command(hooks_cmd)
cli.add_command(profile_cmd)
cli.add_command(template_cmd)
cli.add_command(snapshot_cmd)
cli.add_command(ignore_cmd)
