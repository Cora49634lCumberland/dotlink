"""Pre/post hook support for dotlink operations."""

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class HookError(Exception):
    """Raised when a hook fails."""


@dataclass
class HookResult:
    hook: str
    returncode: int
    stdout: str
    stderr: str

    @property
    def success(self) -> bool:
        return self.returncode == 0


HOOK_NAMES = (
    "pre-link",
    "post-link",
    "pre-unlink",
    "post-unlink",
    "pre-sync",
    "post-sync",
)


def hooks_dir(config: dict) -> Path:
    """Return the hooks directory derived from the repo path in config."""
    repo = Path(config.get("repo_path", "~/.dotfiles")).expanduser()
    return repo / ".dotlink" / "hooks"


def find_hook(config: dict, name: str) -> Optional[Path]:
    """Return the path to a hook script if it exists and is executable."""
    if name not in HOOK_NAMES:
        raise ValueError(f"Unknown hook: {name!r}. Valid hooks: {HOOK_NAMES}")
    candidate = hooks_dir(config) / name
    if candidate.exists() and candidate.stat().st_mode & 0o111:
        return candidate
    return None


def run_hook(config: dict, name: str, cwd: Optional[Path] = None) -> Optional[HookResult]:
    """Run a named hook if it exists. Returns None if the hook is absent."""
    hook_path = find_hook(config, name)
    if hook_path is None:
        return None

    repo = Path(config.get("repo_path", "~/.dotfiles")).expanduser()
    run_cwd = cwd or repo

    result = subprocess.run(
        [str(hook_path)],
        cwd=run_cwd,
        capture_output=True,
        text=True,
    )
    hook_result = HookResult(
        hook=name,
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
    )
    if not hook_result.success:
        raise HookError(
            f"Hook '{name}' exited with code {result.returncode}:\n{result.stderr.strip()}"
        )
    return hook_result


def list_hooks(config: dict) -> List[str]:
    """Return names of all installed hooks."""
    d = hooks_dir(config)
    if not d.exists():
        return []
    return sorted(
        p.name for p in d.iterdir()
        if p.is_file() and p.name in HOOK_NAMES and p.stat().st_mode & 0o111
    )
