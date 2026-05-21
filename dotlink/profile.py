"""Profile support: named sets of links for different machines/contexts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

PROFILE_FILE = "profiles.json"


class ProfileError(Exception):
    pass


def _profiles_path(config: dict) -> Path:
    repo = Path(config["repo_path"])
    return repo / PROFILE_FILE


def load_profiles(config: dict) -> Dict[str, List[dict]]:
    """Load all profiles from the repo. Returns a dict of profile_name -> list of link dicts."""
    path = _profiles_path(config)
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise ProfileError(f"Malformed profiles file: {exc}") from exc
    if not isinstance(data, dict):
        raise ProfileError("Profiles file must contain a JSON object.")
    return data


def save_profiles(config: dict, profiles: Dict[str, List[dict]]) -> None:
    """Persist profiles to the repo."""
    path = _profiles_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profiles, indent=2))


def create_profile(config: dict, name: str) -> None:
    """Create an empty profile. Raises ProfileError if it already exists."""
    profiles = load_profiles(config)
    if name in profiles:
        raise ProfileError(f"Profile '{name}' already exists.")
    profiles[name] = []
    save_profiles(config, profiles)


def delete_profile(config: dict, name: str) -> None:
    """Delete a profile. Raises ProfileError if not found."""
    profiles = load_profiles(config)
    if name not in profiles:
        raise ProfileError(f"Profile '{name}' not found.")
    del profiles[name]
    save_profiles(config, profiles)


def add_link_to_profile(config: dict, name: str, source: str, target: str) -> None:
    """Add a link entry to a profile."""
    profiles = load_profiles(config)
    if name not in profiles:
        raise ProfileError(f"Profile '{name}' not found.")
    entry = {"source": source, "target": target}
    if entry in profiles[name]:
        raise ProfileError(f"Link already exists in profile '{name}'.")
    profiles[name].append(entry)
    save_profiles(config, profiles)


def get_profile(config: dict, name: str) -> List[dict]:
    """Return links for a named profile."""
    profiles = load_profiles(config)
    if name not in profiles:
        raise ProfileError(f"Profile '{name}' not found.")
    return profiles[name]


def list_profiles(config: dict) -> List[str]:
    """Return sorted list of profile names."""
    return sorted(load_profiles(config).keys())
