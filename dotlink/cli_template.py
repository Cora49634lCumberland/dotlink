"""CLI commands for template rendering (dotlink template ...)."""

from __future__ import annotations

from pathlib import Path

import click

from dotlink.config import load_config
from dotlink.template import TemplateError, render_all, render_template, TEMPLATE_SUFFIX


@click.group("template")
def template_cmd() -> None:
    """Manage and render dotfile templates."""


@template_cmd.command("render")
@click.argument("template_file", required=False)
@click.option("--var", "-v", multiple=True, metavar="KEY=VALUE",
              help="Extra variable (repeatable).")
@click.option("--strict", is_flag=True, default=False,
              help="Fail on unresolved variables.")
@click.pass_context
def render_cmd(ctx: click.Context, template_file: str | None,
              var: tuple[str, ...], strict: bool) -> None:
    """Render one template file, or all templates in the repo."""
    cfg = load_config()
    repo_path = Path(cfg["repo_path"]).expanduser()

    extra: dict[str, str] = {}
    for item in var:
        if "=" not in item:
            raise click.BadParameter(f"Expected KEY=VALUE, got: {item!r}",
                                     param_hint="--var")
        k, _, v = item.partition("=")
        extra[k.strip()] = v.strip()

    try:
        if template_file:
            src = Path(template_file).expanduser()
            if not src.suffix == TEMPLATE_SUFFIX:
                click.echo(f"Warning: {src.name} does not end with {TEMPLATE_SUFFIX}",
                           err=True)
            dest = src.with_suffix("")
            result = render_template(src, dest, extra, strict=strict)
            click.echo(f"Rendered {result.source.name} -> {result.destination}")
        else:
            results = render_all(repo_path, extra, strict=strict)
            if not results:
                click.echo("No templates found.")
            for r in results:
                click.echo(f"  {r.source.name} -> {r.destination}")
    except TemplateError as exc:
        raise click.ClickException(str(exc)) from exc


@template_cmd.command("list")
@click.pass_context
def list_cmd(ctx: click.Context) -> None:
    """List all template files in the repo."""
    cfg = load_config()
    repo_path = Path(cfg["repo_path"]).expanduser()
    templates = sorted(repo_path.rglob(f"*{TEMPLATE_SUFFIX}"))
    if not templates:
        click.echo("No templates found.")
        return
    for tpl in templates:
        click.echo(f"  {tpl.relative_to(repo_path)}")
