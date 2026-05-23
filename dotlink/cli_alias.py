"""CLI commands for managing dotlink aliases."""
import click

from dotlink.alias import AliasError, add_alias, load_aliases, remove_alias, resolve_alias
from dotlink.config import load_config


@click.group(name="alias")
def alias_cmd() -> None:
    """Manage short-name aliases for link targets."""


@alias_cmd.command(name="list")
def list_cmd() -> None:
    """List all registered aliases."""
    config = load_config()
    aliases = load_aliases(config)
    if not aliases:
        click.echo("No aliases defined.")
        return
    for name, target in sorted(aliases.items()):
        click.echo(f"  {name}  ->  {target}")


@alias_cmd.command(name="add")
@click.argument("name")
@click.argument("target")
def add_cmd(name: str, target: str) -> None:
    """Add a new alias NAME pointing to TARGET."""
    config = load_config()
    try:
        add_alias(config, name, target)
        click.echo(f"Alias '{name}' -> '{target}' added.")
    except AliasError as exc:
        raise click.ClickException(str(exc)) from exc


@alias_cmd.command(name="remove")
@click.argument("name")
def remove_cmd(name: str) -> None:
    """Remove alias NAME."""
    config = load_config()
    try:
        remove_alias(config, name)
        click.echo(f"Alias '{name}' removed.")
    except AliasError as exc:
        raise click.ClickException(str(exc)) from exc


@alias_cmd.command(name="resolve")
@click.argument("name")
def resolve_cmd(name: str) -> None:
    """Print the target path for alias NAME."""
    config = load_config()
    try:
        target = resolve_alias(config, name)
        click.echo(target)
    except AliasError as exc:
        raise click.ClickException(str(exc)) from exc
