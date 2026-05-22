"""CLI commands for tag management."""

from __future__ import annotations

import click

from dotlink.config import find_config_path, load_config
from dotlink.tag import TagError, add_tag, links_with_tag, remove_tag, tags_for_link


@click.group("tag")
def tag_cmd() -> None:
    """Manage tags on dotfile links."""


@tag_cmd.command("add")
@click.argument("link_name")
@click.argument("tag")
def add_cmd(link_name: str, tag: str) -> None:
    """Add TAG to LINK_NAME."""
    config = load_config(find_config_path())
    try:
        add_tag(config, link_name, tag)
        click.echo(f"Tagged {link_name!r} with {tag!r}.")
    except TagError as exc:
        raise click.ClickException(str(exc)) from exc


@tag_cmd.command("remove")
@click.argument("link_name")
@click.argument("tag")
def remove_cmd(link_name: str, tag: str) -> None:
    """Remove TAG from LINK_NAME."""
    config = load_config(find_config_path())
    try:
        remove_tag(config, link_name, tag)
        click.echo(f"Removed tag {tag!r} from {link_name!r}.")
    except TagError as exc:
        raise click.ClickException(str(exc)) from exc


@tag_cmd.command("list")
@click.argument("link_name")
def list_cmd(link_name: str) -> None:
    """List all tags for LINK_NAME."""
    config = load_config(find_config_path())
    tlist = tags_for_link(config, link_name)
    if tlist:
        for t in tlist:
            click.echo(t)
    else:
        click.echo(f"No tags for {link_name!r}.")


@tag_cmd.command("filter")
@click.argument("tag")
def filter_cmd(tag: str) -> None:
    """List all links that carry TAG."""
    config = load_config(find_config_path())
    names = links_with_tag(config, tag)
    if names:
        for n in names:
            click.echo(n)
    else:
        click.echo(f"No links tagged with {tag!r}.")
