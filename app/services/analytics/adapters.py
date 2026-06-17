"""Deterministic trading result adapters for Analytics.

Converts raw backtest, paper, and live results
into canonical TradingResult dictionaries.
"""

from __future__ import annotations

from typing import Any

from app.utils.errors import ValidationError


class TradingResultAdapter:
    """Adapter to convert various trading result schemas.

    Converts raw schemas into canonical TradingResult structure.
    """

    REQUIRED_KEYS = frozenset(
        {
            "schema_version",
            "result_id",
            "phase",
            "trades",
            "equity_curve",
        }
    )

    @classmethod
    def to_canonical(
        cls,
        source_payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Convert a raw dictionary result payload to a canonical TradingResult.

        Args:
            source_payload: Dict containing the raw results.

        Returns:
            Canonical TradingResult dictionary.

        Raises:
            ValidationError: If required fields or compatibility validations fail.
        """
        if not isinstance(source_payload, dict):
            raise ValidationError("Trading result source payload must be a dictionary.")

        # Check for required top-level keys
        missing_keys = cls.REQUIRED_KEYS - source_payload.keys()
        if missing_keys:
            msg = (
                "Missing required keys for canonical TradingResult: "
                f"{sorted(missing_keys)}"
            )
            raise ValidationError(msg)

        # Validate values in payload
        schema_version = source_payload.get("schema_version")
        if not isinstance(schema_version, str) or not schema_version.strip():
            raise ValidationError("schema_version must be a non-empty string.")

        # Schema version compatibility check
        # We accept versions starting with "1."
        if not schema_version.startswith("1."):
            msg = f"Unsupported schema version: {schema_version}"
            raise ValidationError(msg)

        result_id = source_payload.get("result_id")
        if not isinstance(result_id, str) or not result_id.strip():
            raise ValidationError("result_id must be a non-empty string.")

        phase = source_payload.get("phase")
        if phase not in {"backtest", "paper", "live", "simulation"}:
            raise ValidationError(
                "phase must be one of: backtest, paper, live, simulation"
            )

        # Validate trades list
        trades = source_payload.get("trades")
        if not isinstance(trades, list):
            raise ValidationError("trades must be a list.")

        # Validate equity curve list
        equity_curve = source_payload.get("equity_curve")
        if not isinstance(equity_curve, list):
            raise ValidationError("equity_curve must be a list.")

        # Ensure lossless field preservation by copying all input fields
        canonical = dict(source_payload)

        # Ensure default values for standard fields if missing
        canonical.setdefault("strategy_id", "default_strategy")
        canonical.setdefault("strategy_version", "v1")
        canonical.setdefault("account_base_currency", "USD")
        canonical.setdefault("symbols", [])
        canonical.setdefault("timeframe", "H1")
        canonical.setdefault("metadata", {})

        return canonical
