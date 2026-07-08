"""Tests for Zoya Studio crypto/security system."""

import tempfile
from pathlib import Path

from zoya_studio.security.crypto import CryptoManager, CredentialStore


def test_crypto_encrypt_decrypt():
    """Test encrypt/decrypt round trip."""
    crypto = CryptoManager()
    plaintext = "sk-test-api-key-12345"
    encrypted = crypto.encrypt(plaintext)
    decrypted = crypto.decrypt(encrypted)
    assert decrypted == plaintext
    assert encrypted != plaintext


def test_crypto_unicode():
    """Test crypto with unicode."""
    crypto = CryptoManager()
    plaintext = "Hello, 世界! 🔐"
    encrypted = crypto.encrypt(plaintext)
    decrypted = crypto.decrypt(encrypted)
    assert decrypted == plaintext


def test_crypto_hash_password():
    """Test password hashing."""
    crypto = CryptoManager()
    hash1, salt1 = crypto.hash_password("mypassword")
    hash2, _ = crypto.hash_password("mypassword", salt1)
    assert hash1 == hash2
    assert crypto.verify_password("mypassword", hash1, salt1)
    assert not crypto.verify_password("wrong", hash1, salt1)


def test_credential_store():
    """Test credential store."""
    with tempfile.TemporaryDirectory() as tmp:
        crypto = CryptoManager(str(Path(tmp) / "key.bin"))
        store = CredentialStore(crypto)
        store.store("openai_key", "sk-abc123")
        assert store.retrieve("openai_key") == "sk-abc123"

        keys = store.list_keys()
        assert "openai_key" in keys

        store.delete("openai_key")
        assert store.retrieve("openai_key") is None


def test_credential_store_persist():
    """Test credential store persistence across instances."""
    with tempfile.TemporaryDirectory() as tmp:
        key_file = Path(tmp) / "key.bin"
        store_dir = Path(tmp) / "creds"
        crypto1 = CryptoManager(str(key_file))
        store1 = CredentialStore(crypto1)
        store1.store("test", "secret-value")

        crypto2 = CryptoManager(str(key_file))
        store2 = CredentialStore(crypto2)
        assert store2.retrieve("test") == "secret-value"
