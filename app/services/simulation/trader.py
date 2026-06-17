# ruff: noqa
"""MT5-compatible simulated trader (SimTrader) implementation.

Exposes MT5-style trading functions and query semantics for strategies,
mapping request codes (instant, pending, SL/TP) to the simulation execution engine.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from app.utils.errors import SimulationError

if TYPE_CHECKING:
    from app.services.simulation.engine import EventDrivenExecutionEngine
    from app.services.simulation.validation.schema import SymbolSpec


class SimTrader:
    """MT5-style broker simulator interface for quantitative trading strategies."""

    # MT5 retcodes
    TRADE_RETCODE_DONE = 10009
    TRADE_RETCODE_REJECT = 10006
    TRADE_RETCODE_INVALID_VOLUME = 10014
    TRADE_RETCODE_INVALID_PRICE = 10015
    TRADE_RETCODE_INVALID_STOPS = 10016
    TRADE_RETCODE_FREEZE = 10017
    TRADE_RETCODE_NO_MONEY = 10019
    TRADE_RETCODE_ORDER_NOT_FOUND = 10031
    TRADE_RETCODE_POSITION_NOT_FOUND = 10032

    # MT5 actions
    TRADE_ACTION_DEAL = 1
    TRADE_ACTION_PENDING = 2
    TRADE_ACTION_SLTP = 3
    TRADE_ACTION_MODIFY = 4
    TRADE_ACTION_REMOVE = 5

    def __init__(
        self,
        engine: EventDrivenExecutionEngine,
        symbol_specs: dict[str, SymbolSpec],
    ) -> None:
        """Initialize SimTrader instance."""
        self.engine = engine
        self.symbol_specs = symbol_specs

    def order_send(self, request: dict[str, Any] | Mapping[str, Any]) -> dict[str, Any]:
        """Process MT5-style trade request order send."""
        action = int(request.get("action", self.TRADE_ACTION_DEAL))
        symbol = str(request.get("symbol", ""))
        magic = int(request.get("magic", 0))

        if not symbol or symbol not in self.symbol_specs:
            return {
                "retcode": self.TRADE_RETCODE_REJECT,
                "comment": f"Symbol {symbol} not found in specifications.",
            }

        symbol_spec = self.symbol_specs[symbol]
        last_tick = self.engine.last_tick.get(symbol)
        stops_level = symbol_spec.stops_level
        freeze_level = symbol_spec.freeze_level
        point = symbol_spec.point

        try:
            # Parse volumes and prices as Decimal
            volume = Decimal(str(request.get("volume", "0.0")))
            price = Decimal(str(request.get("price", "0.0")))
            sl = request.get("sl")
            sl_dec = (
                Decimal(str(sl))
                if sl is not None and str(sl) != "0.0" and str(sl) != "0"
                else None
            )
            tp = request.get("tp")
            tp_dec = (
                Decimal(str(tp))
                if tp is not None and str(tp) != "0.0" and str(tp) != "0"
                else None
            )

            # Parse stop limit and pegged parameters
            stop_limit_price = request.get("stop_limit_price") or request.get(
                "stoplimit"
            )
            stop_limit_price_dec = (
                Decimal(str(stop_limit_price))
                if stop_limit_price is not None
                and str(stop_limit_price) != "0.0"
                and str(stop_limit_price) != "0"
                else None
            )

            trailing_stop = request.get("trailing_stop") or request.get(
                "trailing_stop_points"
            )
            trailing_stop_dec = (
                Decimal(str(trailing_stop))
                if trailing_stop is not None
                and str(trailing_stop) != "0.0"
                and str(trailing_stop) != "0"
                else None
            )

            pegged_ref = request.get("pegged_ref")
            pegged_offset = request.get("pegged_offset_points") or request.get(
                "pegged_offset"
            )
            pegged_offset_dec = (
                Decimal(str(pegged_offset)) if pegged_offset is not None else None
            )

            # Validate volume rules
            if action in (self.TRADE_ACTION_DEAL, self.TRADE_ACTION_PENDING):
                if volume < symbol_spec.volume_min or volume > symbol_spec.volume_max:
                    return {
                        "retcode": self.TRADE_RETCODE_INVALID_VOLUME,
                        "comment": f"Volume {volume} out of bounds [{symbol_spec.volume_min}, {symbol_spec.volume_max}].",
                    }

                # Enforce volume steps (round/floor to step)
                remainder = (volume - symbol_spec.volume_min) % symbol_spec.volume_step
                if remainder != 0 and abs(
                    remainder - symbol_spec.volume_step
                ) > Decimal("1e-7"):
                    # Volume step mismatch
                    return {
                        "retcode": self.TRADE_RETCODE_INVALID_VOLUME,
                        "comment": f"Volume step mismatch: {volume} is not a multiple of step {symbol_spec.volume_step}.",
                    }

            # Handle Actions
            if action == self.TRADE_ACTION_DEAL:
                # Direct market execution
                order_type = int(
                    request.get("type", 0)
                )  # 0 = Buy, 1 = Sell (MT5 standard enum)
                direction = "BUY" if order_type == 0 else "SELL"

                # Check stops level
                if stops_level > 0 and last_tick is not None:
                    bid = Decimal(str(last_tick["bid"]))
                    ask = Decimal(str(last_tick["ask"]))
                    stops_dist = stops_level * point
                    if direction == "BUY":
                        if sl_dec is not None and ask - sl_dec < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"SL {sl_dec} violates stops level {stops_level} points from price {ask}.",
                            }
                        if tp_dec is not None and tp_dec - ask < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"TP {tp_dec} violates stops level {stops_level} points from price {ask}.",
                            }
                    else:  # SELL
                        if sl_dec is not None and sl_dec - bid < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"SL {sl_dec} violates stops level {stops_level} points from price {bid}.",
                            }
                        if tp_dec is not None and bid - tp_dec < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"TP {tp_dec} violates stops level {stops_level} points from price {bid}.",
                            }

                # Check freeze level for position close / reduction
                if freeze_level > 0 and last_tick is not None:
                    bid = Decimal(str(last_tick["bid"]))
                    ask = Decimal(str(last_tick["ask"]))
                    freeze_dist = freeze_level * point

                    position_id = request.get("position")
                    if position_id and position_id in self.engine.positions:
                        pos = self.engine.positions[position_id]
                        close_price = bid if pos["type"] == "BUY" else ask
                        pos_sl = pos.get("sl")
                        pos_tp = pos.get("tp")
                        if pos_sl and abs(close_price - pos_sl) < freeze_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_FREEZE,
                                "comment": f"Position {position_id} SL {pos_sl} is within freeze level {freeze_level} points from price {close_price}.",
                            }
                        if pos_tp and abs(close_price - pos_tp) < freeze_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_FREEZE,
                                "comment": f"Position {position_id} TP {pos_tp} is within freeze level {freeze_level} points from price {close_price}.",
                            }
                    elif not self.engine.hedging:
                        # Netting: opposite deal closes/reduces position
                        for p_id, pos in self.engine.positions.items():
                            if pos["symbol"] == symbol and pos["type"] != direction:
                                close_price = bid if pos["type"] == "BUY" else ask
                                pos_sl = pos.get("sl")
                                pos_tp = pos.get("tp")
                                if pos_sl and abs(close_price - pos_sl) < freeze_dist:
                                    return {
                                        "retcode": self.TRADE_RETCODE_FREEZE,
                                        "comment": f"Position {p_id} SL {pos_sl} is within freeze level {freeze_level} points from price {close_price}.",
                                    }
                                if pos_tp and abs(close_price - pos_tp) < freeze_dist:
                                    return {
                                        "retcode": self.TRADE_RETCODE_FREEZE,
                                        "comment": f"Position {p_id} TP {pos_tp} is within freeze level {freeze_level} points from price {close_price}.",
                                    }

                # Check if we have sufficient free margin before opening
                margin_req = self.engine.margin_model.calculate_position_margin(
                    volume=volume,
                    entry_price=price,
                    contract_size=symbol_spec.contract_size,
                    asset_class=symbol_spec.asset_class,
                )
                if margin_req > self.engine.free_margin:
                    return {
                        "retcode": self.TRADE_RETCODE_NO_MONEY,
                        "comment": f"Insufficient margin: requested {margin_req}, free {self.engine.free_margin}.",
                    }

                deal_id = self.engine.execute_order(
                    symbol=symbol,
                    direction=direction,
                    volume=volume,
                    price=price,
                    sl=sl_dec,
                    tp=tp_dec,
                    symbol_spec=symbol_spec,
                    magic=magic,
                    comment=request.get("comment", ""),
                    trailing_stop_points=trailing_stop_dec,
                )
                return {
                    "retcode": self.TRADE_RETCODE_DONE,
                    "deal": deal_id,
                    "volume": float(volume),
                    "price": float(price),
                    "comment": "Request completed successfully.",
                }

            if action == self.TRADE_ACTION_PENDING:
                # Pending limit or stop order
                order_type = int(
                    request.get("type", 2)
                )  # 2 = Buy Limit, 3 = Sell Limit, etc.
                type_map = {
                    2: "BUY_LIMIT",
                    3: "SELL_LIMIT",
                    4: "BUY_STOP",
                    5: "SELL_STOP",
                    6: "BUY_STOP_LIMIT",
                    7: "SELL_STOP_LIMIT",
                }
                ot_str = type_map.get(order_type)
                if not ot_str:
                    return {
                        "retcode": self.TRADE_RETCODE_REJECT,
                        "comment": f"Unsupported pending order type: {order_type}",
                    }

                # Initialize price for pegged orders based on current Bid/Ask/Mid
                if pegged_ref and last_tick is not None:
                    bid_val = Decimal(str(last_tick["bid"]))
                    ask_val = Decimal(str(last_tick["ask"]))
                    point = symbol_spec.point
                    tick_sz = symbol_spec.tick_size
                    if pegged_ref == "BID":
                        ref_price = bid_val
                    elif pegged_ref == "ASK":
                        ref_price = ask_val
                    elif pegged_ref == "MID":
                        ref_price = (bid_val + ask_val) / Decimal("2.0")
                    else:
                        ref_price = None

                    if ref_price is not None:
                        offset_pts = pegged_offset_dec or Decimal("0.0")
                        price = ref_price + (offset_pts * point)
                        price = (price / tick_sz).quantize(
                            Decimal(1), rounding="ROUND_HALF_UP"
                        ) * tick_sz

                # Check stops level
                if stops_level > 0 and last_tick is not None:
                    bid = Decimal(str(last_tick["bid"]))
                    ask = Decimal(str(last_tick["ask"]))
                    stops_dist = stops_level * point

                    if ot_str == "BUY_LIMIT":
                        if ask - price < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"Price {price} violates stops level {stops_level} points from current price {ask}.",
                            }
                        if sl_dec is not None and price - sl_dec < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"SL {sl_dec} violates stops level {stops_level} points from price {price}.",
                            }
                        if tp_dec is not None and tp_dec - price < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"TP {tp_dec} violates stops level {stops_level} points from price {price}.",
                            }
                    elif ot_str == "SELL_LIMIT":
                        if price - bid < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"Price {price} violates stops level {stops_level} points from current price {bid}.",
                            }
                        if sl_dec is not None and sl_dec - price < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"SL {sl_dec} violates stops level {stops_level} points from price {price}.",
                            }
                        if tp_dec is not None and price - tp_dec < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"TP {tp_dec} violates stops level {stops_level} points from price {price}.",
                            }
                    elif ot_str == "BUY_STOP":
                        if price - ask < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"Price {price} violates stops level {stops_level} points from current price {ask}.",
                            }
                        if sl_dec is not None and price - sl_dec < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"SL {sl_dec} violates stops level {stops_level} points from price {price}.",
                            }
                        if tp_dec is not None and tp_dec - price < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"TP {tp_dec} violates stops level {stops_level} points from price {price}.",
                            }
                    elif ot_str == "SELL_STOP":
                        if bid - price < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"Price {price} violates stops level {stops_level} points from current price {bid}.",
                            }
                        if sl_dec is not None and sl_dec - price < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"SL {sl_dec} violates stops level {stops_level} points from price {price}.",
                            }
                        if tp_dec is not None and price - tp_dec < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"TP {tp_dec} violates stops level {stops_level} points from price {price}.",
                            }
                    elif ot_str == "BUY_STOP_LIMIT":
                        if stop_limit_price_dec is None:
                            return {
                                "retcode": self.TRADE_RETCODE_REJECT,
                                "comment": "stop_limit_price is required for BUY_STOP_LIMIT.",
                            }
                        if price - ask < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"Stop price {price} violates stops level {stops_level} points from current price {ask}.",
                            }
                        if abs(price - stop_limit_price_dec) < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"Limit price {stop_limit_price_dec} violates stops level {stops_level} points from stop price {price}.",
                            }
                        if (
                            sl_dec is not None
                            and stop_limit_price_dec - sl_dec < stops_dist
                        ):
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"SL {sl_dec} violates stops level {stops_level} points from limit price {stop_limit_price_dec}.",
                            }
                        if (
                            tp_dec is not None
                            and tp_dec - stop_limit_price_dec < stops_dist
                        ):
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"TP {tp_dec} violates stops level {stops_level} points from limit price {stop_limit_price_dec}.",
                            }
                    elif ot_str == "SELL_STOP_LIMIT":
                        if stop_limit_price_dec is None:
                            return {
                                "retcode": self.TRADE_RETCODE_REJECT,
                                "comment": "stop_limit_price is required for SELL_STOP_LIMIT.",
                            }
                        if bid - price < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"Stop price {price} violates stops level {stops_level} points from current price {bid}.",
                            }
                        if abs(price - stop_limit_price_dec) < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"Limit price {stop_limit_price_dec} violates stops level {stops_level} points from stop price {price}.",
                            }
                        if (
                            sl_dec is not None
                            and sl_dec - stop_limit_price_dec < stops_dist
                        ):
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"SL {sl_dec} violates stops level {stops_level} points from limit price {stop_limit_price_dec}.",
                            }
                        if (
                            tp_dec is not None
                            and stop_limit_price_dec - tp_dec < stops_dist
                        ):
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"TP {tp_dec} violates stops level {stops_level} points from limit price {stop_limit_price_dec}.",
                            }

                order_id = self.engine.submit_pending_order(
                    symbol=symbol,
                    order_type=ot_str,
                    volume=volume,
                    price=price,
                    sl=sl_dec,
                    tp=tp_dec,
                    magic=magic,
                    comment=request.get("comment", ""),
                    stop_limit_price=stop_limit_price_dec,
                    trailing_stop_points=trailing_stop_dec,
                    pegged_ref=pegged_ref,
                    pegged_offset_points=pegged_offset_dec,
                )
                return {
                    "retcode": self.TRADE_RETCODE_DONE,
                    "order": order_id,
                    "volume": float(volume),
                    "price": float(price),
                    "comment": "Pending order submitted successfully.",
                }

            if action == self.TRADE_ACTION_SLTP:
                # Modify SL/TP of existing position
                position_id = str(request.get("position", ""))
                if position_id not in self.engine.positions:
                    return {
                        "retcode": self.TRADE_RETCODE_POSITION_NOT_FOUND,
                        "comment": f"Position {position_id} not found.",
                    }

                pos = self.engine.positions[position_id]

                # Check freeze level
                if freeze_level > 0 and last_tick is not None:
                    bid = Decimal(str(last_tick["bid"]))
                    ask = Decimal(str(last_tick["ask"]))
                    freeze_dist = freeze_level * point
                    close_price = bid if pos["type"] == "BUY" else ask
                    pos_sl = pos.get("sl")
                    pos_tp = pos.get("tp")
                    if pos_sl and abs(close_price - pos_sl) < freeze_dist:
                        return {
                            "retcode": self.TRADE_RETCODE_FREEZE,
                            "comment": f"SL {pos_sl} is within freeze level {freeze_level} points from close price {close_price}.",
                        }
                    if pos_tp and abs(close_price - pos_tp) < freeze_dist:
                        return {
                            "retcode": self.TRADE_RETCODE_FREEZE,
                            "comment": f"TP {pos_tp} is within freeze level {freeze_level} points from close price {close_price}.",
                        }

                # Check stops level
                if stops_level > 0 and last_tick is not None:
                    bid = Decimal(str(last_tick["bid"]))
                    ask = Decimal(str(last_tick["ask"]))
                    stops_dist = stops_level * point
                    if pos["type"] == "BUY":
                        if sl_dec is not None and bid - sl_dec < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"New SL {sl_dec} violates stops level {stops_level} points from price {bid}.",
                            }
                        if tp_dec is not None and tp_dec - bid < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"New TP {tp_dec} violates stops level {stops_level} points from price {bid}.",
                            }
                    else:  # SELL
                        if sl_dec is not None and sl_dec - ask < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"New SL {sl_dec} violates stops level {stops_level} points from price {ask}.",
                            }
                        if tp_dec is not None and ask - tp_dec < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"New TP {tp_dec} violates stops level {stops_level} points from price {ask}.",
                            }

                pos["sl"] = sl_dec
                pos["tp"] = tp_dec

                if self.engine.journal:
                    self.engine.journal.append_event(
                        "position_modified",
                        {
                            "position_id": position_id,
                            "sl": float(sl_dec) if sl_dec else None,
                            "tp": float(tp_dec) if tp_dec else None,
                        },
                    )

                return {
                    "retcode": self.TRADE_RETCODE_DONE,
                    "comment": "SL/TP modified successfully.",
                }

            if action == self.TRADE_ACTION_MODIFY:
                # Modify pending order price or SL/TP
                order_id = str(request.get("order", ""))
                if order_id not in self.engine.orders:
                    return {
                        "retcode": self.TRADE_RETCODE_ORDER_NOT_FOUND,
                        "comment": f"Pending order {order_id} not found.",
                    }

                order = self.engine.orders[order_id]

                # Check freeze level
                if freeze_level > 0 and last_tick is not None:
                    bid = Decimal(str(last_tick["bid"]))
                    ask = Decimal(str(last_tick["ask"]))
                    freeze_dist = freeze_level * point
                    ref_price = ask if order["type"].startswith("BUY") else bid
                    old_price = Decimal(str(order["price"]))
                    if abs(ref_price - old_price) < freeze_dist:
                        return {
                            "retcode": self.TRADE_RETCODE_FREEZE,
                            "comment": f"Order price {old_price} is within freeze level {freeze_level} points from price {ref_price}.",
                        }

                # Check stops level
                if stops_level > 0 and last_tick is not None:
                    bid = Decimal(str(last_tick["bid"]))
                    ask = Decimal(str(last_tick["ask"]))
                    stops_dist = stops_level * point
                    ot_str = order["type"]

                    if ot_str == "BUY_LIMIT":
                        if ask - price < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"New price {price} violates stops level {stops_level} points from price {ask}.",
                            }
                        if sl_dec is not None and price - sl_dec < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"SL {sl_dec} violates stops level {stops_level} points from price {price}.",
                            }
                        if tp_dec is not None and tp_dec - price < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"TP {tp_dec} violates stops level {stops_level} points from price {price}.",
                            }
                    elif ot_str == "SELL_LIMIT":
                        if price - bid < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"New price {price} violates stops level {stops_level} points from price {bid}.",
                            }
                        if sl_dec is not None and sl_dec - price < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"SL {sl_dec} violates stops level {stops_level} points from price {price}.",
                            }
                        if tp_dec is not None and price - tp_dec < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"TP {tp_dec} violates stops level {stops_level} points from price {price}.",
                            }
                    elif ot_str == "BUY_STOP":
                        if price - ask < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"New price {price} violates stops level {stops_level} points from price {ask}.",
                            }
                        if sl_dec is not None and price - sl_dec < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"SL {sl_dec} violates stops level {stops_level} points from price {price}.",
                            }
                        if tp_dec is not None and tp_dec - price < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"TP {tp_dec} violates stops level {stops_level} points from price {price}.",
                            }
                    elif ot_str == "SELL_STOP":
                        if bid - price < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"New price {price} violates stops level {stops_level} points from price {bid}.",
                            }
                        if sl_dec is not None and sl_dec - price < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"SL {sl_dec} violates stops level {stops_level} points from price {price}.",
                            }
                        if tp_dec is not None and price - tp_dec < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"TP {tp_dec} violates stops level {stops_level} points from price {price}.",
                            }
                    elif ot_str == "BUY_STOP_LIMIT":
                        eff_limit_dec = (
                            stop_limit_price_dec
                            if stop_limit_price_dec is not None
                            else Decimal(str(order.get("stop_limit_price") or "0.0"))
                        )
                        if price - ask < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"New price {price} violates stops level {stops_level} points from price {ask}.",
                            }
                        if abs(price - eff_limit_dec) < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"Stop limit price {eff_limit_dec} violates stops level {stops_level} points from stop price {price}.",
                            }
                        if sl_dec is not None and eff_limit_dec - sl_dec < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"SL {sl_dec} violates stops level {stops_level} points from limit price {eff_limit_dec}.",
                            }
                        if tp_dec is not None and tp_dec - eff_limit_dec < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"TP {tp_dec} violates stops level {stops_level} points from limit price {eff_limit_dec}.",
                            }
                    elif ot_str == "SELL_STOP_LIMIT":
                        eff_limit_dec = (
                            stop_limit_price_dec
                            if stop_limit_price_dec is not None
                            else Decimal(str(order.get("stop_limit_price") or "0.0"))
                        )
                        if bid - price < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"New price {price} violates stops level {stops_level} points from price {bid}.",
                            }
                        if abs(price - eff_limit_dec) < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"Stop limit price {eff_limit_dec} violates stops level {stops_level} points from stop price {price}.",
                            }
                        if sl_dec is not None and sl_dec - eff_limit_dec < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"SL {sl_dec} violates stops level {stops_level} points from limit price {eff_limit_dec}.",
                            }
                        if tp_dec is not None and eff_limit_dec - tp_dec < stops_dist:
                            return {
                                "retcode": self.TRADE_RETCODE_INVALID_STOPS,
                                "comment": f"TP {tp_dec} violates stops level {stops_level} points from limit price {eff_limit_dec}.",
                            }

                order["price"] = price
                order["sl"] = sl_dec
                order["tp"] = tp_dec
                if stop_limit_price_dec is not None:
                    order["stop_limit_price"] = stop_limit_price_dec

                if self.engine.journal:
                    self.engine.journal.append_event(
                        "order_modified",
                        {
                            "order_id": order_id,
                            "price": float(price),
                            "sl": float(sl_dec) if sl_dec else None,
                            "tp": float(tp_dec) if tp_dec else None,
                        },
                    )

                return {
                    "retcode": self.TRADE_RETCODE_DONE,
                    "comment": "Pending order modified successfully.",
                }

            if action == self.TRADE_ACTION_REMOVE:
                # Cancel pending order
                order_id = str(request.get("order", ""))
                if order_id not in self.engine.orders:
                    return {
                        "retcode": self.TRADE_RETCODE_ORDER_NOT_FOUND,
                        "comment": f"Pending order {order_id} not found.",
                    }

                order = self.engine.orders[order_id]

                # Check freeze level
                if freeze_level > 0 and last_tick is not None:
                    bid = Decimal(str(last_tick["bid"]))
                    ask = Decimal(str(last_tick["ask"]))
                    freeze_dist = freeze_level * point
                    ref_price = ask if order["type"].startswith("BUY") else bid
                    ord_price = Decimal(str(order["price"]))
                    if abs(ref_price - ord_price) < freeze_dist:
                        return {
                            "retcode": self.TRADE_RETCODE_FREEZE,
                            "comment": f"Order price {ord_price} is within freeze level {freeze_level} points from price {ref_price}.",
                        }

                self.engine.cancel_pending_order(order_id)
                return {
                    "retcode": self.TRADE_RETCODE_DONE,
                    "comment": "Pending order cancelled successfully.",
                }

            return {
                "retcode": self.TRADE_RETCODE_REJECT,
                "comment": f"Unsupported action: {action}",
            }

        except Exception as e:
            return {
                "retcode": self.TRADE_RETCODE_REJECT,
                "comment": f"Error executing order send: {e}",
            }

    def positions_get(
        self, symbol: str | None = None
    ) -> tuple[dict[str, Any], ...] | None:
        """Query open positions, optionally filtered by symbol."""
        pos_list = list(self.engine.positions.values())
        if symbol:
            pos_list = [p for p in pos_list if p["symbol"] == symbol]
        return tuple(pos_list) if pos_list else ()

    def positions_total(self) -> int:
        """Get total open positions count."""
        return len(self.engine.positions)

    def orders_get(
        self, symbol: str | None = None
    ) -> tuple[dict[str, Any], ...] | None:
        """Query pending orders, optionally filtered by symbol."""
        ord_list = list(self.engine.orders.values())
        if symbol:
            ord_list = [o for o in ord_list if o["symbol"] == symbol]
        return tuple(ord_list) if ord_list else ()

    def orders_total(self) -> int:
        """Get total pending orders count."""
        return len(self.engine.orders)

    def history_deals_get(self) -> tuple[dict[str, Any], ...]:
        """Query all historical executed deals."""
        return tuple(self.engine.deals)

    def history_orders_get(self) -> tuple[dict[str, Any], ...]:
        """Query all completed or cancelled orders."""
        return tuple(self.engine.history_orders)

    def account_info(self) -> dict[str, Any]:
        """Get details representing current account balance, equity, margin state."""
        return {
            "balance": float(self.engine.balance),
            "equity": float(self.engine.equity),
            "margin": float(self.engine.margin),
            "free_margin": float(self.engine.free_margin),
            "margin_level": float(self.engine.margin_level)
            if self.engine.margin_level is not None
            else 0.0,
            "leverage": float(self.engine.leverage),
            "currency": self.engine.account_currency,
        }

    def order_calc_margin(
        self,
        action: int,
        symbol: str,
        volume: Decimal | float,
        price: Decimal | float,
    ) -> float:
        """Calculate margin required for a specific hypothetical trade volume/price."""
        if symbol not in self.symbol_specs:
            msg = f"Symbol {symbol} not found."
            raise SimulationError(msg, code="SIM_MISSING_SYMBOL")
        spec = self.symbol_specs[symbol]
        margin_val = self.engine.margin_model.calculate_position_margin(
            volume=Decimal(str(volume)),
            entry_price=Decimal(str(price)),
            contract_size=spec.contract_size,
            asset_class=spec.asset_class,
        )
        return float(margin_val)

    def order_calc_profit(
        self,
        action: int,
        symbol: str,
        volume: Decimal | float,
        price_open: Decimal | float,
        price_close: Decimal | float,
    ) -> float:
        """Calculate profit/loss expected for a trade segment."""
        if symbol not in self.symbol_specs:
            msg = f"Symbol {symbol} not found."
            raise SimulationError(msg, code="SIM_MISSING_SYMBOL")
        spec = self.symbol_specs[symbol]
        # action: 0 = Buy, 1 = Sell
        pnl = self.engine._calculate_realized_pnl(
            pos_type="BUY" if action == 0 else "SELL",
            open_price=Decimal(str(price_open)),
            close_price=Decimal(str(price_close)),
            volume=Decimal(str(volume)),
            symbol_spec=spec,
        )
        return float(pnl)
