"""Tests for dotlink.export — export/import of link configurations."""

import json
import pytest

from dotlink.export import export_config, import_config, ExportError, EXPORT_VERSION


@pytest.fixture()
def sample_config():
    return {
        "repo": "/home/user/dotfiles",
        "links": {
            "~/.bashrc": "dotfiles/bashrc",
            "~/.vimrc": "dotfiles/vimrc",
        },
    }


def test_export_creates_file(tmp_path, sample_config):
    out = tmp_path / "export.json"
    export_config(sample_config, out)
    assert out.exists()


def test_export_file_contains_correct_data(tmp_path, sample_config):
    out = tmp_path / "export.json"
    export_config(sample_config, out)
    data = json.loads(out.read_text())
    assert data["version"] == EXPORT_VERSION
    assert data["repo"] == sample_config["repo"]
    assert data["links"] == sample_config["links"]


def test_export_creates_parent_dirs(tmp_path, sample_config):
    out = tmp_path / "nested" / "deep" / "export.json"
    export_config(sample_config, out)
    assert out.exists()


def test_export_raises_on_unwritable_path(sample_config):
    with pytest.raises(ExportError, match="Failed to write"):
        export_config(sample_config, "/no_permission_root_dir/export.json")


def test_import_merges_links(tmp_path, sample_config):
    out = tmp_path / "export.json"
    export_config(sample_config, out)

    existing = {"repo": "", "links": {"~/.zshrc": "dotfiles/zshrc"}}
    updated = import_config(out, existing)

    assert "~/.zshrc" in updated["links"]
    assert "~/.bashrc" in updated["links"]
    assert "~/.vimrc" in updated["links"]


def test_import_does_not_overwrite_by_default(tmp_path, sample_config):
    out = tmp_path / "export.json"
    export_config(sample_config, out)

    existing = {"links": {"~/.bashrc": "OTHER/bashrc"}}
    updated = import_config(out, existing, overwrite=False)
    assert updated["links"]["~/.bashrc"] == "OTHER/bashrc"


def test_import_overwrites_when_flag_set(tmp_path, sample_config):
    out = tmp_path / "export.json"
    export_config(sample_config, out)

    existing = {"links": {"~/.bashrc": "OTHER/bashrc"}}
    updated = import_config(out, existing, overwrite=True)
    assert updated["links"]["~/.bashrc"] == "dotfiles/bashrc"


def test_import_raises_on_missing_file(tmp_path):
    with pytest.raises(ExportError, match="Failed to read"):
        import_config(tmp_path / "nonexistent.json", {})


def test_import_raises_on_bad_json(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not valid json")
    with pytest.raises(ExportError, match="Failed to read"):
        import_config(bad, {})


def test_import_raises_on_wrong_version(tmp_path):
    bad = tmp_path / "wrong_version.json"
    bad.write_text(json.dumps({"version": 99, "links": {}}))
    with pytest.raises(ExportError, match="Incompatible export version"):
        import_config(bad, {})
