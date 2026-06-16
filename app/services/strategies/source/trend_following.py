# ruff: noqa: ARG002, ANN401
"""Trend Following Strategy implementation.

Provides technical indicator calculation, lookback shifting, and signal generation
following fast/slow EMA crossovers with long-term trend filter confirmation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, ClassVar, Literal

import pandas as pd

from app.services.strategies.base import BaseStrategy
from app.services.strategies.protocols import (
    ReadOnlyExecutionStateSnapshot,
    StrategyEnvironment,
    StrategyExecutionContext,
    StrategyRiskProfile,
    TradeIntent,
)
from app.utils.errors import StrategyConfigError
from app.utils.logger import logger


class TrendFollowingStrategy(BaseStrategy):
    """Trend Following Strategy using EMA crossovers and trend filter confirmation.

    Conforms structurally to StrategyProtocol.
    """

    strategy_id: ClassVar[str] = "trend_following"
    version: ClassVar[str] = "1.0.0"
    lifecycle_status: ClassVar[str] = "RESEARCH"
    permitted_environments: ClassVar[list[StrategyEnvironment]] = ["BACKTEST", "REPLAY"]
    config_schema: ClassVar[dict[str, Any] | None] = {
        "title": "TrendFollowingConfig",
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "default": "UNKNOWN",
                "description": "The ticker symbol to trade.",
            },
            "fast_period": {
                "type": "integer",
                "minimum": 1,
                "maximum": 100,
                "step": 1,
                "default": 20,
                "description": "The period for the fast EMA.",
            },
            "slow_period": {
                "type": "integer",
                "minimum": 1,
                "maximum": 250,
                "step": 1,
                "default": 50,
                "description": "The period for the slow EMA.",
            },
            "filter_period": {
                "type": "integer",
                "minimum": 1,
                "maximum": 500,
                "step": 1,
                "default": 200,
                "description": "The period for the trend filter EMA.",
            },
        },
        "required": ["symbol", "fast_period", "slow_period", "filter_period"],
    }
    config_model: ClassVar[type[Any] | None] = None
    risk_profile: ClassVar[StrategyRiskProfile | None] = None
    max_data_latency_tolerance: ClassVar[pd.Timedelta] = pd.Timedelta(hours=2)

    def on_init(
        self, context: StrategyExecutionContext, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Initialize and validate parameters according to config schema.

        Args:
            context: Operational context during strategy execution.
            config: Dictionary containing the configuration parameters.

        Returns:
            A dictionary containing optional state_updates and trade_intents.
        """
        fast = config.get("fast_period", 20)
        slow = config.get("slow_period", 50)
        symbol = config.get("symbol", "UNKNOWN")
        filter_period = config.get("filter_period", 200)

        if fast >= slow:
            raise StrategyConfigError(
                "fast_period must be strictly less than slow_period"
            )

        logger.info(
            f"Initialized TrendFollowingStrategy for symbol {symbol} with "
            f"fast_period={fast}, slow_period={slow}, "
            f"filter_period={filter_period}"
        )
        return {"state_updates": {}, "trade_intents": []}

    def _calculate_indicators(
        self, data: pd.DataFrame, config: dict[str, Any]
    ) -> pd.DataFrame:
        """Calculate exponential moving averages for the configured periods.

        Args:
            data: Market data DataFrame.
            config: Validated configuration dict.

        Returns:
            DataFrame with indicator columns added.
        """
        df = data.copy()
        df["fast_ema"] = (
            df["close"].ewm(span=config["fast_period"], adjust=False).mean()
        )
        df["slow_ema"] = (
            df["close"].ewm(span=config["slow_period"], adjust=False).mean()
        )
        df["filter_ema"] = (
            df["close"].ewm(span=config["filter_period"], adjust=False).mean()
        )
        return df

    def _shift_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Shift computed EMAs to prevent lookahead and detect crossover points.

        Args:
            data: DataFrame with computed EMAs.

        Returns:
            DataFrame with shifted signal and previous signal columns.
        """
        df = data.copy()
        df["fast_signal"] = df["fast_ema"].shift(1)
        df["slow_signal"] = df["slow_ema"].shift(1)
        df["filter_signal"] = df["filter_ema"].shift(1)
        df["prev_fast_signal"] = df["fast_signal"].shift(1)
        df["prev_slow_signal"] = df["slow_signal"].shift(1)
        return df

    def _ensure_signal_columns(self, data: pd.DataFrame) -> pd.DataFrame:
        """Initialize signal and diagnostic columns with defaults.

        Args:
            data: Input DataFrame.

        Returns:
            DataFrame with signal columns initialized.
        """
        df = data.copy()
        df["entry_signal"] = 0
        df["exit_signal"] = 0
        df["price"] = 0.0
        df["reason"] = ""
        df["setup_id"] = ""
        df["group_id"] = ""
        return df

    def _generate_simple_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply crossover and filter conditions to generate entry and exit signals.

        Args:
            data: DataFrame with shifted features and signal columns.

        Returns:
            DataFrame with signals populated.
        """
        df = data.copy()
        for idx, row in df.iterrows():
            fast_sig = row["fast_signal"]
            slow_sig = row["slow_signal"]
            filter_sig = row["filter_signal"]
            prev_fast_sig = row["prev_fast_signal"]
            prev_slow_sig = row["prev_slow_signal"]

            # Skip checking if there are not enough bars for shift
            if pd.isna(prev_fast_sig) or pd.isna(prev_slow_sig):
                continue

            bullish_cross = (fast_sig > slow_sig) and (prev_fast_sig <= prev_slow_sig)
            bearish_cross = (fast_sig < slow_sig) and (prev_fast_sig >= prev_slow_sig)

            buy_condition = bullish_cross and (slow_sig > filter_sig)
            sell_condition = bearish_cross and (slow_sig < filter_sig)

            # Exit logic
            if bullish_cross:
                df.loc[idx, "exit_signal"] = -1
                df.loc[idx, "price"] = row["open"]
                df.loc[idx, "reason"] = "Bullish EMA crossover exit"
            elif bearish_cross:
                df.loc[idx, "exit_signal"] = 1
                df.loc[idx, "price"] = row["open"]
                df.loc[idx, "reason"] = "Bearish EMA crossover exit"

            # Entry logic
            if buy_condition:
                df.loc[idx, "entry_signal"] = 1
                df.loc[idx, "price"] = row["open"]
                df.loc[idx, "reason"] = (
                    "EMA fast crossed above EMA slow with trend filter confirmation"
                )
                df.loc[idx, "setup_id"] = "ema_trend_buy"
                df.loc[idx, "group_id"] = "ema_trend_buy"
            elif sell_condition:
                df.loc[idx, "entry_signal"] = -1
                df.loc[idx, "price"] = row["open"]
                df.loc[idx, "reason"] = (
                    "EMA fast crossed below EMA slow with trend filter confirmation"
                )
                df.loc[idx, "setup_id"] = "ema_trend_sell"
                df.loc[idx, "group_id"] = "ema_trend_sell"

        return df

    def on_bar(
        self,
        bar: Any,
        indicators: Any = None,
        read_only_state: ReadOnlyExecutionStateSnapshot | None = None,
        context: StrategyExecutionContext | None = None,
        config: Any = None,
    ) -> Any:
        """Process either a batch DataFrame of prices or a single closed bar event.

        Args:
            bar: Either a pd.DataFrame (batch data) or a dict containing a single bar.
            indicators: Composed indicators DataFrame or dict.
            read_only_state: Read-only access to fills and open positions.
            context: The strategy execution context.
            config: The validated strategy configuration dictionary.

        Returns:
            If bar is a DataFrame, returns the calculated DataFrame.
            If bar is a dict, returns a dictionary containing
            trade_intents and state_updates.
        """
        if isinstance(bar, pd.DataFrame):
            cfg_dict = config if config is not None else {}
            df = bar.copy()
            df = self._calculate_indicators(df, cfg_dict)
            df = self._shift_features(df)
            df = self._ensure_signal_columns(df)
            df = self._generate_simple_signals(df)
            return df

        # Event-driven single bar hook execution
        cfg_dict = config if config is not None else {}
        df = pd.DataFrame([bar])
        if "timestamp" in bar:
            df.index = pd.DatetimeIndex([bar["timestamp"]])

        df = self._calculate_indicators(df, cfg_dict)
        df = self._shift_features(df)
        df = self._ensure_signal_columns(df)
        df = self._generate_simple_signals(df)

        intents = []
        for idx, row in df.iterrows():
            entry_sig = row["entry_signal"]
            exit_sig = row["exit_signal"]
            if entry_sig == 0 and exit_sig == 0:
                continue

            dt = datetime.now(UTC)
            if context is not None:
                dt = context.decision_timestamp

            ts = idx if isinstance(idx, pd.Timestamp) else dt
            sig_ts = ts - pd.Timedelta(hours=1)

            if entry_sig != 0:
                side: Literal["BUY", "SELL", "HOLD"] = (
                    "BUY" if entry_sig > 0 else "SELL"
                )
                intent_type: Literal["OPEN", "CLOSE"] = "OPEN"
                reason = row["reason"]
                setup_id = row["setup_id"]
            else:
                side = "SELL" if exit_sig > 0 else "BUY"
                intent_type = "CLOSE"
                reason = row["reason"]
                setup_id = "ema_trend_exit"

            intents.append(
                TradeIntent(
                    intent_id=f"intent-{self.strategy_id}-{ts.strftime('%Y%m%d%H%M%S')}",
                    decision_id=f"decision-{self.strategy_id}-{ts.strftime('%Y%m%d%H%M%S')}",
                    idempotency_key=f"idem-{self.strategy_id}-{ts.strftime('%Y%m%d%H%M%S')}",
                    strategy_id=self.strategy_id,
                    strategy_version=self.version,
                    symbol=cfg_dict.get("symbol", "UNKNOWN"),
                    side=side,
                    intent_type=intent_type,
                    signal_timestamp=sig_ts,
                    decision_timestamp=dt,
                    rationale_ref=reason,
                    lineage={"setup_id": setup_id, "group_id": setup_id},
                )
            )

        return {"state_updates": {}, "trade_intents": intents}

    def run_vectorized_signals(
        self,
        data: pd.DataFrame,
        indicators: pd.DataFrame,
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> list[TradeIntent]:
        """Conform to StrategyProtocol for signal calculation.

        Args:
            data: Raw market data DataFrame.
            indicators: Shifted indicators DataFrame (provided by vectorized runner).
            context: Strategy execution context.
            config: Configuration dictionary.

        Returns:
            List of generated TradeIntent objects.
        """
        self.on_init(context, config)
        calculated_df = self.on_bar(data, config=config)

        intents = []
        for idx, row in calculated_df.iterrows():
            entry_sig = row["entry_signal"]
            exit_sig = row["exit_signal"]

            if entry_sig == 0 and exit_sig == 0:
                continue

            ts = idx if isinstance(idx, pd.Timestamp) else idx[1]

            # Determine previous bar timestamp to prevent lookahead
            if isinstance(calculated_df.index, pd.MultiIndex):
                ts_values = calculated_df.index.get_level_values("timestamp")
            else:
                ts_values = calculated_df.index

            sig_ts = ts
            if len(ts_values) > 1:
                time_diff = ts_values[1] - ts_values[0]
                sig_ts = ts - time_diff
            else:
                sig_ts = ts - pd.Timedelta(hours=1)

            if entry_sig != 0:
                side: Literal["BUY", "SELL", "HOLD"] = (
                    "BUY" if entry_sig > 0 else "SELL"
                )
                intent_type: Literal["OPEN", "CLOSE"] = "OPEN"
                reason = row["reason"]
                setup_id = row["setup_id"]
            else:
                side = "SELL" if exit_sig > 0 else "BUY"
                intent_type = "CLOSE"
                reason = row["reason"]
                setup_id = "ema_trend_exit"

            intents.append(
                TradeIntent(
                    intent_id=f"intent-{self.strategy_id}-{ts.strftime('%Y%m%d%H%M%S')}",
                    decision_id=f"decision-{self.strategy_id}-{ts.strftime('%Y%m%d%H%M%S')}",
                    idempotency_key=f"idem-{self.strategy_id}-{ts.strftime('%Y%m%d%H%M%S')}",
                    strategy_id=self.strategy_id,
                    strategy_version=self.version,
                    symbol=config.get("symbol", "UNKNOWN"),
                    side=side,
                    intent_type=intent_type,
                    signal_timestamp=sig_ts,
                    decision_timestamp=ts,
                    rationale_ref=reason,
                    lineage={"setup_id": setup_id, "group_id": setup_id},
                )
            )

        return intents
