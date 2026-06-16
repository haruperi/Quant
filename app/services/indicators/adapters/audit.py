"""Tamper-evident audit logging adapter for the indicators service.

Provides chained append-only HMAC-SHA256 signature audits for calculations.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import threading
import time
from dataclasses import asdict
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.indicators.protocols import (
        IndicatorContext,
        IndicatorManifest,
    )


class IndicatorAuditLogger:
    """Tamper-evident, append-only logger for indicator execution manifests."""

    def __init__(self, secret_key: bytes = b"haruquant_audit_secret_key_123") -> None:
        """Initialize lock, signing key, and empty audit storage."""
        self._lock = threading.Lock()
        self._secret_key = secret_key
        self._audit_log: list[dict[str, Any]] = []
        self._last_signature: str = ""

    def log_audit(
        self,
        manifest: IndicatorManifest,
        context: IndicatorContext,
        audit_mode: bool = True,
    ) -> str:
        """Create and sign a new audit trail log entry for an execution.

        Returns:
            The HMAC-SHA256 hex signature of the generated entry.
        """
        if not audit_mode:
            return ""

        # Build log payload using manifest and context details
        manifest_dict = asdict(manifest)
        request_metadata = {
            "actor": context.actor,
            "workflow": context.workflow,
            "correlation_id": context.correlation_id,
            "request_id": context.request_id,
            "timestamp": time.time(),
        }

        entry = {
            "manifest": manifest_dict,
            "request_metadata": request_metadata,
            "input_checksum": manifest.input_checksum,
            "output_checksum": manifest.output_checksum,
            "previous_signature": self._last_signature,
        }

        # Deterministically serialize the payload for hashing
        serialized = json.dumps(entry, sort_keys=True)

        # Generate HMAC signature
        signature = hmac.new(
            self._secret_key,
            serialized.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        entry["signature"] = signature

        with self._lock:
            self._audit_log.append(entry)
            self._last_signature = signature

        return signature

    def get_entries(self) -> list[dict[str, Any]]:
        """Return all logged audit entries."""
        with self._lock:
            return list(self._audit_log)

    def verify_chain(self) -> bool:
        """Verify the integrity of the audit chain by recalculating signatures.

        Returns:
            True if all signatures match, False otherwise.
        """
        with self._lock:
            current_prev_sig = ""
            for entry in self._audit_log:
                # Reconstruct signing payload
                entry_copy = {
                    "manifest": entry["manifest"],
                    "request_metadata": entry["request_metadata"],
                    "input_checksum": entry["input_checksum"],
                    "output_checksum": entry["output_checksum"],
                    "previous_signature": current_prev_sig,
                }
                serialized = json.dumps(entry_copy, sort_keys=True)
                expected_sig = hmac.new(
                    self._secret_key,
                    serialized.encode("utf-8"),
                    hashlib.sha256,
                ).hexdigest()

                if expected_sig != entry["signature"]:
                    return False
                current_prev_sig = expected_sig
            return True


# Global audit logger instance
global_audit_logger = IndicatorAuditLogger()
