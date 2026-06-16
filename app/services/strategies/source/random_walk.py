# ruff: noqa: ARG002, ANN401, C901, PLR0912, PLR0915
"""RandomWalk EA quantitative strategy implementation.

Provides scaling order grids with simulated position lifetime checks
for vectorized execution, and live position checks for event-driven ticks.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, ClassVar

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

_MAX_DECIMAL_PLACES: int = 10


class RandomWalkStrategy(BaseStrategy):
    """RandomWalk strategy using buy/sell scaling grids.

    Grid checks are based on active position counts.
    """

    strategy_id: ClassVar[str] = "random_walk"
    version: ClassVar[str] = "1.0.0"
    lifecycle_status: ClassVar[str] = "RESEARCH"
    permitted_environments: ClassVar[list[StrategyEnvironment]] = [
        "BACKTEST",
        "REPLAY",
    ]
    config_schema: ClassVar[dict[str, Any] | None] = {
        "title": "RandomWalkConfig",
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "default": "EURUSD",
                "description": "The ticker symbol to trade.",
            },
            "timeframe": {
                "type": "string",
                "default": "5m",
                "description": "The strategy execution timeframe.",
            },
            "sell_magic": {
                "type": "integer",
                "default": 2134,
                "description": "Magic number for sell orders.",
            },
            "buy_magic": {
                "type": "integer",
                "default": 2323,
                "description": "Magic number for buy orders.",
            },
            "max_slippage": {
                "type": "integer",
                "default": 1,
                "description": "Max acceptable slippage deviation in pips/points.",
            },
            "take_profit": {
                "type": "number",
                "minimum": 0.0,
                "default": 20.0,
                "description": "Take profit target in pips.",
            },
            "stop_loss": {
                "type": "number",
                "minimum": 0.0,
                "default": 10.0,
                "description": "Stop loss target in pips.",
            },
            "total_volume": {
                "type": "number",
                "minimum": 0.0,
                "default": 0.3,
                "description": "Total allocated trading volume.",
            },
            "volume_per_trade": {
                "type": "number",
                "minimum": 0.0,
                "default": 0.02,
                "description": "Volume size per individual order.",
            },
            "point_size": {
                "type": "number",
                "minimum": 0.0,
                "default": 0.00001,
                "description": "Point size multiplier (EURUSD default 0.00001).",
            },
        },
        "required": [
            "symbol",
            "timeframe",
            "sell_magic",
            "buy_magic",
            "max_slippage",
            "take_profit",
            "stop_loss",
            "total_volume",
            "volume_per_trade",
            "point_size",
        ],
    }
    config_model: ClassVar[type[Any] | None] = None
    risk_profile: ClassVar[StrategyRiskProfile | None] = None
    max_data_latency_tolerance: ClassVar[pd.Timedelta] = pd.Timedelta(hours=2)

    def __init__(self) -> None:
        """Initialize strategy state variables."""
        self._old_num_bars: int = 0

    def on_init(
        self, context: StrategyExecutionContext, config: dict[str, Any]
    ) -> dict[str, Any]:
        """Validate input parameters and initialize chart visuals logs.

        Args:
            context: Operational context during strategy execution.
            config: Dictionary containing the configuration parameters.

        Returns:
            A dictionary containing state_updates and trade_intents.
        """
        total_vol = config.get("total_volume", 0.3)
        trade_vol = config.get("volume_per_trade", 0.02)

        if total_vol <= 0 or trade_vol <= 0:
            raise StrategyConfigError(
                "INVALID VOLUME VALUES: total_volume and "
                "volume_per_trade must be positive."
            )

        if trade_vol > total_vol:
            raise StrategyConfigError(
                "INVALID VOLUME VALUES: volume_per_trade cannot exceed total_volume."
            )

        logger.info(
            "RandomWalkStrategy chart visuals configured: black background, green bull."
        )
        return {"state_updates": {}, "trade_intents": []}

    def _count_active_buys(
        self,
        read_only_state: ReadOnlyExecutionStateSnapshot | None,
        symbol: str,
        buy_magic: int,
    ) -> int:
        """Count active Buy positions matching symbol and magic number.

        Args:
            read_only_state: Read-only access to open positions state.
            symbol: Target trade symbol.
            buy_magic: Magic identifier for buy trades.

        Returns:
            Count of matching active buy positions.
        """
        if not read_only_state or not read_only_state.open_positions:
            return 0

        count = 0
        for pos in read_only_state.open_positions:
            pos_symbol = pos.get("symbol", "")
            pos_magic = pos.get("magic") or pos.get("magic_number")
            pos_side = pos.get("side")
            pos_type = pos.get("type")

            if (
                pos_symbol == symbol
                and pos_magic == buy_magic
                and (pos_side == "BUY" or pos_type == 0 or pos_side is None)
            ):
                count += 1
        return count

    def _count_active_sells(
        self,
        read_only_state: ReadOnlyExecutionStateSnapshot | None,
        symbol: str,
        sell_magic: int,
    ) -> int:
        """Count active Sell positions matching symbol and magic number.

        Args:
            read_only_state: Read-only access to open positions state.
            symbol: Target trade symbol.
            sell_magic: Magic identifier for sell trades.

        Returns:
            Count of matching active sell positions.
        """
        if not read_only_state or not read_only_state.open_positions:
            return 0

        count = 0
        for pos in read_only_state.open_positions:
            pos_symbol = pos.get("symbol", "")
            pos_magic = pos.get("magic") or pos.get("magic_number")
            pos_side = pos.get("side")
            pos_type = pos.get("type")

            if (
                pos_symbol == symbol
                and pos_magic == sell_magic
                and (pos_side == "SELL" or pos_type == 1 or pos_side is None)
            ):
                count += 1
        return count

    def on_bar(
        self,
        bar: Any,
        indicators: Any = None,
        read_only_state: ReadOnlyExecutionStateSnapshot | None = None,
        context: StrategyExecutionContext | None = None,
        config: Any = None,
    ) -> Any:
        """Process event-driven single closed bar events.

        Args:
            bar: Dictionary containing details of the new closed bar.
            indicators: Calculated indicators for the bar.
            read_only_state: Read-only access to fills and open positions.
            context: The strategy execution context.
            config: The validated strategy configuration dictionary.

        Returns:
            A dictionary containing optional state_updates and trade_intents.
        """
        cfg_dict = config if config is not None else {}
        symbol = cfg_dict.get("symbol", "EURUSD")
        buy_magic = cfg_dict.get("buy_magic", 2323)
        sell_magic = cfg_dict.get("sell_magic", 2134)
        vol_per_trade = cfg_dict.get("volume_per_trade", 0.02)
        total_vol = cfg_dict.get("total_volume", 0.3)
        sl_pips = cfg_dict.get("stop_loss", 10.0)
        tp_pips = cfg_dict.get("take_profit", 20.0)
        point_size = cfg_dict.get("point_size", 0.00001)

        dt = datetime.now(UTC)
        if context is not None:
            dt = context.decision_timestamp

        ts_str = dt.strftime("%Y%m%d%H%M%S")
        sig_ts = dt - pd.Timedelta(minutes=5)

        stp = sl_pips * 10 * point_size
        tkp = tp_pips * 10 * point_size
        num_trades = round(total_vol / vol_per_trade)

        ask_price = float(bar.get("close", bar.get("open", 0.0)))
        bid_price = float(bar.get("close", bar.get("open", 0.0)))

        # Determine rounding decimal places from point_size
        decimals = 0
        ps = point_size
        while ps < 1.0 and decimals < _MAX_DECIMAL_PLACES:
            ps *= 10
            decimals += 1

        intents = []

        # 1. Execute Buy Grid
        active_buys = self._count_active_buys(read_only_state, symbol, buy_magic)
        if active_buys == 0:
            multiplier = 1
            for i in range(num_trades):
                target_sl = round(ask_price - (stp * multiplier), decimals)
                target_tp = round(ask_price + (tkp * multiplier), decimals)

                rationale = f"Scaling BUY order grid element {i + 1} of {num_trades}"
                intents.append(
                    TradeIntent(
                        intent_id=f"intent-rw-{ts_str}-BUY-{i}",
                        decision_id=f"decision-rw-{ts_str}-BUY-{i}",
                        idempotency_key=f"idem-rw-{ts_str}-BUY-{i}",
                        strategy_id=self.strategy_id,
                        strategy_version=self.version,
                        symbol=symbol,
                        side="BUY",
                        intent_type="OPEN",
                        quantity_hint=Decimal(str(vol_per_trade)),
                        signal_timestamp=sig_ts,
                        decision_timestamp=dt,
                        stop_loss=Decimal(str(target_sl)),
                        take_profit=Decimal(str(target_tp)),
                        rationale_ref=rationale,
                        lineage={"magic": str(buy_magic), "element_index": str(i)},
                    )
                )
                multiplier += 1

        # 2. Execute Sell Grid
        active_sells = self._count_active_sells(read_only_state, symbol, sell_magic)
        if active_sells == 0:
            multiplier = 1
            for i in range(num_trades):
                target_sl = round(bid_price + (stp * multiplier), decimals)
                target_tp = round(bid_price - (tkp * multiplier), decimals)

                rationale = f"Scaling SELL order grid element {i + 1} of {num_trades}"
                intents.append(
                    TradeIntent(
                        intent_id=f"intent-rw-{ts_str}-SELL-{i}",
                        decision_id=f"decision-rw-{ts_str}-SELL-{i}",
                        idempotency_key=f"idem-rw-{ts_str}-SELL-{i}",
                        strategy_id=self.strategy_id,
                        strategy_version=self.version,
                        symbol=symbol,
                        side="SELL",
                        intent_type="OPEN",
                        quantity_hint=Decimal(str(vol_per_trade)),
                        signal_timestamp=sig_ts,
                        decision_timestamp=dt,
                        stop_loss=Decimal(str(target_sl)),
                        take_profit=Decimal(str(target_tp)),
                        rationale_ref=rationale,
                        lineage={"magic": str(sell_magic), "element_index": str(i)},
                    )
                )
                multiplier += 1

        return {"state_updates": {}, "trade_intents": intents}

    def run_vectorized_signals(
        self,
        data: pd.DataFrame,
        indicators: pd.DataFrame,
        context: StrategyExecutionContext,
        config: dict[str, Any],
    ) -> list[TradeIntent]:
        """Perform chronological simulation of scaling grids across historical bars.

        Args:
            data: Raw market data DataFrame.
            indicators: Shifted indicators DataFrame.
            context: Strategy execution context.
            config: Validated configuration parameters.

        Returns:
            List of generated TradeIntent objects.
        """
        self.on_init(context, config)

        symbol = config.get("symbol", "EURUSD")
        buy_magic = config.get("buy_magic", 2323)
        sell_magic = config.get("sell_magic", 2134)
        vol_per_trade = config.get("volume_per_trade", 0.02)
        total_vol = config.get("total_volume", 0.3)
        sl_pips = config.get("stop_loss", 10.0)
        tp_pips = config.get("take_profit", 20.0)
        point_size = config.get("point_size", 0.00001)

        stp = sl_pips * 10 * point_size
        tkp = tp_pips * 10 * point_size
        num_trades = round(total_vol / vol_per_trade)

        # Determine rounding decimal places from point_size
        decimals = 0
        ps = point_size
        while ps < 1.0 and decimals < _MAX_DECIMAL_PLACES:
            ps *= 10
            decimals += 1

        active_buys: list[dict[str, float]] = []
        active_sells: list[dict[str, float]] = []

        all_intents = []

        # Walk through the DataFrame chronologically
        for idx, row in data.iterrows():
            ts = idx if isinstance(idx, pd.Timestamp) else idx[1]
            open_price = float(row["open"])
            high_price = float(row["high"])
            low_price = float(row["low"])

            # 1. Update/check existing simulated position exits on this bar
            remaining_buys = []
            for pos in active_buys:
                if low_price <= pos["sl"]:
                    continue
                if high_price >= pos["tp"]:
                    continue
                remaining_buys.append(pos)
            active_buys = remaining_buys

            remaining_sells = []
            for pos in active_sells:
                if high_price >= pos["sl"]:
                    continue
                if low_price <= pos["tp"]:
                    continue
                remaining_sells.append(pos)
            active_sells = remaining_sells

            ts_str = ts.strftime("%Y%m%d%H%M%S")

            if len(data.index) > 1:
                if isinstance(data.index, pd.MultiIndex):
                    ts_vals = data.index.get_level_values("timestamp")
                else:
                    ts_vals = data.index
                time_diff = ts_vals[1] - ts_vals[0]
                sig_ts = ts - time_diff
            else:
                sig_ts = ts - pd.Timedelta(minutes=5)

            # 2. Check and execute buy grid
            if len(active_buys) == 0:
                multiplier = 1
                for i in range(num_trades):
                    target_sl = round(open_price - (stp * multiplier), decimals)
                    target_tp = round(open_price + (tkp * multiplier), decimals)

                    active_buys.append({"sl": target_sl, "tp": target_tp})

                    rationale = (
                        f"Scaling BUY order grid element {i + 1} of {num_trades}"
                    )
                    all_intents.append(
                        TradeIntent(
                            intent_id=f"intent-rw-{ts_str}-BUY-{i}",
                            decision_id=f"decision-rw-{ts_str}-BUY-{i}",
                            idempotency_key=f"idem-rw-{ts_str}-BUY-{i}",
                            strategy_id=self.strategy_id,
                            strategy_version=self.version,
                            symbol=symbol,
                            side="BUY",
                            intent_type="OPEN",
                            quantity_hint=Decimal(str(vol_per_trade)),
                            signal_timestamp=sig_ts,
                            decision_timestamp=ts,
                            stop_loss=Decimal(str(target_sl)),
                            take_profit=Decimal(str(target_tp)),
                            rationale_ref=rationale,
                            lineage={"magic": str(buy_magic), "element_index": str(i)},
                        )
                    )
                    multiplier += 1

            # 3. Check and execute sell grid
            if len(active_sells) == 0:
                multiplier = 1
                for i in range(num_trades):
                    target_sl = round(open_price + (stp * multiplier), decimals)
                    target_tp = round(open_price - (tkp * multiplier), decimals)

                    active_sells.append({"sl": target_sl, "tp": target_tp})

                    rationale = (
                        f"Scaling SELL order grid element {i + 1} of {num_trades}"
                    )
                    all_intents.append(
                        TradeIntent(
                            intent_id=f"intent-rw-{ts_str}-SELL-{i}",
                            decision_id=f"decision-rw-{ts_str}-SELL-{i}",
                            idempotency_key=f"idem-rw-{ts_str}-SELL-{i}",
                            strategy_id=self.strategy_id,
                            strategy_version=self.version,
                            symbol=symbol,
                            side="SELL",
                            intent_type="OPEN",
                            quantity_hint=Decimal(str(vol_per_trade)),
                            signal_timestamp=sig_ts,
                            decision_timestamp=ts,
                            stop_loss=Decimal(str(target_sl)),
                            take_profit=Decimal(str(target_tp)),
                            rationale_ref=rationale,
                            lineage={"magic": str(sell_magic), "element_index": str(i)},
                        )
                    )
                    multiplier += 1

        return all_intents
