"""Tag management for dotlink — assign tags to links and filter by them."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from dotlink.config import load_config


class TagError(Exception):
    """Raised when a tag operation fails."""


def _tags_path(config: dict) -> Path:
    return Path(config["repo_path"]) / ".dotlink_tags.json"


def load_tags(config: dict) -> Dict[str, List[str]]:
    """Return mapping of link_name -> list[tag]. Empty dict if file absent."""
    path = _tags_path(config)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise TagError(f"Corrupt tags file: {exc}") from exc


def save_tags(config: dict, tags: Dict[str, List[str]]) -> None:
    path = _tags_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tags, indent=2))


def add_tag(config: dict, link_name: str, tag: str) -> Dict[str, List[str]]:
    """Add *tag* to *link_name*. Raises TagError if link not in config."""
    cfg = load_config(config.get("_path", "")) if "links" not in config else config
    if link_name not in cfg.get("links", {}):
        raise TagError(f"Unknown link: {link_name!r}")
    tags = load_tags(config)
    entry = tags.setdefault(link_name, [])
    if tag not in entry:
        entry.append(tag)
    save_tags(config, tags)
    return tags


def remove_tag(config: dict, link_name: str, tag: str) -> Dict[str, List[str]]:
    """Remove *tag* from *link_name*. Raises TagError if tag not present."""
    tags = load_tags(config)
    if tag not in tags.get(link_name, []):
        raise TagError(f"Tag {tag!r} not found on {link_name!r}")
    tags[link_name].remove(tag)
    if not tags[link_name]:
        del tags[link_name]
    save_tags(config, tags)
    return tags


def links_with_tag(config: dict, tag: str) -> List[str]:
    """Return list of link names that carry *tag*."""
    tags = load_tags(config)
    return [name for name, tlist in tags.items() if tag in tlist]


def tags_for_link(config: dict, link_name: str) -> List[str]:
    """Return all tags assigned to *link_name*."""
    return load_tags(config).get(link_name, [])
