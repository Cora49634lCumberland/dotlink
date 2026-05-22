"""Main CLI entry-point for dotlink."""
from __future__ import annotations

import click
from dotlink.config import find_config_path, load_config, init_config
from dotlink.links import create_link, remove_link, link_status, list_links
from dotlink.sync import sync
from dotlink.cli_hooks import hooks_cmd
from dotlink.cli_profile import profile_cmd
from dotlink.cli_template import template_cmd
from dotlink.cli_snapshot import snapshot_cmd
from dotlink.cli_ignore import ignore_cmd
from dotlink.cli_pin import pin_cmd
from dotlink.cli_tag import tag_cmd
from dotlink.cli_audit import audit_cmd
from dotlink.audit import record


@click.group()
def cli() -> None:
    """dotlink — dotfile manager."""


@cli.command()
@click.argument("repo_path")
def init(repo_path: str) -> None:
    """Initialise a new dotlink config."""
    cfg = init_config(repo_path)
    click.echo(f"Initialised dotlink repo at {cfg['repo_path']}")


@cli.command("add")
@click.argument("source")
@click.argument("target")
def add_link(source: str, target: str) -> None:
    """Track and create a symlink SOURCE -> TARGET."""
    config = load_config(find_config_path())
    create_link(source, target)
    config.setdefault("links", {})[source] = target
    from dotlink.config import save_config
    save_config(config, find_config_path())
    record(config, "link_added", source=source, target=target)
    click.echo(f"Linked {source} -> {target}")


@cli.command("remove")
@click.argument("source")
def remove_link_cmd(source: str) -> None:
    """Remove a tracked symlink."""
    config = load_config(find_config_path())
    target = config.get("links", {}).pop(source, None)
    if target is None:
        raise click.ClickException(f"{source} is not tracked")
    remove_link(source)
    from dotlink.config import save_config
    save_config(config, find_config_path())
    record(config, "link_removed", source=source, target=target)
    click.echo(f"Removed link {source}")


@cli.command()
def status() -> None:
    """Show status of all tracked links."""
    config = load_config(find_config_path())
    links = list_links(config)
    if not links:
        click.echo("No links tracked.")
        return
    for src, tgt in links:
        st = link_status(src, tgt)
        click.echo(f"{st:10s} {src} -> {tgt}")


@cli.command()
def sync_cmd() -> None:
    """Pull latest changes and reapply links."""
    config = load_config(find_config_path())
    sync(config)
    record(config, "sync")
    click.echo("Sync complete.")


cli.add_command(hooks_cmd)
cli.add_command(profile_cmd)
cli.add_command(template_cmd)
cli.add_command(snapshot_cmd)
cli.add_command(ignore_cmd)
cli.add_command(pin_cmd)
cli.add_command(tag_cmd)
cli.add_command(audit_cmd)
