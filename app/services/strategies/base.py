# ruff: noqa: ARG002
"""Abstract Base Class (ABC) for all quantitative trading strategies.

Provides default fields, parameter initialization validation, and structural
contracts ensuring protocol compliance for both batch/vectorized and hook-based
event-driven strategies.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

import pandas as pd

if TYPE_CHECKING:
    from app.services.strategies.protocols import (
        ReadOnlyExecutionStateSnapshot,
        StrategyEnvironment,
        StrategyExecutionContext,
        StrategyRiskProfile,
        TradeIntent,
    )


class BaseStrategy(ABC):
    """Abstract base class for all trading strategies.

    Provides core defaults and enforce interface contracts.
    """

    strategy_id: ClassVar[str] = "base_strategy"
    version: ClassVar[str] = "1.0.0"
    lifecycle_status: ClassVar[str] = "DRAFT"
    permitted_environments: ClassVar[list[StrategyEnvironment]] = ["BACKTEST"]
    config_schema: ClassVar[dict[str, Any] | None] = None
    config_model: ClassVar[type[Any] | None] = None
    risk_profile: ClassVar[StrategyRiskProfile | None] = None
    max_data_latency_tolerance: ClassVar[pd.Timedelta] = pd.Timedelta(hours=2)

    @abstractmethod
    def run_vectorized_signals(
        self,
        data: pd.DataFrame,
        indicators: pd.DataFrame,
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> list[TradeIntent]:
        """Compute signals across a batch DataFrame and return TradeIntent list.

        Args:
            data: Market data DataFrame.
            indicators: Calculated indicators DataFrame.
            context: Strategy execution context.
            config: Validated configuration parameters.

        Returns:
            List of generated TradeIntent objects.
        """

    def on_init(
        self, context: StrategyExecutionContext, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Optional lifecycle hook called on strategy initialization.

        Args:
            context: The strategy execution context.
            config: The validated strategy configuration dictionary.

        Returns:
            A dictionary containing optional state_updates and trade_intents.
        """
        return {"state_updates": {}, "trade_intents": []}

    def on_bar(
        self,
        bar: dict[str, Any],
        indicators: dict[str, Any],
        read_only_state: ReadOnlyExecutionStateSnapshot | None,
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Optional lifecycle hook called on closed bar events.

        Args:
            bar: Dictionary containing details of the new closed bar.
            indicators: Calculated indicators for the bar.
            read_only_state: Read-only access to fills and open positions.
            context: The strategy execution context.
            config: The validated strategy configuration dictionary.

        Returns:
            A dictionary containing optional state_updates and trade_intents.
        """
        return {"state_updates": {}, "trade_intents": []}

    def on_tick(
        self,
        tick: dict[str, Any],
        read_only_state: ReadOnlyExecutionStateSnapshot | None,
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Optional lifecycle hook called on new price ticks.

        Args:
            tick: Dictionary containing price tick details.
            read_only_state: Read-only access to fills and open positions.
            context: The strategy execution context.
            config: The validated strategy configuration dictionary.

        Returns:
            A dictionary containing optional state_updates and trade_intents.
        """
        return {"state_updates": {}, "trade_intents": []}

    def on_fill_update(
        self,
        fill_event: dict[str, Any],
        read_only_state: ReadOnlyExecutionStateSnapshot | None,
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Optional lifecycle hook called on deal fills/partial fills.

        Args:
            fill_event: Details of the filled deal.
            read_only_state: Read-only access to fills and open positions.
            context: The strategy execution context.
            config: The validated strategy configuration dictionary.

        Returns:
            A dictionary containing optional state_updates and trade_intents.
        """
        return {"state_updates": {}, "trade_intents": []}

    def on_partial_fill(
        self,
        fill_event: dict[str, Any],
        read_only_state: ReadOnlyExecutionStateSnapshot | None,
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Optional lifecycle hook called on partial fill events.

        Args:
            fill_event: Details of the partially filled deal.
            read_only_state: Read-only access to fills and open positions.
            context: The strategy execution context.
            config: The validated strategy configuration dictionary.

        Returns:
            A dictionary containing optional state_updates and trade_intents.
        """
        return {"state_updates": {}, "trade_intents": []}

    def on_order_update(
        self,
        order_event: dict[str, Any],
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Optional lifecycle hook called on order updates.

        Args:
            order_event: Details of the order update.
            context: The strategy execution context.
            config: The validated strategy configuration dictionary.

        Returns:
            A dictionary containing optional state_updates and trade_intents.
        """
        return {"state_updates": {}, "trade_intents": []}

    def on_timer(
        self,
        timer_event: dict[str, Any],
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Optional lifecycle hook called on timer triggers.

        Args:
            timer_event: Details of the timer trigger event.
            context: The strategy execution context.
            config: The validated strategy configuration dictionary.

        Returns:
            A dictionary containing optional state_updates and trade_intents.
        """
        return {"state_updates": {}, "trade_intents": []}

    def on_error(
        self,
        error_event: dict[str, Any],
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Optional lifecycle hook called when an error is caught.

        Args:
            error_event: Details of the encountered error.
            context: The strategy execution context.
            config: The validated strategy configuration dictionary.

        Returns:
            A dictionary containing optional state_updates and trade_intents.
        """
        return {"state_updates": {}, "trade_intents": []}

    def on_checkpoint(
        self, context: StrategyExecutionContext, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Optional lifecycle hook called before creating a state checkpoint.

        Args:
            context: The strategy execution context.
            config: The validated strategy configuration dictionary.

        Returns:
            A dictionary containing optional state_updates and trade_intents.
        """
        return {"state_updates": {}, "trade_intents": []}

    def on_restore(
        self,
        checkpoint_data: dict[str, Any],
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> dict[str, Any]:
        """Optional lifecycle hook called when restoring from a checkpoint.

        Args:
            checkpoint_data: The restored checkpoint payload.
            context: The strategy execution context.
            config: The validated strategy configuration dictionary.

        Returns:
            A dictionary containing optional state_updates and trade_intents.
        """
        return {"state_updates": {}, "trade_intents": []}

    def on_stop(
        self, context: StrategyExecutionContext, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Optional lifecycle hook called when the strategy is stopped.

        Args:
            context: The strategy execution context.
            config: The validated strategy configuration dictionary.

        Returns:
            A dictionary containing optional state_updates and trade_intents.
        """
        return {"state_updates": {}, "trade_intents": []}
