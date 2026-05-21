"""Tests for dotlink.template."""

from __future__ import annotations

import pytest
from pathlib import Path

from dotlink.template import (
    TemplateError,
    RenderResult,
    default_variables,
    render_template,
    render_all,
    TEMPLATE_SUFFIX,
)


@pytest.fixture()
def tpl_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def test_default_variables_contains_home():
    dvars = default_variables()
    assert "HOME" in dvars
    assert dvars["HOME"] == str(Path.home())


def test_render_template_basic_substitution(tpl_dir: Path):
    src = _write(tpl_dir / f"gitconfig{TEMPLATE_SUFFIX}", "home={{ HOME }}")
    dest = tpl_dir / "gitconfig"
    result = render_template(src, dest)
    assert isinstance(result, RenderResult)
    assert dest.read_text() == f"home={Path.home()}"
    assert "HOME" in result.variables_used


def test_render_template_extra_variables(tpl_dir: Path):
    src = _write(tpl_dir / f"cfg{TEMPLATE_SUFFIX}", "name={{ NAME }}")
    dest = tpl_dir / "cfg"
    render_template(src, dest, variables={"NAME": "alice"})
    assert dest.read_text() == "name=alice"


def test_render_template_unknown_var_kept_by_default(tpl_dir: Path):
    src = _write(tpl_dir / f"cfg{TEMPLATE_SUFFIX}", "x={{ UNKNOWN }}")
    dest = tpl_dir / "cfg"
    result = render_template(src, dest)
    assert "{{ UNKNOWN }}" in dest.read_text()
    assert "UNKNOWN" in result.skipped_vars


def test_render_template_strict_raises_on_unknown(tpl_dir: Path):
    src = _write(tpl_dir / f"cfg{TEMPLATE_SUFFIX}", "x={{ MISSING }}")
    dest = tpl_dir / "cfg"
    with pytest.raises(TemplateError, match="MISSING"):
        render_template(src, dest, strict=True)


def test_render_template_creates_parent_dirs(tpl_dir: Path):
    src = _write(tpl_dir / f"nested/file{TEMPLATE_SUFFIX}", "ok")
    dest = tpl_dir / "out" / "deep" / "file"
    render_template(src, dest)
    assert dest.exists()


def test_render_template_source_missing(tpl_dir: Path):
    with pytest.raises(TemplateError, match="not found"):
        render_template(tpl_dir / "ghost.dtpl", tpl_dir / "out")


def test_render_all_finds_templates(tpl_dir: Path):
    _write(tpl_dir / f"a{TEMPLATE_SUFFIX}", "{{ HOME }}")
    _write(tpl_dir / f"sub/b{TEMPLATE_SUFFIX}", "static")
    results = render_all(tpl_dir)
    assert len(results) == 2
    paths = {r.destination for r in results}
    assert tpl_dir / "a" in paths
    assert tpl_dir / "sub" / "b" in paths


def test_render_all_empty_repo(tpl_dir: Path):
    assert render_all(tpl_dir) == []


def test_render_all_strict_propagates(tpl_dir: Path):
    _write(tpl_dir / f"x{TEMPLATE_SUFFIX}", "{{ NOPE }}")
    with pytest.raises(TemplateError):
        render_all(tpl_dir, strict=True)
