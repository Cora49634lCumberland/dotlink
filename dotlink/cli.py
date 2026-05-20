"""Command-line interface for dotlink link management commands."""

import sys
import click

from dotlink.config import find_config_path, load_config, save_config
from dotlink.links import create_link, remove_link, list_links, LinkError


@click.group()
def cli():
    """dotlink — a simple dotfile symlink manager."""
    pass


@cli.command("add")
@click.argument("source")
@click.argument("target")
@click.option("--overwrite", is_flag=True, default=False, help="Overwrite existing target.")
def add_link(source: str, target: str, overwrite: bool):
    """Track and create a symlink from TARGET -> SOURCE."""
    config_path = find_config_path()
    config = load_config(config_path)

    try:
        create_link(source, target, overwrite=overwrite)
    except LinkError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    config.setdefault("links", {})[source] = target
    save_config(config_path, config)
    click.echo(f"Linked: {target} -> {source}")


@cli.command("remove")
@click.argument("source")
def remove_link_cmd(source: str):
    """Remove the symlink for SOURCE and stop tracking it."""
    config_path = find_config_path()
    config = load_config(config_path)
    links = config.get("links", {})

    if source not in links:
        click.echo(f"Error: '{source}' is not tracked.", err=True)
        sys.exit(1)

    target = links[source]
    try:
        remove_link(target)
    except LinkError as exc:
        click.echo(f"Warning: {exc}", err=True)

    del links[source]
    save_config(config_path, config)
    click.echo(f"Removed link: {target}")


@cli.command("status")
def status():
    """Show the status of all tracked symlinks."""
    config_path = find_config_path()
    config = load_config(config_path)
    links = config.get("links", {})

    if not links:
        click.echo("No links tracked.")
        return

    statuses = list_links(links)
    for entry in statuses:
        symbol = {
            "linked": click.style("✔", fg="green"),
            "not_linked": click.style("✘", fg="yellow"),
            "missing_source": click.style("!", fg="red"),
            "conflict": click.style("~", fg="magenta"),
        }.get(entry["status"], "?")
        click.echo(f"  {symbol}  {entry['target']} -> {entry['source']}  [{entry['status']}]")


if __name__ == "__main__":
    cli()
