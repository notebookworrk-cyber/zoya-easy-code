"""Secure credential storage and encryption for Zoya Studio."""

from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path
from typing import Any

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


class CryptoManager:
    """Manages encryption of credentials."""

    def __init__(self, key_file: str | None = None):
        self.key_dir = Path.home() / ".zoya" / "studio" / "secure"
        self.key_dir.mkdir(parents=True, exist_ok=True)
        self.key_file = Path(key_file) if key_file else self.key_dir / "key.bin"
        self._fernet = self._load_or_create_key()

    def _load_or_create_key(self) -> Any | None:
        """Load or create encryption key."""
        if not CRYPTO_AVAILABLE:
            return None

        if self.key_file.exists():
            key = self.key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            os.chmod(self.key_file, 0o600)

        return Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string."""
        if not self._fernet:
            # Fallback: base64 (not secure but functional)
            return base64.b64encode(plaintext.encode()).decode()

        token = self._fernet.encrypt(plaintext.encode())
        return base64.b64encode(token).decode()

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt a string."""
        if not self._fernet:
            try:
                return base64.b64decode(ciphertext.encode()).decode()
            except Exception:
                return ciphertext

        try:
            token = base64.b64decode(ciphertext.encode())
            return self._fernet.decrypt(token).decode()
        except Exception:
            return ciphertext

    @staticmethod
    def hash_password(password: str, salt: bytes | None = None) -> tuple[str, bytes]:
        """Hash a password with salt."""
        if salt is None:
            salt = os.urandom(16)

        if CRYPTO_AVAILABLE:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = kdf.derive(password.encode())
            return base64.b64encode(key).decode(), salt
        else:
            h = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
            return base64.b64encode(h).decode(), salt

    @staticmethod
    def verify_password(password: str, stored_hash: str, salt: bytes) -> bool:
        """Verify a password against stored hash."""
        computed, _ = CryptoManager.hash_password(password, salt)
        return computed == stored_hash

    def secure_delete(self, path: str) -> None:
        """Securely delete a file."""
        p = Path(path)
        if p.exists():
            size = p.stat().st_size
            with open(p, "ba+", buffering=0) as f:
                for _ in range(3):
                    f.seek(0)
                    f.write(os.urandom(size))
            p.unlink()


class CredentialStore:
    """Secure credential storage."""

    def __init__(self, crypto: CryptoManager | None = None):
        self.crypto = crypto or CryptoManager()
        self.store_dir = Path.home() / ".zoya" / "studio" / "credentials"
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, str] = {}

    def store(self, key: str, value: str) -> None:
        """Store an encrypted credential."""
        encrypted = self.crypto.encrypt(value)
        safe_key = base64.b64encode(key.encode()).decode().replace("/", "_").replace("+", "-")
        path = self.store_dir / f"{safe_key}.enc"
        path.write_text(encrypted)
        os.chmod(path, 0o600)
        self._cache[key] = value

    def retrieve(self, key: str) -> str | None:
        """Retrieve a decrypted credential."""
        if key in self._cache:
            return self._cache[key]

        safe_key = base64.b64encode(key.encode()).decode().replace("/", "_").replace("+", "-")
        path = self.store_dir / f"{safe_key}.enc"
        if path.exists():
            encrypted = path.read_text()
            value = self.crypto.decrypt(encrypted)
            self._cache[key] = value
            return value
        return None

    def delete(self, key: str) -> None:
        """Delete a credential."""
        safe_key = base64.b64encode(key.encode()).decode().replace("/", "_").replace("+", "-")
        path = self.store_dir / f"{safe_key}.enc"
        if path.exists():
            self.crypto.secure_delete(str(path))
        self._cache.pop(key, None)

    def list_keys(self) -> list[str]:
        """List stored credential keys."""
        keys = []
        for path in self.store_dir.glob("*.enc"):
            safe_key = path.stem
            key = base64.b64decode(
                safe_key.replace("-", "+").replace("_", "/")
            ).decode()
            keys.append(key)
        return keys
