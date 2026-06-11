"""Security helpers for redaction, hashing, and optional encryption."""

from __future__ import annotations

import base64
import hashlib
import hmac
import importlib
import os
import re
import time
from collections.abc import Mapping
from typing import Any, Literal

from tools.utils.errors import ConfigurationError, SecurityError, ValidationError
from tools.utils.standard import (
    StandardResponse,
    build_metadata,
    error_response,
    success_response,
)

TOOL_VERSION = "1.0.0"
MIN_PASSWORD_HASH_ITERATIONS = 100_000
SENSITIVE_KEY_PATTERN = re.compile(
    r"(password|passphrase|token|secret|credential|api_?key|authorization|private)",
    re.IGNORECASE,
)
SECRET_VALUE_PATTERN = re.compile(
    r"(?i)((?:password|token|secret|api_?key|authorization)\s*[:=]\s*)[^\s,;&]+"
)
LONG_SECRET_PATTERN = re.compile(r"(?i)\b(?:[a-f0-9]{32,}|eyJ[A-Za-z0-9_.=-]+)\b")


def redact_text(text: str, *, replacement: str = "[REDACTED]") -> str:
    """Return text with secret-like material redacted."""
    if not isinstance(text, str):
        raise ValidationError("text must be a string.", code="INVALID_INPUT")
    redacted = SECRET_VALUE_PATTERN.sub(rf"\1{replacement}", text)
    return LONG_SECRET_PATTERN.sub(replacement, redacted)


def redact_mapping(payload: Mapping[str, object]) -> dict[str, object]:
    """Return a recursively redacted mapping copy."""
    redacted: dict[str, object] = {}
    for key, value in payload.items():
        key_text = str(key)
        if SENSITIVE_KEY_PATTERN.search(key_text):
            redacted[key_text] = "[REDACTED]"
        else:
            redacted[key_text] = redact_value(value)
    return redacted


def redact_value(value: object) -> object:
    """Return a redacted JSON-like value."""
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Mapping):
        return redact_mapping(value)
    if isinstance(value, list | tuple | set):
        return [redact_value(item) for item in value]
    return value


def hash_password(
    password: str,
    *,
    salt: bytes | None = None,
    iterations: int = 390_000,
) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256.

    Argon2id remains preferred for production policy, but this stdlib fallback
    is deterministic, explicit, salted, and available without optional
    dependencies.
    """
    if not isinstance(password, str) or not password:
        raise ValidationError(
            "password must be a non-empty string.", code="INVALID_INPUT"
        )
    if iterations < MIN_PASSWORD_HASH_ITERATIONS:
        raise ValidationError(
            "iterations is below the approved minimum.", code="INVALID_INPUT"
        )
    salt_bytes = os.urandom(16) if salt is None else salt
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt_bytes, iterations)
    return (
        "pbkdf2_sha256$"
        f"{iterations}$"
        f"{base64.urlsafe_b64encode(salt_bytes).decode()}$"
        f"{base64.urlsafe_b64encode(digest).decode()}"
    )


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against a ``hash_password`` value."""
    try:
        algorithm, iterations_text, salt_text, _digest_text = password_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = hash_password(password, salt=salt, iterations=iterations)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(expected, password_hash)


def _fernet() -> object:
    """Return the Fernet class lazily."""
    try:
        return importlib.import_module("cryptography.fernet").Fernet
    except ImportError as exc:  # pragma: no cover - dependency exists in CI image
        message = "cryptography is required for encryption helpers."
        raise ConfigurationError(message, code="CONFIGURATION_ERROR") from exc


def generate_encryption_key() -> str:
    """Generate a Fernet encryption key."""
    fernet: Any = _fernet()
    return str(fernet.generate_key().decode())


def encrypt_text(plaintext: str, *, key: str) -> str:
    """Encrypt text with a caller-supplied Fernet key."""
    if not plaintext:
        raise ValidationError("plaintext must be non-empty.", code="INVALID_INPUT")
    if not key:
        raise SecurityError("encryption key is required.")
    fernet: Any = _fernet()
    return str(fernet(key.encode()).encrypt(plaintext.encode()).decode())


def decrypt_text(ciphertext: str, *, key: str) -> str:
    """Decrypt Fernet ciphertext with a caller-supplied key."""
    if not ciphertext:
        raise ValidationError("ciphertext must be non-empty.", code="INVALID_INPUT")
    if not key:
        raise SecurityError("encryption key is required.")
    fernet: Any = _fernet()
    return str(fernet(key.encode()).decrypt(ciphertext.encode()).decode())


def redact_payload(
    payload: Mapping[str, object] | str,
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only redaction tool for approved workflows."""
    start = time.perf_counter()
    metadata = build_metadata(
        tool_name="redact_payload",
        start_time=start,
        tool_version=TOOL_VERSION,
        tool_category="utils",
        tool_risk_level="low",
        request_id=request_id,
    )
    try:
        data = (
            redact_text(payload)
            if isinstance(payload, str)
            else redact_mapping(payload)
        )
        return success_response(
            message="Payload redacted.",
            data={"redacted": data},
            metadata=metadata,
        )
    except (SecurityError, ValidationError) as exc:
        return error_response(
            message="Payload redaction failed.",
            code=exc.code,
            details=str(exc),
            metadata=metadata,
        )


def classify_secret_key(key: str) -> Literal["sensitive", "safe"]:
    """Classify whether a key name appears sensitive."""
    if not isinstance(key, str) or not key:
        raise ValidationError("key must be a non-empty string.", code="INVALID_INPUT")
    return "sensitive" if SENSITIVE_KEY_PATTERN.search(key) else "safe"
