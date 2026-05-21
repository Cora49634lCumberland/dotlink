"""Export and import dotlink configurations to/from portable formats."""

import json
import os
from pathlib import Path
from typing import Any

EXPORT_VERSION = 1


class ExportError(Exception):
    """Raised when export or import fails."""


def export_config(config: dict[str, Any], output_path: str | os.PathLike) -> None:
    """Export the current dotlink config and link map to a JSON file.

    Args:
        config: Loaded dotlink config dict (from load_config).
        output_path: Destination file path for the exported JSON.

    Raises:
        ExportError: If the output file cannot be written.
    """
    output_path = Path(output_path)

    payload = {
        "version": EXPORT_VERSION,
        "repo": config.get("repo", ""),
        "links": config.get("links", {}),
    }

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
    except OSError as exc:
        raise ExportError(f"Failed to write export file '{output_path}': {exc}") from exc


def import_config(
    import_path: str | os.PathLike,
    config: dict[str, Any],
    overwrite: bool = False,
) -> dict[str, Any]:
    """Import links from an exported JSON file into an existing config dict.

    Args:
        import_path: Path to the previously exported JSON file.
        config: Existing dotlink config dict to merge links into.
        overwrite: If True, imported links overwrite existing ones with the same target.

    Returns:
        Updated config dict with merged links.

    Raises:
        ExportError: If the file cannot be read or has an incompatible version.
    """
    import_path = Path(import_path)

    try:
        with import_path.open("r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise ExportError(f"Failed to read import file '{import_path}': {exc}") from exc

    version = payload.get("version")
    if version != EXPORT_VERSION:
        raise ExportError(
            f"Incompatible export version: expected {EXPORT_VERSION}, got {version}"
        )

    imported_links: dict[str, str] = payload.get("links", {})
    existing_links: dict[str, str] = config.setdefault("links", {})

    added = 0
    for target, source in imported_links.items():
        if overwrite or target not in existing_links:
            existing_links[target] = source
            added += 1

    return config
