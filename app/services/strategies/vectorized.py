# ruff: noqa: E501, EM101, EM102, TRY301, TRY300, BLE001, C901, PLR0912, PLR0915, SIM102, RUF100
"""Vectorized batch strategy execution engine.

Calculates signal series across dataframes, aligns timing policies (shifting features),
and inspects emitted TradeIntents for lookahead risks and stale data.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pandas as pd

from app.services.strategies.protocols import (
    StrategyExecutionContext,
    StrategyRefInput,
    StrategyTimingPolicy,
)
from app.services.strategies.registry import get_strategy, validate_strategy_config
from app.utils.errors import (
    StrategyLookaheadDetectedError,
    StrategyStaleDataError,
    StrategyUnsupportedTimingPolicyError,
    map_exception_to_strategy_error,
)
from app.utils.logger import logger


def validate_timezone_consistency(df: pd.DataFrame) -> None:
    """Ensure that DatetimeIndex or timestamp columns are timezone-aware."""
    if df.empty:
        return

    # Check index
    if isinstance(df.index, pd.DatetimeIndex):
        if df.index.tz is None:
            raise ValidationError("DatetimeIndex must be timezone-aware.")
    elif isinstance(df.index, pd.MultiIndex):
        if "timestamp" in df.index.names:
            ts_level = df.index.get_level_values("timestamp")
            if isinstance(ts_level, pd.DatetimeIndex) and ts_level.tz is None:
                raise ValidationError(
                    "MultiIndex level 'timestamp' must be timezone-aware."
                )

    # Check columns
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            if not hasattr(df[col].dtype, "tz") or df[col].dtype.tz is None:
                raise ValidationError(
                    f"Datetime column '{col}' must be timezone-aware."
                )


class ValidationError(ValueError):
    """Local validation helper for timezone checking."""


def run_vectorized_strategy_signals(
    strategy_ref: StrategyRefInput,
    market_data: pd.DataFrame,
    indicators: pd.DataFrame,
    timing_policy: StrategyTimingPolicy = "BAR_OPEN_PREVIOUS_CLOSE",
    context: StrategyExecutionContext | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute vectorized signal generation for a registered strategy.

    Shifts conditions/data to closed bars if required, enforces timezone/lookahead
    policies, and verifies expected alpha thresholds.

    Returns:
        Standard envelope dictionary containing status, data (intents), and errors.
    """
    request_id = context.request_id if context else None
    correlation_id = context.correlation_id if context else None
    decision_ts = context.decision_timestamp if context else None

    try:
        # Validate inputs
        if timing_policy != "BAR_OPEN_PREVIOUS_CLOSE":
            # REQ-STRAT-357: STRATEGY_UNSUPPORTED_TIMING_POLICY
            raise StrategyUnsupportedTimingPolicyError(
                f"Timing policy '{timing_policy}' is unsupported in vectorized signals."
            )

        validate_timezone_consistency(market_data)
        validate_timezone_consistency(indicators)

        # Retrieve strategy class
        strategy_class = get_strategy(
            strategy_ref.strategy_id, strategy_ref.version_constraint
        )

        # Validate config schema
        cfg = config or {}
        validated_config = validate_strategy_config(strategy_class, cfg)

        # Latency/staleness check
        # REQ-STRAT-058, REQ-STRAT-059
        max_latency = getattr(strategy_class, "max_data_latency_tolerance", None)
        if max_latency is not None and not market_data.empty and decision_ts:
            last_dt = market_data.index[-1]
            if (
                isinstance(market_data.index, pd.MultiIndex)
                and "timestamp" in market_data.index.names
            ):
                last_dt = market_data.index.get_level_values("timestamp")[-1]

            # Convert pd.Timedelta if max_latency is string/number
            tolerance = (
                pd.Timedelta(max_latency)
                if not isinstance(max_latency, pd.Timedelta)
                else max_latency
            )
            if decision_ts - last_dt > tolerance:
                raise StrategyStaleDataError(
                    f"Market data timestamp {last_dt} exceeds latency tolerance {max_latency} from decision {decision_ts}."
                )

        # Instantiate strategy and run
        strategy_instance = strategy_class()

        ctx = context or StrategyExecutionContext(
            environment=strategy_ref.environment,
            decision_timestamp=pd.Timestamp.now(tz="UTC"),
            timing_policy=timing_policy,
            seed_material="default_seed",
            request_id="default_req",
            correlation_id="default_corr",
        )

        # Shift inputs by default to ensure only closed bar data N-1 is accessed at Bar Open N
        # REQ-STRAT-053: Vectorized signal generation shall shift current-bar conditions so that bar-open entries are based on previous closed-bar values.
        shifted_indicators = indicators.shift(1) if not indicators.empty else indicators

        intents = strategy_instance.run_vectorized_signals(
            market_data, shifted_indicators, ctx, validated_config
        )

        # Lookahead detection
        # REQ-STRAT-060: If a vectorized batch detects lookahead at any element, the entire batch shall fail atomically.
        for intent in intents:
            if intent.signal_timestamp >= intent.decision_timestamp:
                raise StrategyLookaheadDetectedError(
                    f"Lookahead risk detected: signal timestamp {intent.signal_timestamp} "
                    f"must be strictly before decision timestamp {intent.decision_timestamp} under BAR_OPEN_PREVIOUS_CLOSE.",
                    code="STRATEGY_LOOKAHEAD_DETECTED",
                )

        # Evaluate min_expected_alpha and max_acceptable_transaction_cost
        # REQ-STRAT-039
        min_alpha = validated_config.get("min_expected_alpha")
        if min_alpha is None:
            min_alpha = getattr(strategy_class, "min_expected_alpha", None)

        max_cost = validated_config.get("max_acceptable_transaction_cost")
        if max_cost is None:
            max_cost = getattr(strategy_class, "max_acceptable_transaction_cost", None)

        active_intents = []
        suppressed_count = 0
        details = {}

        for intent in intents:
            suppress = False
            # Check expected alpha
            if min_alpha is not None:
                expected_alpha = Decimal(intent.lineage.get("expected_alpha", "0"))
                if expected_alpha < Decimal(str(min_alpha)):
                    suppress = True
                    details["suppression_reason"] = (
                        f"Alpha {expected_alpha} below threshold {min_alpha}"
                    )

            # Check transaction cost
            if max_cost is not None:
                cost = Decimal(intent.lineage.get("estimated_transaction_cost", "0"))
                if cost > Decimal(str(max_cost)):
                    suppress = True
                    details["suppression_reason"] = (
                        f"Cost {cost} above threshold {max_cost}"
                    )

            if suppress:
                suppressed_count += 1
            else:
                active_intents.append(intent)

        status = "success"
        if suppressed_count > 0 and not active_intents:
            status = "suppressed"

        # Log completion
        logger.info(
            f"Executed vectorized signals for strategy: {strategy_ref.strategy_id}",
            extra={
                "strategy_id": strategy_ref.strategy_id,
                "version": strategy_class.version,
                "status": status,
                "intents_emitted": len(active_intents),
                "intents_suppressed": suppressed_count,
            },
        )

        return {
            "status": "success",
            "message": "Vectorized signal generation completed.",
            "data": {
                "trade_intents": active_intents,
                "diagnostics": {
                    "strategy_id": strategy_ref.strategy_id,
                    "strategy_version": strategy_class.version,
                    "request_id": request_id or "",
                    "correlation_id": correlation_id or "",
                    "decision_timestamp": decision_ts,
                    "status": status,
                    "details": details,
                    "redaction_status": "not_required",
                },
            },
            "error": None,
            "metadata": {
                "request_id": request_id,
                "correlation_id": correlation_id,
            },
        }

    except Exception as exc:
        mapped = map_exception_to_strategy_error(exc)
        logger.error(
            f"Vectorized execution failed: {exc}",
            extra={
                "strategy_id": strategy_ref.strategy_id,
                "error_code": mapped.code,
            },
        )
        return {
            "status": "error",
            "message": f"Execution failed: {exc}",
            "data": None,
            "error": {
                "code": mapped.code,
                "details": str(exc),
            },
            "metadata": {
                "request_id": request_id,
                "correlation_id": correlation_id,
            },
        }
