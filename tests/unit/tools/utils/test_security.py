"""Unit tests for security helpers."""

import pytest
from tools.utils import (
    classify_secret_key,
    decrypt_text,
    encrypt_text,
    generate_encryption_key,
    hash_password,
    redact_mapping,
    redact_payload,
    redact_text,
    verify_password,
)


def test_redaction_removes_sensitive_values() -> None:
    """Redaction handles text and nested mappings."""
    redacted = redact_text("token=abcdef1234567890abcdef1234567890")
    mapping = redact_mapping({"api_key": "secret", "nested": {"password": "x"}})
    response = redact_payload({"authorization": "Bearer token"})

    assert "[REDACTED]" in redacted
    assert mapping["api_key"] == "[REDACTED]"
    assert response["status"] == "success"
    assert classify_secret_key("password") == "sensitive"


def test_hashing_and_encryption_roundtrip() -> None:
    """Password hashing and optional encryption helpers round-trip safely."""
    password_hash = hash_password(
        "correct horse battery staple", salt=b"1234567890123456"
    )
    pytest.importorskip("cryptography")
    key = generate_encryption_key()
    ciphertext = encrypt_text("payload", key=key)

    assert verify_password("correct horse battery staple", password_hash) is True
    assert verify_password("wrong", password_hash) is False
    assert decrypt_text(ciphertext, key=key) == "payload"
