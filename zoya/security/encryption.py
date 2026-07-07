"""Encryption utilities providing AES cipher, hashing, and key generation."""

import base64
import hashlib
import hmac as _hmac
import os
import secrets
import struct
import uuid
import warnings


class AESCipher:
    BLOCK_SIZE = 16

    @classmethod
    def _derive_keystream(cls, key: str, iv: bytes, length: int) -> bytes:
        keystream = b""
        counter = 0
        while len(keystream) < length:
            block = hashlib.sha256(key.encode("utf-8") + iv + struct.pack(">I", counter)).digest()
            keystream += block
            counter += 1
        return keystream[:length]

    @classmethod
    def encrypt(cls, plaintext: str, key: str) -> str:
        iv = os.urandom(cls.BLOCK_SIZE)
        data = plaintext.encode("utf-8")
        padding_len = cls.BLOCK_SIZE - (len(data) % cls.BLOCK_SIZE)
        data += bytes([padding_len] * padding_len)

        keystream = cls._derive_keystream(key, iv, len(data))
        ciphertext = b""
        prev = iv

        for i in range(0, len(data), cls.BLOCK_SIZE):
            block = data[i : i + cls.BLOCK_SIZE]
            xored = bytes(a ^ b for a, b in zip(block, prev, strict=False))
            enc_block = bytes(
                a ^ b for a, b in zip(xored, keystream[i : i + cls.BLOCK_SIZE], strict=False)
            )
            ciphertext += enc_block
            prev = enc_block

        return base64.b64encode(iv + ciphertext).decode("ascii")

    @classmethod
    def decrypt(cls, ciphertext: str, key: str) -> str:
        raw = base64.b64decode(ciphertext)
        iv = raw[: cls.BLOCK_SIZE]
        data = raw[cls.BLOCK_SIZE :]

        keystream = cls._derive_keystream(key, iv, len(data))
        plaintext = b""
        prev = iv

        for i in range(0, len(data), cls.BLOCK_SIZE):
            block = data[i : i + cls.BLOCK_SIZE]
            xored = bytes(
                a ^ b for a, b in zip(block, keystream[i : i + cls.BLOCK_SIZE], strict=False)
            )
            dec_block = bytes(a ^ b for a, b in zip(xored, prev, strict=False))
            plaintext += dec_block
            prev = block

        padding_len = plaintext[-1]
        if padding_len > cls.BLOCK_SIZE:
            raise ValueError("invalid padding")
        plaintext = plaintext[:-padding_len]

        return plaintext.decode("utf-8")


class Hasher:
    @staticmethod
    def sha256(data: str) -> str:
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    @staticmethod
    def sha512(data: str) -> str:
        return hashlib.sha512(data.encode("utf-8")).hexdigest()

    @staticmethod
    def md5(data: str) -> str:
        warnings.warn(
            "MD5 is not secure for cryptographic purposes. Use SHA-256 instead.",
            UserWarning,
            stacklevel=2,
        )
        return hashlib.md5(data.encode("utf-8")).hexdigest()

    @staticmethod
    def hmac(key: str, data: str) -> str:
        return _hmac.new(key.encode("utf-8"), data.encode("utf-8"), hashlib.sha256).hexdigest()

    @staticmethod
    def pbkdf2(password: str, salt: str = None, iterations: int = 100000) -> tuple[str, str]:
        if salt is None:
            salt = base64.b64encode(os.urandom(16)).decode("ascii")
        key = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
        )
        return (key.hex(), salt)

    @staticmethod
    def verify_pbkdf2(password: str, hash: str, salt: str, iterations: int = 100000) -> bool:
        key = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt.encode("utf-8"), iterations
        )
        return key.hex() == hash

    @staticmethod
    def bcrypt_like(password: str, salt: str = None) -> tuple[str, str]:
        if salt is None:
            salt = base64.b64encode(os.urandom(16)).decode("ascii")
        h = salt + password
        for _ in range(64):
            h = hashlib.sha512(h.encode("utf-8")).hexdigest()
        return (h, salt)

    @staticmethod
    def verify_bcrypt_like(password: str, hash: str, salt: str) -> bool:
        h = salt + password
        for _ in range(64):
            h = hashlib.sha512(h.encode("utf-8")).hexdigest()
        return h == hash


class KeyGenerator:
    @staticmethod
    def generate_secret_key(length: int = 32) -> str:
        return secrets.token_hex(length)

    @staticmethod
    def generate_api_key(prefix: str = "zk_") -> str:
        return prefix + secrets.token_hex(32)

    @staticmethod
    def generate_otp(length: int = 6) -> str:
        return "".join(str(secrets.randbelow(10)) for _ in range(length))

    @staticmethod
    def generate_uuid4() -> str:
        return str(uuid.uuid4())
