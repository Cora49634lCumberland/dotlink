"""CLI commands for the audit log."""
from __future__ import annotations

import click
from dotlink.config import load_config, find_config_path
from dotlink.audit import load_entries, clear_log, AuditError


@click.group("audit")
def audit_cmd() -> None:
    """View and manage the dotlink audit log."""


@audit_cmd.command("list")
@click.option("--last", default=0, help="Show only the last N entries (0 = all).")
def list_cmd(last: int) -> None:
    """List recorded audit entries."""
    config = load_config(find_config_path())
    try:
        entries = load_entries(config)
    except AuditError as exc:
        raise click.ClickException(str(exc))

    if not entries:
        click.echo("No audit entries found.")
        return

    shown = entries[-last:] if last > 0 else entries
    for e in shown:
        detail_str = ", ".join(f"{k}={v}" for k, v in e.details.items())
        click.echo(f"[{e.timestamp}] {e.operation}  {detail_str}")


@audit_cmd.command("clear")
@click.confirmation_option(prompt="Clear the entire audit log?")
def clear_cmd() -> None:
    """Delete all audit log entries."""
    config = load_config(find_config_path())
    try:
        count = clear_log(config)
    except AuditError as exc:
        raise click.ClickException(str(exc))
    click.echo(f"Cleared {count} audit entr{'y' if count == 1 else 'ies'}.")
