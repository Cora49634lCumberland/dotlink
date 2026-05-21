"""CLI commands for managing dotlink profiles."""

from __future__ import annotations

import click
from dotlink.config import load_config
from dotlink.profile import (
    ProfileError,
    create_profile,
    delete_profile,
    add_link_to_profile,
    get_profile,
    list_profiles,
)


@click.group("profile")
def profile_cmd():
    """Manage named link profiles."""


@profile_cmd.command("list")
def list_cmd():
    """List all profiles."""
    config = load_config()
    names = list_profiles(config)
    if not names:
        click.echo("No profiles defined.")
    else:
        for name in names:
            click.echo(name)


@profile_cmd.command("create")
@click.argument("name")
def create_cmd(name: str):
    """Create a new empty profile."""
    config = load_config()
    try:
        create_profile(config, name)
        click.echo(f"Profile '{name}' created.")
    except ProfileError as exc:
        raise click.ClickException(str(exc))


@profile_cmd.command("delete")
@click.argument("name")
def delete_cmd(name: str):
    """Delete a profile."""
    config = load_config()
    try:
        delete_profile(config, name)
        click.echo(f"Profile '{name}' deleted.")
    except ProfileError as exc:
        raise click.ClickException(str(exc))


@profile_cmd.command("add")
@click.argument("profile")
@click.argument("source")
@click.argument("target")
def add_cmd(profile: str, source: str, target: str):
    """Add a link entry to a profile."""
    config = load_config()
    try:
        add_link_to_profile(config, profile, source, target)
        click.echo(f"Added link to profile '{profile}'.")
    except ProfileError as exc:
        raise click.ClickException(str(exc))


@profile_cmd.command("show")
@click.argument("name")
def show_cmd(name: str):
    """Show all links in a profile."""
    config = load_config()
    try:
        links = get_profile(config, name)
    except ProfileError as exc:
        raise click.ClickException(str(exc))
    if not links:
        click.echo(f"Profile '{name}' has no links.")
    else:
        for entry in links:
            click.echo(f"  {entry['source']}  ->  {entry['target']}")
