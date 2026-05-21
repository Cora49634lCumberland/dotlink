"""CLI commands for managing dotlink hooks."""

import shutil
import stat
from pathlib import Path

import click

from dotlink.config import load_config
from dotlink.hooks import HOOK_NAMES, HookError, hooks_dir, list_hooks, run_hook


@click.group("hooks")
def hooks_cmd():
    """Manage dotlink lifecycle hooks."""


@hooks_cmd.command("list")
def list_cmd():
    """List all installed hooks."""
    config = load_config()
    installed = list_hooks(config)
    if not installed:
        click.echo("No hooks installed.")
        return
    for name in installed:
        click.echo(f"  {name}")


@hooks_cmd.command("install")
@click.argument("name", type=click.Choice(HOOK_NAMES))
@click.argument("script", type=click.Path(exists=True, dir_okay=False))
def install_cmd(name: str, script: str):
    """Install a hook script for NAME."""
    config = load_config()
    dest = hooks_dir(config) / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(script, dest)
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    click.echo(f"Installed hook '{name}' -> {dest}")


@hooks_cmd.command("remove")
@click.argument("name", type=click.Choice(HOOK_NAMES))
def remove_cmd(name: str):
    """Remove an installed hook."""
    config = load_config()
    target = hooks_dir(config) / name
    if not target.exists():
        click.echo(f"Hook '{name}' is not installed.")
        return
    target.unlink()
    click.echo(f"Removed hook '{name}'.")


@hooks_cmd.command("run")
@click.argument("name", type=click.Choice(HOOK_NAMES))
def run_cmd(name: str):
    """Manually run a hook by NAME."""
    config = load_config()
    try:
        result = run_hook(config, name)
    except HookError as exc:
        raise click.ClickException(str(exc)) from exc

    if result is None:
        click.echo(f"Hook '{name}' is not installed — nothing to run.")
    else:
        if result.stdout:
            click.echo(result.stdout, nl=False)
        click.echo(f"Hook '{name}' completed successfully.")
