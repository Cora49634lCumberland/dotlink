"""Tests for dotlink.encrypt."""

from __future__ import annotations

import pytest
from pathlib import Path

from dotlink.encrypt import (
    EncryptError,
    EncryptResult,
    _key_path,
    _derive_key,
    _xor_bytes,
    save_passphrase,
    verify_passphrase,
    encrypt_file,
    decrypt_file,
)


@pytest.fixture()
def config(tmp_path: Path) -> dict:
    repo = tmp_path / "repo"
    repo.mkdir()
    return {"repo_path": str(repo)}


@pytest.fixture()
def src_file(tmp_path: Path) -> Path:
    f = tmp_path / "secret.txt"
    f.write_text("my secret config value")
    return f


def test_key_path_uses_repo(config: dict) -> None:
    kp = _key_path(config)
    assert kp.parent == Path(config["repo_path"])
    assert kp.name == ".dotlink_key"


def test_derive_key_returns_32_bytes() -> None:
    key = _derive_key("hunter2")
    assert isinstance(key, bytes)
    assert len(key) == 32


def test_xor_bytes_roundtrip() -> None:
    key = _derive_key("testpass")
    original = b"hello world"
    assert _xor_bytes(_xor_bytes(original, key), key) == original


def test_save_passphrase_creates_key_file(config: dict) -> None:
    save_passphrase(config, "mypassword")
    kp = _key_path(config)
    assert kp.exists()
    assert len(kp.read_text().strip()) == 64  # sha256 hex digest


def test_verify_passphrase_correct(config: dict) -> None:
    save_passphrase(config, "correct")
    assert verify_passphrase(config, "correct") is True


def test_verify_passphrase_wrong(config: dict) -> None:
    save_passphrase(config, "correct")
    assert verify_passphrase(config, "wrong") is False


def test_verify_passphrase_no_file(config: dict) -> None:
    assert verify_passphrase(config, "anything") is False


def test_encrypt_file_creates_dest(src_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "encrypted" / "secret.enc"
    result = encrypt_file(src_file, dest, "pass")
    assert dest.exists()
    assert isinstance(result, EncryptResult)
    assert result.encrypted is True


def test_encrypt_file_content_differs(src_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "secret.enc"
    encrypt_file(src_file, dest, "pass")
    assert dest.read_bytes() != src_file.read_bytes()


def test_decrypt_file_roundtrip(src_file: Path, tmp_path: Path) -> None:
    enc = tmp_path / "secret.enc"
    dec = tmp_path / "secret.dec"
    encrypt_file(src_file, enc, "mypass")
    result = decrypt_file(enc, dec, "mypass")
    assert dec.read_text() == "my secret config value"
    assert result.encrypted is False


def test_encrypt_raises_if_source_missing(tmp_path: Path) -> None:
    with pytest.raises(EncryptError, match="Source file not found"):
        encrypt_file(tmp_path / "ghost.txt", tmp_path / "out.enc", "pass")


def test_decrypt_raises_if_source_missing(tmp_path: Path) -> None:
    with pytest.raises(EncryptError, match="Encrypted file not found"):
        decrypt_file(tmp_path / "ghost.enc", tmp_path / "out.txt", "pass")
