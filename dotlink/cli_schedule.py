"""CLI commands for managing the dotlink sync schedule."""
import click

from dotlink.config import load_config, find_config_path
from dotlink.schedule import (
    ScheduleError,
    load_schedule,
    set_schedule,
    disable_schedule,
    enable_schedule,
)


@click.group("schedule")
def schedule_cmd():
    """Manage periodic sync schedule."""


@schedule_cmd.command("show")
def show_cmd():
    """Show the current schedule."""
    config = load_config(find_config_path())
    schedule = load_schedule(config)
    if schedule is None:
        click.echo("No schedule configured.")
        return
    status = "enabled" if schedule.enabled else "disabled"
    click.echo(f"Interval : {schedule.interval_minutes} minute(s)")
    click.echo(f"Status   : {status}")
    click.echo(f"Last run : {schedule.last_run or 'never'}")


@schedule_cmd.command("set")
@click.argument("interval", type=int)
def set_cmd(interval: int):
    """Set sync interval in minutes."""
    config = load_config(find_config_path())
    try:
        schedule = set_schedule(config, interval)
        click.echo(f"Schedule set: every {schedule.interval_minutes} minute(s).")
    except ScheduleError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@schedule_cmd.command("enable")
def enable_cmd():
    """Enable the current schedule."""
    config = load_config(find_config_path())
    try:
        enable_schedule(config)
        click.echo("Schedule enabled.")
    except ScheduleError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)


@schedule_cmd.command("disable")
def disable_cmd():
    """Disable the current schedule."""
    config = load_config(find_config_path())
    try:
        disable_schedule(config)
        click.echo("Schedule disabled.")
    except ScheduleError as exc:
        click.echo(f"Error: {exc}", err=True)
        raise SystemExit(1)
