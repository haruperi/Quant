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


class Contract(BaseModel):
    """Canonical contract base model.

    Carries metadata fields required for tracing, auditing, and serialization stability.
    """

    schema_version: str = Field(
        default="1.0.0", description="Contract schema version (major.minor.patch)."
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
            "Escape hatch for namespaced adapter, provider, or experimental fields."
        ),
    )

    @field_validator("metadata")
    @classmethod
    def validate_metadata_structure(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Validate metadata keys and structure.

        Requires that all keys are namespaced (contain a dot or a colon, e.g.
        'mt5.ticket') to prevent key collisions, and verifies that they do
        not contain sensitive names.
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

        # Verify that metadata can be serialized deterministically
        try:
            canonical_json(v)
        except Exception as e:
            msg = f"Metadata is not deterministically serializable: {e}"
            raise ValueError(msg) from e

        return v

    @model_validator(mode="after")
    def validate_trace_identifiers(self) -> Contract:
        """Post-validation check on trace identifiers formatting."""
        for name in ("request_id", "workflow_id", "correlation_id"):
            val = getattr(self, name)
            if val is not None and (not isinstance(val, str) or not val.strip()):
                raise ValueError(f"{name} must be a non-empty string or None.")
        return self

    def to_json(self) -> str:
        """Serialize contract to deterministic canonical JSON string.

        Returns:
            str: Deterministic, sorted canonical JSON string.
        """
        try:
            return canonical_json(self.model_dump())
        except Exception as e:
            raise ValidationError(f"Failed to serialize contract: {e}") from e

    def contract_hash(self) -> str:
        """Calculate deterministic SHA256 contract hash for reproducibility and caching.

        Returns:
            str: SHA256 hex digest.
        """
        return hashlib.sha256(self.to_json().encode("utf-8")).hexdigest()

    def check_compatibility(self, target_version: str) -> bool:
        """Determine compatibility of this contract version against a target version.

        Rules:
        - Major version must match exactly.
        - This object's minor version must be greater than or equal to
          the target's minor.

        Args:
            target_version: Schema version string to compare against (e.g. '1.1.0').

        Returns:
            bool: True if compatible, otherwise False.
        """
        min_parts = 2
        try:
            current_parts = [int(p) for p in self.schema_version.split(".")]
            target_parts = [int(p) for p in target_version.split(".")]
            if len(current_parts) < min_parts or len(target_parts) < min_parts:
                return False
            # Major must match exactly
            if current_parts[0] != target_parts[0]:
                return False
            # Minor must be >= target's minor
            return current_parts[1] >= target_parts[1]
        except ValueError:
            return False
