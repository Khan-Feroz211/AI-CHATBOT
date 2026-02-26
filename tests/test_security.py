import hashlib

from src.core.security import hash_password, is_legacy_sha256_hash, verify_password


def test_hash_password_generates_pbkdf2_format():
    value = hash_password("strong-pass-123")
    assert value.startswith("pbkdf2_sha256$")
    assert verify_password("strong-pass-123", value)
    assert not verify_password("wrong-pass", value)


def test_legacy_sha256_still_verifies():
    legacy = hashlib.sha256("abc123".encode("utf-8")).hexdigest()
    assert is_legacy_sha256_hash(legacy)
    assert verify_password("abc123", legacy)
    assert not verify_password("abc124", legacy)
