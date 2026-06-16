# ruff: noqa: E501, PD011, PLR2004, C901, PLR0912, PLR0915, BLE001
"""Feature flagging and canary-routing adapter for indicator execution."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import pandas as pd

from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.indicators.protocols import (
        IndicatorConfig,
        IndicatorContext,
        IndicatorResult,
    )


@dataclass(frozen=True)
class CanaryConfig:
    """Configuration constraints for feature-flagged canary routing.

    Attributes:
        enabled: If True, indicates canary evaluation is active.
        canary_indicator_id: Indicator ID of the new canary implementation.
        canary_parameters: Dict of parameters for the canary execution.
        target_actors: List of actors routed to canary (empty = all).
        target_workflows: List of workflows routed to canary (empty = all).
        target_symbols: List of symbols routed to canary (empty = all).
        target_requests: List of request IDs routed to canary (empty = all).
        select_canary_route: If True, official outputs use canary values.
    """

    enabled: bool = False
    canary_indicator_id: str = ""
    canary_parameters: dict[str, Any] = field(default_factory=dict)
    target_actors: list[str] = field(default_factory=list)
    target_workflows: list[str] = field(default_factory=list)
    target_symbols: list[str] = field(default_factory=list)
    target_requests: list[str] = field(default_factory=list)
    select_canary_route: bool = False


class CanaryComparisonRecord:
    """Stored record of a completed canary-routing execution comparison."""

    def __init__(
        self,
        request_id: str,
        baseline_id: str,
        canary_id: str,
        output_deltas: dict[str, float],
        tolerance_passed: bool,
        performance_delta_ms: float,
        rollback_recommended: bool,
    ) -> None:
        """Initialize the comparison audit record fields."""
        self.request_id = request_id
        self.baseline_id = baseline_id
        self.canary_id = canary_id
        self.output_deltas = output_deltas
        self.tolerance_passed = tolerance_passed
        self.performance_delta_ms = performance_delta_ms
        self.rollback_recommended = rollback_recommended


class CanaryRouter:
    """Engine matching incoming requests against canary rules and auditing deltas."""

    def __init__(self) -> None:
        """Initialize the thread-safe comparison logging list."""
        self.comparisons: list[CanaryComparisonRecord] = []

    def evaluate_and_route(
        self,
        data: pd.DataFrame,
        config: IndicatorConfig,
        context: IndicatorContext,
        canary_config: CanaryConfig,
        baseline_runner: Callable[..., IndicatorResult],
    ) -> IndicatorResult:
        """Evaluate matching rules, execute baseline/canary, compare, and route."""
        # 1. Verify routing activation
        match = True
        if not canary_config.enabled:
            match = False
        else:
            # Parse symbol details
            symbol = "UNKNOWN"
            if "symbol" in data.columns:
                symbol = str(data["symbol"].iloc[0])
            elif isinstance(data.index, pd.MultiIndex) and "symbol" in data.index.names:
                symbol = str(data.index.unique(level="symbol")[0])

            # Check matching lists
            if (
                canary_config.target_actors
                and context.actor not in canary_config.target_actors
            ):
                match = False
            if (
                canary_config.target_workflows
                and context.workflow not in canary_config.target_workflows
            ):
                match = False
            if (
                canary_config.target_symbols
                and symbol not in canary_config.target_symbols
            ):
                match = False
            if (
                canary_config.target_requests
                and context.request_id not in canary_config.target_requests
            ):
                match = False

        if not match:
            # Fallback directly to normal baseline workflow execution
            return baseline_runner(
                config.indicator_id,
                data,
                config.parameters,
                config.source_column,
                context=context,
                column_conflict_policy=config.column_conflict_policy,
                custom_output_columns=config.custom_output_columns,
                conflict_suffix=config.conflict_suffix,
            )

        # 2. Match hit! Run baseline first
        start_baseline = time.perf_counter()
        baseline_res = baseline_runner(
            config.indicator_id,
            data,
            config.parameters,
            config.source_column,
            context=context,
            column_conflict_policy=config.column_conflict_policy,
            custom_output_columns=config.custom_output_columns,
            conflict_suffix=config.conflict_suffix,
        )
        baseline_duration = (time.perf_counter() - start_baseline) * 1000.0

        # 3. Run canary implementation
        start_canary = time.perf_counter()
        try:
            canary_res = baseline_runner(
                canary_config.canary_indicator_id,
                data,
                canary_config.canary_parameters,
                config.source_column,
                context=context,
                column_conflict_policy=config.column_conflict_policy,
                custom_output_columns=config.custom_output_columns,
                conflict_suffix=config.conflict_suffix,
            )
            canary_duration = (time.perf_counter() - start_canary) * 1000.0
            canary_failed = False
            canary_error_msg = ""
        except Exception as exc:
            canary_duration = (time.perf_counter() - start_canary) * 1000.0
            canary_failed = True
            canary_error_msg = str(exc)

        # Compute performance delta
        perf_delta_ms = canary_duration - baseline_duration

        # 4. Compare outputs & evaluate tolerance
        output_deltas: dict[str, float] = {}
        tolerance_passed = True
        rollback_recommended = False

        if canary_failed:
            tolerance_passed = False
            rollback_recommended = True
            logger.warning(
                f"Canary execution failed: {canary_error_msg}. Rollback recommended.",
                extra={
                    "event_name": "canary_execution_failed",
                    "request_id": context.request_id,
                },
            )
        else:
            # Compare output numeric column shapes and values
            b_cols = [
                c
                for c in baseline_res.values.columns
                if c not in ("timestamp", "symbol", "available_at", "quality")
            ]
            c_cols = [
                c
                for c in canary_res.values.columns
                if c not in ("timestamp", "symbol", "available_at", "quality")
            ]

            if len(baseline_res.values) != len(canary_res.values):
                tolerance_passed = False
                rollback_recommended = True
                output_deltas["row_count_mismatch"] = float(
                    abs(len(baseline_res.values) - len(canary_res.values))
                )
            else:
                for col_idx, b_col in enumerate(b_cols):
                    if col_idx < len(c_cols):
                        c_col = c_cols[col_idx]
                        b_series = baseline_res.values[b_col]
                        c_series = canary_res.values[c_col]

                        # Element-wise delta computations
                        abs_diff = (b_series - c_series).abs()
                        max_abs = float(abs_diff.max())
                        output_deltas[f"{b_col}_vs_{c_col}_abs"] = max_abs

                        rel_diff = abs_diff / (b_series.abs() + 1e-15)
                        max_rel = float(rel_diff.max())
                        output_deltas[f"{b_col}_vs_{c_col}_rel"] = max_rel

                        # Apply golden tolerance validations
                        if max_abs > 1e-12 or max_rel > 1e-9:
                            tolerance_passed = False
                            rollback_recommended = True

        # Store comparison audit record
        record = CanaryComparisonRecord(
            request_id=context.request_id or "UNKNOWN",
            baseline_id=config.indicator_id,
            canary_id=canary_config.canary_indicator_id,
            output_deltas=output_deltas,
            tolerance_passed=tolerance_passed,
            performance_delta_ms=perf_delta_ms,
            rollback_recommended=rollback_recommended,
        )
        self.comparisons.append(record)

        logger.info(
            f"Canary comparison completed for {config.indicator_id} vs {canary_config.canary_indicator_id}",
            extra={
                "event_name": "canary_comparison",
                "request_id": context.request_id,
                "tolerance_passed": tolerance_passed,
                "performance_delta_ms": perf_delta_ms,
                "rollback_recommended": rollback_recommended,
                "output_deltas": output_deltas,
            },
        )

        if canary_config.select_canary_route and not canary_failed:
            return canary_res
        return baseline_res


# Global canary router instance
global_canary_router = CanaryRouter()
