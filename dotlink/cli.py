"""Command-line interface for dotlink."""

from __future__ import annotations

import click

from dotlink.config import init_config, load_config, save_config
from dotlink.links import LinkError, create_link, link_status, remove_link
from dotlink.sync import SyncError, sync


@click.group()
def cli() -> None:
    """dotlink — a simple dotfile manager."""


@cli.command("add")
@click.argument("source")
@click.argument("target")
@click.option("--overwrite", is_flag=True, default=False, help="Replace existing target.")
def add_link(source: str, target: str, overwrite: bool) -> None:
    """Track SOURCE as a symlink at TARGET."""
    try:
        create_link(source, target, overwrite=overwrite)
    except LinkError as exc:
        raise click.ClickException(str(exc)) from exc

    config = load_config()
    entry = {"source": source, "target": target}
    if entry not in config.setdefault("links", []):
        config["links"].append(entry)
        save_config(config)
    click.echo(f"Linked {source} -> {target}")


@cli.command("remove")
@click.argument("target")
def remove_link_cmd(target: str) -> None:
    """Remove the symlink at TARGET and stop tracking it."""
    try:
        remove_link(target)
    except LinkError as exc:
        raise click.ClickException(str(exc)) from exc

    config = load_config()
    config["links"] = [
        e for e in config.get("links", []) if e.get("target") != target
    ]
    save_config(config)
    click.echo(f"Removed link {target}")


@cli.command("status")
def status() -> None:
    """Show the status of all tracked symlinks."""
    config = load_config()
    links = config.get("links", [])
    if not links:
        click.echo("No links tracked.")
        return
    for entry in links:
        src = entry.get("source", "?")
        tgt = entry.get("target", "?")
        state = link_status(src, tgt)
        symbol = {"ok": "✔", "missing": "✘", "conflict": "!", "broken": "~"}.get(state, "?")
        click.echo(f"  {symbol} {tgt} -> {src}  [{state}]")


@cli.command("sync")
def sync_cmd() -> None:
    """Pull the git repo and reapply all tracked symlinks."""
    try:
        result = sync()
    except SyncError as exc:
        raise click.ClickException(str(exc)) from exc

    click.echo(f"git pull: {result['pull_output'] or 'no output'}")
    for tgt in result["ok"]:
        click.echo(f"  ✔ {tgt}")
    for tgt, msg in result["errors"]:
        click.echo(f"  ✘ {tgt}: {msg}", err=True)
    if result["errors"]:
        raise click.ClickException("Some links could not be applied.")


@cli.command("init")
@click.option("--repo", default="~/dotfiles", show_default=True, help="Path to the dotfiles git repo.")
def init(repo: str) -> None:
    """Initialise a new dotlink config file."""
    try:
        path = init_config(repo_path=repo)
        click.echo(f"Initialised dotlink config at {path}")
    except FileExistsError as exc:
        raise click.ClickException(str(exc)) from exc
