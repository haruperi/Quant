# ruff: noqa: EM102
"""Base contract module defining the common foundation for all canonical models.

This module provides the Base Contract class, enforcing deterministic serialization,
hashing, schema version validation, and metadata namespacing rules.
"""

from __future__ import annotations

import hashlib
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.utils.errors import ValidationError
from app.utils.normalization import utc_now
from app.utils.standard import SENSITIVE_KEY_PATTERN, canonical_json

# Trace fields excluded from content hashing so that two contracts with
# identical business data but different creation times produce the same hash.
_TRACE_FIELDS: frozenset[str] = frozenset(
    {"created_at", "request_id", "workflow_id", "correlation_id"}
)


class Contract(BaseModel):
    """Canonical contract base model.

    Carries metadata fields required for tracing, auditing, and serialization
    stability. All contracts inherit deterministic serialization, content
    hashing, and schema compatibility checks.

    Attributes:
        schema_version: Semantic version string (major.minor.patch).
        created_at: UTC ISO 8601 timestamp of object creation.
        request_id: Optional causation/correlation request identifier.
        workflow_id: Optional workflow run identifier for distributed tracing.
        correlation_id: Optional causation chain identifier.
        metadata: Namespaced escape hatch for adapter-specific fields.
    """

    schema_version: str = Field(
        default="1.0.0",
        description="Contract schema version (major.minor.patch).",
    )
    created_at: str = Field(
        default_factory=lambda: utc_now().isoformat(),
        description="UTC ISO 8601 creation timestamp.",
    )
    request_id: str | None = Field(default=None, description="Correlation request ID.")
    workflow_id: str | None = Field(
        default=None, description="Associated workflow run identifier."
    )
    correlation_id: str | None = Field(
        default=None, description="Causation correlation identifier."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Escape hatch for namespaced adapter, provider, or experimental "
            "fields. All keys must be namespaced (e.g. 'mt5.ticket')."
        ),
    )

    @field_validator("metadata")
    @classmethod
    def validate_metadata_structure(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate metadata keys are namespaced and do not contain secrets.

        Args:
            v: The metadata dict to validate.

        Returns:
            The validated metadata dict.

        Raises:
            TypeError: If any key is not a string.
            ValueError: If any key is not namespaced, matches a sensitive
                pattern, or if the dict is not deterministically serializable.
        """
        for key in v:
            if not isinstance(key, str):
                raise TypeError("Metadata keys must be strings.")
            if "." not in key and ":" not in key:
                msg = (
                    f"Metadata key '{key}' is not namespaced. "
                    "Keys must be namespaced with a '.' or ':' separator."
                )
                raise ValueError(msg)
            if SENSITIVE_KEY_PATTERN.search(key):
                msg = (
                    f"Metadata key '{key}' matches sensitive key pattern "
                    "and is not allowed."
                )
                raise ValueError(msg)

        # Verify that metadata can be serialized deterministically.
        try:
            canonical_json(v)
        except (TypeError, ValueError) as e:
            msg = f"Metadata is not deterministically serializable: {e}"
            raise ValueError(msg) from e

        return v

    @model_validator(mode="after")
    def validate_trace_identifiers(self) -> Contract:
        """Validate that trace identifier fields are non-empty strings or None.

        Returns:
            The validated Contract instance.

        Raises:
            ValueError: If any trace field is set to a blank string.
        """
        for name in ("request_id", "workflow_id", "correlation_id"):
            val = getattr(self, name)
            if val is not None and (not isinstance(val, str) or not val.strip()):
                raise ValueError(f"{name} must be a non-empty string or None.")
        return self

    def to_json(self) -> str:
        """Serialize this contract to a deterministic canonical JSON string.

        Returns:
            Deterministic, key-sorted canonical JSON string.

        Raises:
            ValidationError: If the contract cannot be serialized.
        """
        try:
            return canonical_json(self.model_dump())
        except (TypeError, ValueError) as e:
            raise ValidationError(f"Failed to serialize contract: {e}") from e

    def content_hash(self) -> str:
        """Calculate a stable SHA256 hash over business-data fields only.

        Excludes trace fields (``created_at``, ``request_id``,
        ``workflow_id``, ``correlation_id``) so that two contracts with
        identical content but different creation times or trace contexts
        produce the same hash. Use this for caching, evidence packs, and
        reproducibility checks.

        Returns:
            SHA256 hex digest (64 characters).
        """
        payload = {k: v for k, v in self.model_dump().items() if k not in _TRACE_FIELDS}
        try:
            serialized = canonical_json(payload)
        except (TypeError, ValueError) as e:
            raise ValidationError(f"Failed to compute content hash: {e}") from e
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def contract_hash(self) -> str:
        """Calculate SHA256 hash over the full serialized contract.

        Includes all fields, including ``created_at`` and trace identifiers.
        Two contracts are byte-for-byte identical only if every field matches.
        For content-only comparison, use :meth:`content_hash` instead.

        Returns:
            SHA256 hex digest (64 characters).
        """
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    def check_compatibility(self, target_version: str) -> bool:
        """Check whether this contract version is compatible with a target.

        Compatibility rules:
        - Major version must match exactly.
        - This contract's minor version must be >= the target's minor version.

        Args:
            target_version: Schema version string to compare against
                (e.g. ``'1.1.0'``).

        Returns:
            True if this contract is compatible with the target version.
        """
        min_parts = 2
        try:
            current_parts = [int(p) for p in self.schema_version.split(".")]
            target_parts = [int(p) for p in target_version.split(".")]
            if len(current_parts) < min_parts or len(target_parts) < min_parts:
                return False
            if current_parts[0] != target_parts[0]:
                return False
            return current_parts[1] >= target_parts[1]
        except ValueError:
            return False
