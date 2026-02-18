"""
Password security helpers.

Supports:
- New hashes: pbkdf2_sha256 with per-password random salt
- Legacy verification: plain SHA256 hex digest
"""

import hashlib
import hmac
import os

PBKDF2_ALGO = "sha256"
PBKDF2_ITERATIONS = 260000
PBKDF2_PREFIX = "pbkdf2_sha256"


def hash_password(password: str, iterations: int = PBKDF2_ITERATIONS) -> str:
    if not isinstance(password, str) or not password:
        raise ValueError("password must be a non-empty string")
    salt = os.urandom(16).hex()
    derived = hashlib.pbkdf2_hmac(PBKDF2_ALGO, password.encode("utf-8"), bytes.fromhex(salt), iterations)
    return f"{PBKDF2_PREFIX}${iterations}${salt}${derived.hex()}"


def is_legacy_sha256_hash(stored_hash: str) -> bool:
    if not isinstance(stored_hash, str):
        return False
    if len(stored_hash) != 64:
        return False
    return all(c in "0123456789abcdefABCDEF" for c in stored_hash)


def verify_password(password: str, stored_hash: str) -> bool:
    if not password or not stored_hash:
        return False

    if stored_hash.startswith(f"{PBKDF2_PREFIX}$"):
        parts = stored_hash.split("$")
        if len(parts) != 4:
            return False
        _, iterations_raw, salt_hex, expected_hex = parts
        try:
            iterations = int(iterations_raw)
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(expected_hex)
        except ValueError:
            return False

        actual = hashlib.pbkdf2_hmac(PBKDF2_ALGO, password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)

    if is_legacy_sha256_hash(stored_hash):
        legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy, stored_hash)

    return False
