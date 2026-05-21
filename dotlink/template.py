"""Template rendering for dotfiles with variable substitution."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

TEMPLATE_SUFFIX = ".dtpl"
_VAR_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


class TemplateError(Exception):
    """Raised when template rendering fails."""


@dataclass
class RenderResult:
    source: Path
    destination: Path
    variables_used: list[str] = field(default_factory=list)
    skipped_vars: list[str] = field(default_factory=list)


def default_variables() -> Dict[str, str]:
    """Return a dict of built-in variables available to all templates."""
    return {
        "HOME": str(Path.home()),
        "USER": os.environ.get("USER", os.environ.get("USERNAME", "")),
        "HOSTNAME": os.uname().nodename if hasattr(os, "uname") else "",
    }


def render_template(
    source: Path,
    destination: Path,
    variables: Optional[Dict[str, str]] = None,
    *,
    strict: bool = False,
) -> RenderResult:
    """Render *source* template into *destination*, substituting {{ VAR }} tokens.

    Args:
        source: Path to the ``.dtpl`` template file.
        destination: Path where the rendered file will be written.
        variables: Extra variables to merge with the built-ins.
        strict: If True, raise TemplateError for any unresolved variable.
    """
    if not source.exists():
        raise TemplateError(f"Template source not found: {source}")

    all_vars = default_variables()
    if variables:
        all_vars.update(variables)

    text = source.read_text(encoding="utf-8")
    used: list[str] = []
    skipped: list[str] = []

    def replacer(match: re.Match) -> str:
        key = match.group(1)
        if key in all_vars:
            used.append(key)
            return all_vars[key]
        if strict:
            raise TemplateError(f"Unresolved template variable: {{{{{key}}}}}")
        skipped.append(key)
        return match.group(0)

    rendered = _VAR_RE.sub(replacer, text)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(rendered, encoding="utf-8")

    return RenderResult(source=source, destination=destination,
                        variables_used=used, skipped_vars=skipped)


def render_all(
    repo_path: Path,
    variables: Optional[Dict[str, str]] = None,
    *,
    strict: bool = False,
) -> list[RenderResult]:
    """Find and render every ``*.dtpl`` file under *repo_path*."""
    results: list[RenderResult] = []
    for tpl in sorted(repo_path.rglob(f"*{TEMPLATE_SUFFIX}")):
        dest = tpl.with_suffix("")  # strip .dtpl
        results.append(render_template(tpl, dest, variables, strict=strict))
    return results
