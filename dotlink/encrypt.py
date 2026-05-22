"""Optional encryption support for sensitive dotfiles using symmetric key."""

from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class EncryptError(Exception):
    """Raised when encryption or decryption fails."""


@dataclass
class EncryptResult:
    path: Path
    encrypted: bool
    message: str


def _key_path(config: dict) -> Path:
    repo = Path(config["repo_path"])
    return repo / ".dotlink_key"


def _derive_key(passphrase: str) -> bytes:
    """Derive a 32-byte key from a passphrase using SHA-256."""
    return hashlib.sha256(passphrase.encode()).digest()


def _xor_bytes(data: bytes, key: bytes) -> bytes:
    """Simple XOR cipher (repeating key)."""
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))


def save_passphrase(config: dict, passphrase: str) -> None:
    """Store a hashed passphrase hint in the repo (not the raw key)."""
    key_file = _key_path(config)
    digest = hashlib.sha256(passphrase.encode()).hexdigest()
    key_file.write_text(digest)


def verify_passphrase(config: dict, passphrase: str) -> bool:
    """Return True if passphrase matches the stored digest."""
    key_file = _key_path(config)
    if not key_file.exists():
        return False
    stored = key_file.read_text().strip()
    return stored == hashlib.sha256(passphrase.encode()).hexdigest()


def encrypt_file(src: Path, dest: Path, passphrase: str) -> EncryptResult:
    """Encrypt *src* into *dest* using XOR + base64 encoding."""
    if not src.exists():
        raise EncryptError(f"Source file not found: {src}")
    key = _derive_key(passphrase)
    raw = src.read_bytes()
    encrypted = base64.b64encode(_xor_bytes(raw, key))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(encrypted)
    return EncryptResult(path=dest, encrypted=True, message="encrypted")


def decrypt_file(src: Path, dest: Path, passphrase: str) -> EncryptResult:
    """Decrypt *src* (created by encrypt_file) into *dest*."""
    if not src.exists():
        raise EncryptError(f"Encrypted file not found: {src}")
    key = _derive_key(passphrase)
    try:
        raw = base64.b64decode(src.read_bytes())
    except Exception as exc:
        raise EncryptError(f"Failed to decode file: {exc}") from exc
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(_xor_bytes(raw, key))
    return EncryptResult(path=dest, encrypted=False, message="decrypted")
