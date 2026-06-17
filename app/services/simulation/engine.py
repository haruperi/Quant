# ruff: noqa
"""Event-driven execution engine for simulation.

Implements the central execution engine, managing order matching, position updates,
accounting invariants (balance, equity, margin), stopouts, and SL/TP hits.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from app.services.simulation.models import (
    FeeModel,
    LiquidityModel,
    MarginModel,
    SlippageModel,
    SpreadModel,
    SwapModel,
)
from app.utils.errors import SimulationError
from app.utils.logger import logger

if TYPE_CHECKING:
    from app.services.simulation.journal import Journal
    from app.services.simulation.validation.schema import SymbolSpec


class EventDrivenExecutionEngine:
    """Manages backtest execution state, processing ticks and updating account/positions."""

    def __init__(
        self,
        initial_balance: Decimal,
        account_currency: str = "USD",
        leverage: Decimal = Decimal("100.0"),
        stopout_level_pct: Decimal = Decimal("50.0"),
        hedging: bool = False,
        journal: Journal | None = None,
        spread_model: SpreadModel | None = None,
        slippage_model: SlippageModel | None = None,
        liquidity_model: LiquidityModel | None = None,
        fee_model: FeeModel | None = None,
        swap_model: SwapModel | None = None,
        margin_model: MarginModel | None = None,
    ) -> None:
        """Initialize simulation engine state."""
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.equity = initial_balance
        self.account_currency = account_currency
        self.leverage = leverage
        self.hedging = hedging
        self.journal = journal

        # Simulator models
        self.spread_model = spread_model or SpreadModel()
        self.slippage_model = slippage_model or SlippageModel()
        self.liquidity_model = liquidity_model or LiquidityModel()
        self.fee_model = fee_model or FeeModel()
        self.swap_model = swap_model or SwapModel()
        self.margin_model = margin_model or MarginModel(
            leverage=leverage, stopout_level_pct=stopout_level_pct
        )

        # State collections
        self.orders: dict[
            str, dict[str, Any]
        ] = {}  # Pending orders: order_id -> order_info
        self.positions: dict[
            str, dict[str, Any]
        ] = {}  # Open positions: position_id -> position_info
        self.deals: list[dict[str, Any]] = []  # Executed deal records
        self.history_orders: list[dict[str, Any]] = []  # Closed/cancelled orders

        self.margin = Decimal("0.0")
        self.free_margin = initial_balance
        self.margin_level: Decimal | None = None

        self.current_time: str | None = None
        self.last_tick: dict[str, Any] = {}
        self.order_counter = 0
        self.position_counter = 0
        self.deal_counter = 0

        # Equity curve tracking
        self.equity_curve: list[tuple[str, Decimal]] = []

    def get_next_order_id(self) -> str:
        """Generate a monotonic transaction order ID."""
        self.order_counter += 1
        return f"ORD_{self.order_counter:06d}"

    def get_next_position_id(self) -> str:
        """Generate a monotonic position ID."""
        self.position_counter += 1
        return f"POS_{self.position_counter:06d}"

    def get_next_deal_id(self) -> str:
        """Generate a monotonic deal ID."""
        self.deal_counter += 1
        return f"DEAL_{self.deal_counter:06d}"

    def process_tick(self, tick: dict[str, Any], symbol_spec: SymbolSpec) -> None:
        """Advance simulation clock, evaluate pending orders, check SL/TP and margins."""
        self.current_time = tick["time"]
        self.last_tick[tick["symbol"]] = tick

        # 1. Update active pegged pending orders
        self._update_pegged_orders(tick, symbol_spec)

        # 2. Update trailing stops on active positions
        self._update_trailing_stops(tick, symbol_spec)

        # 3. Update mark-to-market floating PnL and account equity
        self._update_accounting(symbol_spec)

        # 4. Check and enforce Stopout first (highest priority)
        if self._check_stopout(symbol_spec):
            # If stopout triggered, position closes occurred. Re-update accounting.
            self._update_accounting(symbol_spec)
            return

        # 5. Process SL / TP triggers on open positions
        self._process_sl_tp(tick, symbol_spec)

        # 6. Process pending order triggers
        self._process_pending_orders(tick, symbol_spec)

        # 7. Record equity snapshot
        if self.current_time is not None:
            if not self.equity_curve or self.equity_curve[-1][0] != self.current_time:
                self.equity_curve.append((self.current_time, self.equity))

    def _update_pegged_orders(
        self, tick: dict[str, Any], symbol_spec: SymbolSpec
    ) -> None:
        """Update price for pegged orders based on current Bid/Ask."""
        bid = Decimal(str(tick["bid"]))
        ask = Decimal(str(tick["ask"]))
        point = symbol_spec.point
        tick_sz = symbol_spec.tick_size

        for ord_id, order in self.orders.items():
            if order["symbol"] != tick["symbol"]:
                continue

            ref = order.get("pegged_ref")
            if not ref:
                continue

            offset_pts = Decimal(str(order.get("pegged_offset_points") or 0))

            if ref == "BID":
                ref_price = bid
            elif ref == "ASK":
                ref_price = ask
            elif ref == "MID":
                ref_price = (bid + ask) / Decimal("2.0")
            else:
                continue

            new_price = ref_price + (offset_pts * point)
            # Normalize to tick size
            new_price = (new_price / tick_sz).quantize(
                Decimal(1), rounding="ROUND_HALF_UP"
            ) * tick_sz

            old_price = Decimal(str(order["price"]))
            if new_price != old_price:
                order["price"] = new_price
                if self.journal:
                    self.journal.append_event(
                        "pegged_order_repriced",
                        {
                            "order_id": ord_id,
                            "old_price": float(old_price),
                            "new_price": float(new_price),
                            "time": self.current_time,
                        },
                    )

    def _update_trailing_stops(
        self, tick: dict[str, Any], symbol_spec: SymbolSpec
    ) -> None:
        """Update Stop Loss values for positions with active trailing stops."""
        bid = Decimal(str(tick["bid"]))
        ask = Decimal(str(tick["ask"]))
        point = symbol_spec.point
        curr_time = self.current_time

        for pos_id, pos in self.positions.items():
            if pos["symbol"] != tick["symbol"]:
                continue

            trail_pts = pos.get("trailing_stop_points")
            if not trail_pts or trail_pts <= 0:
                continue

            trail_dist = Decimal(str(trail_pts)) * point

            if pos["type"] == "BUY":
                highest_bid = pos.get("highest_bid")
                if highest_bid is None:
                    highest_bid = Decimal(str(pos["price"]))

                if bid > highest_bid:
                    pos["highest_bid"] = bid
                    new_sl = bid - trail_dist
                    current_sl = pos.get("sl")
                    if current_sl is None or new_sl > current_sl:
                        pos["sl"] = new_sl
                        if self.journal:
                            self.journal.append_event(
                                "trailing_stop_updated",
                                {
                                    "position_id": pos_id,
                                    "symbol": pos["symbol"],
                                    "new_sl": float(new_sl),
                                    "time": curr_time,
                                },
                            )
            else:  # SELL
                lowest_ask = pos.get("lowest_ask")
                if lowest_ask is None:
                    lowest_ask = Decimal(str(pos["price"]))

                if ask < lowest_ask:
                    pos["lowest_ask"] = ask
                    new_sl = ask + trail_dist
                    current_sl = pos.get("sl")
                    if current_sl is None or new_sl < current_sl:
                        pos["sl"] = new_sl
                        if self.journal:
                            self.journal.append_event(
                                "trailing_stop_updated",
                                {
                                    "position_id": pos_id,
                                    "symbol": pos["symbol"],
                                    "new_sl": float(new_sl),
                                    "time": curr_time,
                                },
                            )

    def _update_accounting(self, symbol_spec: SymbolSpec) -> None:
        """Recalculate floating profit/loss, equity, margin, free margin and margin level."""
        floating_pnl = Decimal("0.0")
        total_margin = Decimal("0.0")

        # Sum floating profit across active positions
        for _pos_id, pos in list(self.positions.items()):
            symbol = pos["symbol"]
            last_q = self.last_tick.get(symbol)
            if not last_q:
                continue

            vol = Decimal(str(pos["volume"]))
            open_p = Decimal(str(pos["price"]))
            contract_sz = symbol_spec.contract_size

            # Profit calculation direction
            # Buy: bid - open_price
            # Sell: open_price - ask
            if pos["type"] == "BUY":
                pnl = vol * contract_sz * (Decimal(str(last_q["bid"])) - open_p)
            else:
                pnl = vol * contract_sz * (open_p - Decimal(str(last_q["ask"])))

            pos["profit"] = pnl
            floating_pnl += pnl

            # Calculate margin required for this position
            pos_margin = self.margin_model.calculate_position_margin(
                volume=vol,
                entry_price=open_p,
                contract_size=contract_sz,
                asset_class=symbol_spec.asset_class,
            )
            pos["margin_required"] = pos_margin
            total_margin += pos_margin

        self.equity = self.balance + floating_pnl
        self.margin = total_margin
        self.free_margin = self.equity - self.margin
        self.margin_level = self.margin_model.calculate_margin_level(
            self.equity, self.margin
        )

        # Accounting invariant check
        if self.equity < 0:
            logger.warning(
                f"Negative equity detected: {self.equity}. Invariant warning.",
                extra={"event_name": "negative_equity"},
            )

    def _check_stopout(self, symbol_spec: SymbolSpec) -> bool:
        """Check if account margin level is at or below stopout percent and liquidate largest loser."""
        if not self.positions:
            return False

        if self.margin_model.evaluate_stopout(self.equity, self.margin):
            logger.warning(
                "Stopout level breached. Initiating position liquidation.",
                extra={"event_name": "stopout_triggered"},
            )
            # Find the largest losing position
            largest_loss_pos = None
            largest_loss = Decimal("0.0")

            for pos in self.positions.values():
                pnl = pos.get("profit", Decimal("0.0"))
                if pnl < largest_loss:
                    largest_loss = pnl
                    largest_loss_pos = pos

            if largest_loss_pos:
                # Close this position at current market price
                symbol = largest_loss_pos["symbol"]
                last_q = self.last_tick.get(symbol)
                if isinstance(last_q, dict) and self.current_time is not None:
                    close_price = (
                        last_q["bid"]
                        if largest_loss_pos["type"] == "BUY"
                        else last_q["ask"]
                    )
                    self._close_position(
                        pos_id=largest_loss_pos["id"],
                        close_price=Decimal(str(close_price)),
                        close_time=self.current_time,
                        symbol_spec=symbol_spec,
                        comment="Stopout liquidation",
                    )
                    if self.journal:
                        self.journal.append_event(
                            "stopout_liquidation",
                            {
                                "position_id": largest_loss_pos["id"],
                                "close_price": float(close_price),
                                "time": self.current_time,
                            },
                        )
                    return True
        return False

    def _process_sl_tp(self, tick: dict[str, Any], symbol_spec: SymbolSpec) -> None:
        """Verify and execute stop-loss or take-profit hits for positions."""
        curr_time = self.current_time
        if curr_time is None:
            return
        bid = Decimal(str(tick["bid"]))
        ask = Decimal(str(tick["ask"]))

        for pos_id, pos in list(self.positions.items()):
            if pos["symbol"] != tick["symbol"]:
                continue

            sl = pos.get("sl")
            tp = pos.get("tp")

            # Check Buy position
            if pos["type"] == "BUY":
                # Buy close is at Bid
                if sl is not None and sl > 0 and bid <= sl:
                    # SL hit
                    self._close_position(
                        pos_id, sl, curr_time, symbol_spec, "Stop Loss hit"
                    )
                elif tp is not None and tp > 0 and bid >= tp:
                    # TP hit
                    self._close_position(
                        pos_id, tp, curr_time, symbol_spec, "Take Profit hit"
                    )

            # Check Sell position
            elif pos["type"] == "SELL":
                # Sell close is at Ask
                if sl is not None and sl > 0 and ask >= sl:
                    # SL hit
                    self._close_position(
                        pos_id, sl, curr_time, symbol_spec, "Stop Loss hit"
                    )
                elif tp is not None and tp > 0 and ask <= tp:
                    # TP hit
                    self._close_position(
                        pos_id, tp, curr_time, symbol_spec, "Take Profit hit"
                    )

    def _process_pending_orders(
        self, tick: dict[str, Any], symbol_spec: SymbolSpec
    ) -> None:
        """Check if pending orders trigger prices are touched, and execute them."""
        bid = Decimal(str(tick["bid"]))
        ask = Decimal(str(tick["ask"]))

        for ord_id, order in list(self.orders.items()):
            if order["symbol"] != tick["symbol"]:
                continue

            trigger = False
            fill_price = Decimal("0.0")

            ot = order["type"]
            price_limit = Decimal(str(order["price"]))

            if ot == "BUY_LIMIT":
                # Triggered when ask <= limit_price
                if ask <= price_limit:
                    trigger = True
                    fill_price = ask
            elif ot == "BUY_STOP":
                # Triggered when ask >= stop_price
                if ask >= price_limit:
                    trigger = True
                    fill_price = ask
            elif ot == "SELL_LIMIT":
                # Triggered when bid >= limit_price
                if bid >= price_limit:
                    trigger = True
                    fill_price = bid
            elif ot == "SELL_STOP":
                # Triggered when bid <= stop_price
                if bid <= price_limit:
                    trigger = True
                    fill_price = bid
            elif ot == "BUY_STOP_LIMIT":
                # Triggered when ask >= stop_price, then activates pending BUY_LIMIT
                if ask >= price_limit:
                    limit_price = Decimal(str(order["stop_limit_price"]))
                    order["type"] = "BUY_LIMIT"
                    order["price"] = limit_price
                    if self.journal:
                        self.journal.append_event(
                            "stop_limit_activated",
                            {
                                "order_id": ord_id,
                                "type": "BUY_LIMIT",
                                "price": float(limit_price),
                                "time": self.current_time,
                            },
                        )
                    continue
            elif ot == "SELL_STOP_LIMIT":
                # Triggered when bid <= stop_price, then activates pending SELL_LIMIT
                if bid <= price_limit:
                    limit_price = Decimal(str(order["stop_limit_price"]))
                    order["type"] = "SELL_LIMIT"
                    order["price"] = limit_price
                    if self.journal:
                        self.journal.append_event(
                            "stop_limit_activated",
                            {
                                "order_id": ord_id,
                                "type": "SELL_LIMIT",
                                "price": float(limit_price),
                                "time": self.current_time,
                            },
                        )
                    continue

            if trigger:
                # Remove pending order and execute
                del self.orders[ord_id]
                order["status"] = "filled"
                self.history_orders.append(order)

                # Execute order fill
                self.execute_order(
                    symbol=order["symbol"],
                    direction="BUY" if ot.startswith("BUY") else "SELL",
                    volume=Decimal(str(order["volume"])),
                    price=fill_price,
                    sl=order.get("sl"),
                    tp=order.get("tp"),
                    symbol_spec=symbol_spec,
                    magic=order.get("magic", 0),
                    comment=order.get("comment", ""),
                    trailing_stop_points=order.get("trailing_stop_points"),
                )

    def execute_order(
        self,
        symbol: str,
        direction: str,  # BUY or SELL
        volume: Decimal,
        price: Decimal,
        sl: Decimal | None,
        tp: Decimal | None,
        symbol_spec: SymbolSpec,
        magic: int = 0,
        comment: str = "",
        trailing_stop_points: Decimal | None = None,
    ) -> str:
        """Process direct market order, evaluate liquidity and slippage, create deals and update positions."""
        # 1. Evaluate Liquidity model first
        liq_res = self.liquidity_model.evaluate_fill(
            requested_volume=volume,
            direction=direction,
        )

        filled_vol = liq_res["filled_volume"]
        if filled_vol <= 0:
            msg = "Order rejected due to insufficient liquidity."
            raise SimulationError(
                msg,
                code="SIM_LIQUIDITY_UNAVAILABLE",
            )

        # 2. Evaluate Slippage model on the filled volume
        exec_price = self.slippage_model.calculate_price(
            base_price=price,
            direction=direction,
            point=symbol_spec.point,
            volume=filled_vol,
        )

        # 3. Calculate Commissions
        comm = self.fee_model.calculate_commission(
            filled_volume=filled_vol,
            fill_price=exec_price,
            contract_size=symbol_spec.contract_size,
        )

        # Create Deal record
        deal_id = self.get_next_deal_id()
        deal = {
            "id": deal_id,
            "magic": magic,
            "symbol": symbol,
            "side": direction,
            "volume": filled_vol,
            "price": exec_price,
            "commission": comm,
            "swap": Decimal("0.0"),
            "profit": Decimal("0.0"),
            "time": self.current_time,
            "comment": comment,
            "entry": "in",
        }

        # Netting accounting mode: update single position per symbol
        if not self.hedging:
            existing_pos_id = None
            for p_id, p in self.positions.items():
                if p["symbol"] == symbol:
                    existing_pos_id = p_id
                    break

            if existing_pos_id:
                pos = self.positions[existing_pos_id]
                pos_vol = Decimal(str(pos["volume"]))
                pos_price = Decimal(str(pos["price"]))

                if pos["type"] == direction:
                    # Add to existing position: average price update
                    new_vol = pos_vol + filled_vol
                    avg_price = (
                        (pos_vol * pos_price) + (filled_vol * exec_price)
                    ) / new_vol
                    pos["volume"] = new_vol
                    pos["price"] = avg_price
                    # Update SL/TP if provided
                    if sl:
                        pos["sl"] = sl
                    if tp:
                        pos["tp"] = tp
                    # Update trailing stop points if provided
                    if trailing_stop_points is not None:
                        pos["trailing_stop_points"] = trailing_stop_points
                        pos["highest_bid"] = exec_price if direction == "BUY" else None
                        pos["lowest_ask"] = exec_price if direction == "SELL" else None
                # Opposite direction: reduce or reverse position
                elif filled_vol < pos_vol:
                    # Partial close
                    realized_pnl = self._calculate_realized_pnl(
                        pos["type"], pos_price, exec_price, filled_vol, symbol_spec
                    )
                    deal["profit"] = realized_pnl
                    deal["entry"] = "out"
                    pos["volume"] = pos_vol - filled_vol
                    self.balance += realized_pnl
                elif filled_vol == pos_vol:
                    # Full close
                    realized_pnl = self._calculate_realized_pnl(
                        pos["type"], pos_price, exec_price, filled_vol, symbol_spec
                    )
                    deal["profit"] = realized_pnl
                    deal["entry"] = "out"
                    del self.positions[existing_pos_id]
                    self.balance += realized_pnl
                else:
                    # Reverse position
                    realized_pnl = self._calculate_realized_pnl(
                        pos["type"], pos_price, exec_price, pos_vol, symbol_spec
                    )
                    deal["profit"] = realized_pnl
                    deal["entry"] = "out"
                    self.balance += realized_pnl
                    del self.positions[existing_pos_id]

                    # Open new opposite position with remainder volume
                    rem_vol = filled_vol - pos_vol
                    new_pos_id = self.get_next_position_id()
                    self.positions[new_pos_id] = {
                        "id": new_pos_id,
                        "magic": magic,
                        "symbol": symbol,
                        "type": direction,
                        "volume": rem_vol,
                        "price": exec_price,
                        "sl": sl,
                        "tp": tp,
                        "profit": Decimal("0.0"),
                        "time": self.current_time,
                        "comment": comment,
                        "trailing_stop_points": trailing_stop_points,
                        "highest_bid": exec_price if direction == "BUY" else None,
                        "lowest_ask": exec_price if direction == "SELL" else None,
                    }
            else:
                # Open new position
                new_pos_id = self.get_next_position_id()
                self.positions[new_pos_id] = {
                    "id": new_pos_id,
                    "magic": magic,
                    "symbol": symbol,
                    "type": direction,
                    "volume": filled_vol,
                    "price": exec_price,
                    "sl": sl,
                    "tp": tp,
                    "profit": Decimal("0.0"),
                    "time": self.current_time,
                    "comment": comment,
                    "trailing_stop_points": trailing_stop_points,
                    "highest_bid": exec_price if direction == "BUY" else None,
                    "lowest_ask": exec_price if direction == "SELL" else None,
                }
        else:
            # Hedging mode: every order opens a separate position
            new_pos_id = self.get_next_position_id()
            self.positions[new_pos_id] = {
                "id": new_pos_id,
                "magic": magic,
                "symbol": symbol,
                "type": direction,
                "volume": filled_vol,
                "price": exec_price,
                "sl": sl,
                "tp": tp,
                "profit": Decimal("0.0"),
                "time": self.current_time,
                "comment": comment,
                "trailing_stop_points": trailing_stop_points,
                "highest_bid": exec_price if direction == "BUY" else None,
                "lowest_ask": exec_price if direction == "SELL" else None,
            }

        self.balance -= comm
        self.deals.append(deal)

        if self.journal:
            self.journal.append_event("deal", deal)

        return deal_id

    def _close_position(
        self,
        pos_id: str,
        close_price: Decimal,
        close_time: str,
        symbol_spec: SymbolSpec,
        comment: str = "",
    ) -> None:
        """Close an existing position, record deals, and update account balance."""
        pos = self.positions.get(pos_id)
        if not pos:
            return

        vol = Decimal(str(pos["volume"]))
        open_price = Decimal(str(pos["price"]))
        direction = "SELL" if pos["type"] == "BUY" else "BUY"

        # Apply commissions to close trade
        comm = self.fee_model.calculate_commission(
            filled_volume=vol,
            fill_price=close_price,
            contract_size=symbol_spec.contract_size,
        )

        realized_pnl = self._calculate_realized_pnl(
            pos_type=pos["type"],
            open_price=open_price,
            close_price=close_price,
            volume=vol,
            symbol_spec=symbol_spec,
        )

        # Create Deal record
        deal_id = self.get_next_deal_id()
        deal = {
            "id": deal_id,
            "magic": pos.get("magic", 0),
            "symbol": pos["symbol"],
            "side": direction,
            "volume": vol,
            "price": close_price,
            "commission": comm,
            "swap": Decimal("0.0"),
            "profit": realized_pnl,
            "time": close_time,
            "comment": comment,
            "entry": "out",
        }

        self.balance += realized_pnl - comm
        self.deals.append(deal)
        del self.positions[pos_id]

        if self.journal:
            self.journal.append_event("deal", deal)

    def _calculate_realized_pnl(
        self,
        pos_type: str,
        open_price: Decimal,
        close_price: Decimal,
        volume: Decimal,
        symbol_spec: SymbolSpec,
    ) -> Decimal:
        """Calculate realized profit/loss using standard asset class calculations."""
        contract_sz = symbol_spec.contract_size
        if pos_type == "BUY":
            return volume * contract_sz * (close_price - open_price)
        return volume * contract_sz * (open_price - close_price)

    def submit_pending_order(
        self,
        symbol: str,
        order_type: str,
        volume: Decimal,
        price: Decimal,
        sl: Decimal | None,
        tp: Decimal | None,
        magic: int = 0,
        comment: str = "",
        stop_limit_price: Decimal | None = None,
        trailing_stop_points: Decimal | None = None,
        pegged_ref: str | None = None,
        pegged_offset_points: Decimal | None = None,
    ) -> str:
        """Submit a pending limit or stop order."""
        ord_id = self.get_next_order_id()
        order = {
            "id": ord_id,
            "magic": magic,
            "symbol": symbol,
            "type": order_type.upper(),
            "volume": volume,
            "price": price,
            "sl": sl,
            "tp": tp,
            "status": "pending",
            "time": self.current_time,
            "comment": comment,
            "stop_limit_price": stop_limit_price,
            "trailing_stop_points": trailing_stop_points,
            "pegged_ref": pegged_ref,
            "pegged_offset_points": pegged_offset_points,
        }
        self.orders[ord_id] = order

        if self.journal:
            self.journal.append_event("order_placed", order)

        return ord_id

    def cancel_pending_order(self, order_id: str) -> None:
        """Cancel an existing pending order."""
        order = self.orders.get(order_id)
        if order:
            del self.orders[order_id]
            order["status"] = "cancelled"
            self.history_orders.append(order)
            if self.journal:
                self.journal.append_event("order_cancelled", {"order_id": order_id})
