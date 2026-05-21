"""Main CLI entry point for dotlink."""

from __future__ import annotations

from pathlib import Path

import click

from dotlink.config import init_config, load_config, save_config
from dotlink.links import LinkError, create_link, link_status, remove_link
from dotlink.sync import SyncError, sync
from dotlink.cli_hooks import hooks_cmd
from dotlink.cli_profile import profile_cmd
from dotlink.cli_template import template_cmd


@click.group()
def cli() -> None:
    """dotlink — a simple dotfile manager."""


@cli.command()
@click.option("--repo", default="~/dotfiles", show_default=True,
              help="Path to the dotfiles git repository.")
def init(repo: str) -> None:
    """Initialise a new dotlink config."""
    try:
        init_config(repo_path=repo)
        click.echo(f"Initialised dotlink with repo: {repo}")
    except FileExistsError as exc:
        raise click.ClickException(str(exc)) from exc


@cli.command("add")
@click.argument("source")
@click.argument("target")
def add_link(source: str, target: str) -> None:
    """Track a new symlink (SOURCE in repo -> TARGET on disk)."""
    cfg = load_config()
    try:
        create_link(Path(source), Path(target))
    except LinkError as exc:
        raise click.ClickException(str(exc)) from exc
    cfg["links"][source] = target
    save_config(cfg)
    click.echo(f"Linked {source} -> {target}")


@cli.command("remove")
@click.argument("target")
def remove_link_cmd(target: str) -> None:
    """Remove a tracked symlink."""
    cfg = load_config()
    try:
        remove_link(Path(target))
    except LinkError as exc:
        raise click.ClickException(str(exc)) from exc
    cfg["links"] = {s: t for s, t in cfg["links"].items() if t != target}
    save_config(cfg)
    click.echo(f"Removed link: {target}")


@cli.command()
def status() -> None:
    """Show the status of all tracked symlinks."""
    cfg = load_config()
    links = cfg.get("links", {})
    if not links:
        click.echo("No links tracked.")
        return
    for source, target in links.items():
        state = link_status(Path(source), Path(target))
        click.echo(f"  [{state}] {target} -> {source}")


@cli.command("sync")
def sync_cmd() -> None:
    """Pull latest changes and reapply all symlinks."""
    cfg = load_config()
    try:
        sync(cfg)
        click.echo("Sync complete.")
    except SyncError as exc:
        raise click.ClickException(str(exc)) from exc


cli.add_command(hooks_cmd)
cli.add_command(profile_cmd)
cli.add_command(template_cmd)
