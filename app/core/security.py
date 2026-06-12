# ruff: noqa: PLC0415
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
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from app.utils.standard import StandardResponse

TOOL_NAME = "redact_payload"
TOOL_VERSION = "1.0.0"
TOOL_CATEGORY = "utils"
TOOL_RISK_LEVEL: Literal["low"] = "low"
REQUIRES_APPROVAL = False
READS = False
WRITES = False
UPDATES = False
DELETES = False
TRADES = False
REQUIRES_NETWORK = False

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
    from app.utils.errors import ValidationError

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


def _validate_redactable_payload(payload: object) -> Mapping[str, object] | str:
    """Return a supported redaction payload or raise validation."""
    from app.utils.errors import ValidationError

    if not isinstance(payload, str | Mapping):
        raise ValidationError(
            "payload must be a mapping or string.",
            code="INVALID_INPUT",
        )
    return payload


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
    from app.utils.errors import ValidationError

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
    from app.utils.errors import ConfigurationError

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
    from app.utils.errors import SecurityError, ValidationError

    if not plaintext:
        raise ValidationError("plaintext must be non-empty.", code="INVALID_INPUT")
    if not key:
        raise SecurityError("encryption key is required.")
    fernet: Any = _fernet()
    return str(fernet(key.encode()).encrypt(plaintext.encode()).decode())


def decrypt_text(ciphertext: str, *, key: str) -> str:
    """Decrypt Fernet ciphertext with a caller-supplied key."""
    from app.utils.errors import SecurityError, ValidationError

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
    """Official low-risk read-only redaction tool for approved workflows.

    Use this tool to redact sensitive keys (like passwords, keys, tokens) from payloads.

    Args:
        payload (Mapping[str, object] | str): The payload or text to redact.
        request_id (str | None, optional): Optional trace request ID.

    Returns:
        StandardResponse: Standard tool response envelope.

    Errors:
        INVALID_INPUT: Payload is not a mapping or string.
        PERMISSION_DENIED: Redaction security validation fails.
        TOOL_EXECUTION_FAILED: Unexpected redaction runtime failure.

    Side effects:
        Emits structured tool logs only.
    """
    from app.utils.errors import SecurityError, ValidationError
    from app.utils.logger import logger
    from app.utils.standard import (
        build_metadata,
        error_response,
        success_response,
    )

    start = time.perf_counter()
    logger.info(
        "redact_payload called",
        extra={"event_name": "tool_called", "request_id": request_id},
    )
    metadata = build_metadata(
        tool_name=TOOL_NAME,
        tool_version=TOOL_VERSION,
        tool_category=TOOL_CATEGORY,
        tool_risk_level=TOOL_RISK_LEVEL,
        request_id=request_id,
        reads=READS,
        writes=WRITES,
        updates=UPDATES,
        deletes=DELETES,
        trades=TRADES,
        requires_network=REQUIRES_NETWORK,
        start_time=start,
    )
    try:
        redaction_payload = _validate_redactable_payload(payload)
        data = (
            redact_text(redaction_payload)
            if isinstance(redaction_payload, str)
            else redact_mapping(redaction_payload)
        )
        logger.info(
            "redact_payload completed",
            extra={"event_name": "tool_success", "request_id": request_id},
        )
        return success_response(
            message="Payload redacted.",
            data={"redacted": data},
            metadata=metadata,
        )
    except (SecurityError, ValidationError) as exc:
        logger.warning(
            "redact_payload failed",
            extra={"event_name": "tool_validation_failed", "request_id": request_id},
        )
        return error_response(
            message="Payload redaction failed.",
            code=exc.code,
            details=str(exc),
            metadata=metadata,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "redact_payload raised exception",
            extra={"event_name": "tool_exception", "request_id": request_id},
        )
        return error_response(
            message="Payload redaction failed.",
            code="TOOL_EXECUTION_FAILED",
            details=f"{exc.__class__.__name__}: {exc}",
            metadata=metadata,
        )


def classify_secret_key(key: str) -> Literal["sensitive", "safe"]:
    """Classify whether a key name appears sensitive."""
    from app.utils.errors import ValidationError

    if not isinstance(key, str) or not key:
        raise ValidationError("key must be a non-empty string.", code="INVALID_INPUT")
    return "sensitive" if SENSITIVE_KEY_PATTERN.search(key) else "safe"
