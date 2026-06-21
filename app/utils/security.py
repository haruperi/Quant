"""Security helpers for redaction, hashing, and optional encryption.

This module is a support helper, not an official AI tool (except for the
``redact_payload`` exported tool). It provides denylist-based secret
redaction, Argon2id/PBKDF2 password hashing, Fernet symmetric encryption,
and secret-version selection.

Public exports:
    MAX_REDACTION_DEPTH, SECRET_VERSION_NOT_FOUND, SENSITIVE_KEY_PATTERN,
    RedactionDiagnostics, SecretVersion,
    redact_text, redact_mapping, redact_value,
    redact_mapping_with_diagnostics, classify_secret_key,
    hash_password, verify_password,
    generate_encryption_key, load_encryption_key,
    encrypt_text, decrypt_text, encrypt_value, decrypt_value,
    select_active_secret_version, redact_payload.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import importlib
import os
import re
import time
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Final, Literal, TypedDict

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

MIN_PASSWORD_HASH_ITERATIONS: Final[int] = 100_000
MAX_REDACTION_DEPTH: Final[int] = 12
SECRET_VERSION_NOT_FOUND: Final[str] = (
    "SECRET_VERSION_NOT_FOUND"  # pragma: allowlist secret  # noqa: S105
)
SENSITIVE_KEY_PATTERN = re.compile(
    r"(password|passphrase|token|secret|credential|api_?key|authorization|private)",
    re.IGNORECASE,
)
SECRET_VALUE_PATTERN = re.compile(
    r"(?i)((?:password|token|secret|api_?key|authorization)\s*[:=]\s*)[^\s,;&]+"
)
LONG_SECRET_PATTERN = re.compile(r"(?i)\b(?:[a-f0-9]{32,}|eyJ[A-Za-z0-9_.=-]+)\b")


class RedactionDiagnostics(TypedDict):
    """Diagnostics describing redacted fields without exposing values."""

    redacted_paths: list[str]
    truncated_paths: list[str]


class SecretVersion(TypedDict, total=False):
    """Secret-version metadata accepted by selection helpers."""

    version: int | str
    active: bool
    value: str


def redact_text(text: str, *, replacement: str = "[REDACTED]") -> str:
    """Return text with secret-like material redacted."""
    from app.utils.errors import ValidationError

    if not isinstance(text, str):
        raise ValidationError("text must be a string.", code="INVALID_INPUT")
    redacted = SECRET_VALUE_PATTERN.sub(rf"\1{replacement}", text)
    return LONG_SECRET_PATTERN.sub(replacement, redacted)


def redact_mapping(
    payload: Mapping[str, object],
    *,
    allowlist: set[str] | None = None,
    max_depth: int = MAX_REDACTION_DEPTH,
) -> dict[str, object]:
    """Return a recursively redacted mapping copy."""
    diagnostics = _new_diagnostics()
    redacted = _redact_mapping(
        payload,
        allowlist=allowlist or set(),
        diagnostics=diagnostics,
        path="",
        depth=0,
        max_depth=max_depth,
    )
    return redacted


def redact_value(
    value: object,
    *,
    allowlist: set[str] | None = None,
    max_depth: int = MAX_REDACTION_DEPTH,
) -> object:
    """Return a redacted JSON-like value."""
    diagnostics = _new_diagnostics()
    return _redact_value(
        value,
        allowlist=allowlist or set(),
        diagnostics=diagnostics,
        path="",
        depth=0,
        max_depth=max_depth,
    )


def redact_mapping_with_diagnostics(
    payload: Mapping[str, object],
    *,
    allowlist: set[str] | None = None,
    max_depth: int = MAX_REDACTION_DEPTH,
) -> tuple[dict[str, object], RedactionDiagnostics]:
    """Return a redacted copy and bounded field-level diagnostics.

    Args:
        payload: Mapping to redact.
        allowlist: Narrow field-path allowlist for safe values.
        max_depth: Maximum recursive redaction depth.

    Returns:
        Tuple of redacted mapping and diagnostics containing redacted/truncated
        field paths only.
    """
    diagnostics = _new_diagnostics()
    redacted = _redact_mapping(
        payload,
        allowlist=allowlist or set(),
        diagnostics=diagnostics,
        path="",
        depth=0,
        max_depth=max_depth,
    )
    return redacted, diagnostics


def _new_diagnostics() -> RedactionDiagnostics:
    """Build empty redaction diagnostics."""
    return {"redacted_paths": [], "truncated_paths": []}


def _redact_value(
    value: object,
    *,
    allowlist: set[str],
    diagnostics: RedactionDiagnostics,
    path: str,
    depth: int,
    max_depth: int,
) -> object:
    """Return redacted JSON-like value with recursion protection."""
    if depth > max_depth:
        diagnostics["truncated_paths"].append(path or "$")
        return "[TRUNCATED]"
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, Mapping):
        return _redact_mapping(
            value,
            allowlist=allowlist,
            diagnostics=diagnostics,
            path=path,
            depth=depth,
            max_depth=max_depth,
        )
    if isinstance(value, list | tuple | set):
        return [
            _redact_value(
                item,
                allowlist=allowlist,
                diagnostics=diagnostics,
                path=f"{path}/{index}",
                depth=depth + 1,
                max_depth=max_depth,
            )
            for index, item in enumerate(value)
        ]
    return value


def _redact_mapping(
    payload: Mapping[str, object],
    *,
    allowlist: set[str],
    diagnostics: RedactionDiagnostics,
    path: str,
    depth: int,
    max_depth: int,
) -> dict[str, object]:
    """Return a recursively redacted mapping copy."""
    from app.utils.errors import SecurityError, ValidationError

    if max_depth < 0:
        raise ValidationError("max_depth must be non-negative.", code="INVALID_INPUT")
    if any("*" in item for item in allowlist):
        raise SecurityError("redaction allowlist cannot contain wildcards.")
    if depth > max_depth:
        diagnostics["truncated_paths"].append(path or "$")
        return {"_truncated": True}
    redacted: dict[str, object] = {}
    for key, value in payload.items():
        key_text = str(key)
        field_path = f"{path}/{key_text}" if path else key_text
        if SENSITIVE_KEY_PATTERN.search(key_text) and field_path not in allowlist:
            redacted[key_text] = "[REDACTED]"
            diagnostics["redacted_paths"].append(field_path)
        else:
            redacted[key_text] = _redact_value(
                value,
                allowlist=allowlist,
                diagnostics=diagnostics,
                path=field_path,
                depth=depth + 1,
                max_depth=max_depth,
            )
    return redacted


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
    """Hash a password with Argon2id (preferred) or PBKDF2-HMAC-SHA256.

    Tries ``argon2-cffi`` first. Falls back to stdlib PBKDF2-HMAC-SHA256
    when the optional ``argon2`` package is unavailable.

    Args:
        password: Non-empty plaintext password to hash.
        salt: Optional explicit salt bytes for PBKDF2 fallback. When
            ``None``, a 16-byte random salt is generated. Ignored when
            Argon2id is used (Argon2 generates its own salt internally).
        iterations: PBKDF2 iteration count. Must be at least
            ``MIN_PASSWORD_HASH_ITERATIONS``. Ignored for Argon2id.

    Returns:
        Opaque hash string. Argon2id hashes begin with ``$argon2id$``.
        PBKDF2 hashes begin with ``pbkdf2_sha256$``.

    Raises:
        ValidationError: If ``password`` is empty or ``iterations`` is
            below the approved minimum.

    Side effects:
        None. Password value is never logged.
    """
    from app.utils.errors import ValidationError

    if not isinstance(password, str) or not password:
        raise ValidationError(
            "password must be a non-empty string.", code="INVALID_INPUT"
        )
    # Prefer Argon2id when available.
    try:
        from argon2 import (
            PasswordHasher,  # type: ignore[import-not-found, unused-ignore]
        )

        ph = PasswordHasher()
        return str(ph.hash(password))
    except ImportError:
        pass
    # PBKDF2-HMAC-SHA256 stdlib fallback.
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
    """Verify a password against a ``hash_password`` value.

    Supports both Argon2id hashes (``$argon2id$…``) and legacy
    ``pbkdf2_sha256$…`` hashes produced by the stdlib fallback.

    Args:
        password: Plaintext candidate password.
        password_hash: Hash produced by ``hash_password``.

    Returns:
        ``True`` when the password matches the hash; ``False`` otherwise.

    Side effects:
        None. Uses constant-time comparison to prevent timing attacks.
    """
    if password_hash.startswith("$argon2"):
        try:
            from argon2 import (
                PasswordHasher,  # type: ignore[import-not-found, unused-ignore]
            )
            from argon2.exceptions import (  # type: ignore[import-not-found, unused-ignore]
                VerifyMismatchError,
            )

            ph = PasswordHasher()
            try:
                return bool(ph.verify(password_hash, password))
            except VerifyMismatchError:
                return False
        except ImportError:
            return False
    # Legacy PBKDF2-HMAC-SHA256 path.
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


def load_encryption_key(environ: Mapping[str, str] | None = None) -> str:
    """Load the active Fernet key from ``ENCRYPTION_KEY``.

    Args:
        environ: Optional environment mapping for deterministic tests.

    Returns:
        Fernet key string.

    Raises:
        SecurityError: If the key is missing.
    """
    from app.utils.errors import SecurityError

    source = os.environ if environ is None else environ
    key = source.get("ENCRYPTION_KEY", "")
    if not key:
        raise SecurityError("ENCRYPTION_KEY is not configured.")
    return key


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
    """Decrypt Fernet ciphertext with a caller-supplied key.

    Args:
        ciphertext: Non-empty Fernet-encrypted string.
        key: Fernet key string. Must not be empty.

    Returns:
        Decrypted plaintext string.

    Raises:
        ValidationError: If ``ciphertext`` is empty.
        SecurityError: If ``key`` is empty or decryption fails (invalid
            token, wrong key, or corrupted ciphertext).

    Side effects:
        None.
    """
    from app.utils.errors import SecurityError, ValidationError

    if not ciphertext:
        raise ValidationError("ciphertext must be non-empty.", code="INVALID_INPUT")
    if not key:
        raise SecurityError("encryption key is required.")
    fernet: Any = _fernet()
    try:
        return str(fernet(key.encode()).decrypt(ciphertext.encode()).decode())
    except Exception as exc:
        raise SecurityError(
            "decryption failed: invalid token or key.",
            code="PERMISSION_DENIED",
        ) from exc


def encrypt_value(plaintext: str, *, key: str | None = None) -> str:
    """Encrypt text using an explicit or environment-supplied Fernet key."""
    return encrypt_text(plaintext, key=key or load_encryption_key())


def decrypt_value(ciphertext: str, *, key: str | None = None) -> str:
    """Decrypt text using an explicit or environment-supplied Fernet key."""
    return decrypt_text(ciphertext, key=key or load_encryption_key())


def select_active_secret_version(
    versions: Mapping[str, SecretVersion | Mapping[str, object]],
) -> SecretVersion:
    """Select the active secret with the highest numeric version.

    Args:
        versions: Mapping of secret-version records. Active records must contain
            ``active=True`` and numeric ``version``.

    Returns:
        The active secret-version metadata with the highest numeric version.

    Raises:
        SecurityError: If no active version exists or if the highest active
            numeric version is duplicated.
    """
    from app.utils.errors import SecurityError, ValidationError

    active: list[tuple[int, SecretVersion]] = []
    for item in versions.values():
        if not bool(item.get("active", False)):
            continue
        version_value = item.get("version")
        if not isinstance(version_value, str | int):
            raise ValidationError(
                "active secret versions require numeric version.",
                code="INVALID_INPUT",
            )
        try:
            version = int(version_value)
        except ValueError as exc:
            raise ValidationError(
                "active secret versions require numeric version.",
                code="INVALID_INPUT",
            ) from exc
        selected: SecretVersion = {
            "version": version,
            "active": True,
        }
        value = item.get("value")
        if isinstance(value, str):
            selected["value"] = value
        active.append((version, selected))
    if not active:
        raise SecurityError(
            "No active secret version exists.", code=SECRET_VERSION_NOT_FOUND
        )
    highest = max(version for version, _item in active)
    matches = [item for version, item in active if version == highest]
    if len(matches) > 1:
        raise SecurityError(
            "Duplicate active secret versions conflict.",
            code="SECRET_VERSION_CONFLICT",
        )
    return matches[0]


def redact_payload(
    payload: Mapping[str, object] | str,
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Official low-risk read-only redaction tool for approved workflows.

    Use this tool to redact sensitive keys (passwords, API keys, tokens)
    from mapping payloads or free-text strings.

    Args:
        payload: The payload or text to redact. Must be a ``Mapping`` or
            a ``str``.
        request_id: Optional trace request identifier.

    Returns:
        Standard tool response envelope with ``data.redacted`` containing
        the redacted output.

    Raises:
        N/A — all exceptions are caught and returned as error responses.

    Side effects:
        Emits structured tool call, success, and exception logs only.
        Secret values are never logged.
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
