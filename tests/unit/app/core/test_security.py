"""Unit tests for security helpers."""

import pytest
from app.core.security import (
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
from app.utils.errors import SecurityError, ValidationError


def test_redaction_removes_sensitive_values() -> None:
    """Redaction handles text and nested mappings."""
    redacted = redact_text("token=abcdef1234567890abcdef1234567890")
    mapping = redact_mapping({"api_key": "secret", "nested": {"password": "x"}})
    response = redact_payload({"authorization": "Bearer token"})

    assert "[REDACTED]" in redacted
    assert mapping["api_key"] == "[REDACTED]"
    assert response["status"] == "success"
    assert classify_secret_key("password") == "sensitive"


def test_redaction_rejects_invalid_inputs_with_clear_errors() -> None:
    """Redaction helpers validate input types and return standard errors at boundary."""
    with pytest.raises(ValidationError, match="text must be a string"):
        redact_text(123)  # type: ignore[arg-type]

    response = redact_payload(["not", "a", "mapping"])  # type: ignore[arg-type]

    assert response["status"] == "error"
    assert response["error"] is not None
    assert response["error"]["code"] == "INVALID_INPUT"
    assert response["metadata"]["tool_name"] == "redact_payload"


def test_redact_payload_maps_unexpected_failures_to_standard_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unexpected redaction failures return a standard execution error."""

    def fail_redaction(_payload: object) -> dict[str, object]:
        raise RuntimeError("unexpected redaction failure")

    monkeypatch.setattr("app.core.security.redact_mapping", fail_redaction)

    response = redact_payload({"safe": "value"})

    assert response["status"] == "error"
    assert response["error"] is not None
    assert response["error"]["code"] == "TOOL_EXECUTION_FAILED"


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


def test_hashing_and_encryption_reject_invalid_inputs() -> None:
    """Security helpers fail closed for malformed password and encryption inputs."""
    with pytest.raises(ValidationError, match="password must be a non-empty string"):
        hash_password("")
    with pytest.raises(ValidationError, match="approved minimum"):
        hash_password("secret", iterations=1)

    assert verify_password("secret", "not-a-valid-hash") is False
    assert verify_password("secret", "argon2$1$salt$digest") is False

    pytest.importorskip("cryptography")
    key = generate_encryption_key()
    with pytest.raises(ValidationError, match="plaintext must be non-empty"):
        encrypt_text("", key=key)
    with pytest.raises(SecurityError, match="encryption key is required"):
        encrypt_text("payload", key="")
    with pytest.raises(ValidationError, match="ciphertext must be non-empty"):
        decrypt_text("", key=key)
    with pytest.raises(SecurityError, match="encryption key is required"):
        decrypt_text("payload", key="")


def test_classify_secret_key_rejects_empty_keys() -> None:
    """Secret-key classification validates external key names."""
    with pytest.raises(ValidationError, match="key must be a non-empty string"):
        classify_secret_key("")
