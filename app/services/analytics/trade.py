"""Trade metrics calculations for Analytics.

Implements all metrics, statistics, and calculations based on trade history logs.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, cast

from app.utils import (
    StandardResponse,
    build_metadata,
    response_from_exception,
    success_response,
)
from app.utils.errors import ValidationError


def _validate_request_id(request_id: str | None) -> None:
    """Helper to validate request_id strictly."""
    if request_id is not None:
        if not isinstance(request_id, str) or not request_id.strip():
            raise ValidationError("request_id must be a non-empty string.")


def _to_trade_list(trades: Any) -> list[dict[str, Any]]:
    """Helper to convert various inputs to a list of dicts."""
    if trades is None:
        return []
    if hasattr(trades, "to_dict"):
        # Pandas DataFrame
        return cast("list[dict[str, Any]]", trades.to_dict("records"))
    if isinstance(trades, list):
        res = []
        for t in trades:
            if isinstance(t, dict):
                res.append(t)
            elif hasattr(t, "model_dump"):
                res.append(t.model_dump())
            elif hasattr(t, "__dict__"):
                res.append(t.__dict__)
            else:
                res.append(dict(t))
        return res
    return []


def _get_trade_pnl(trade: dict[str, Any]) -> float:
    """Extract PnL value from a trade dict."""
    for key in ("net_pnl", "profit_loss", "pnl", "profit", "profit_loss_usd"):
        if key in trade:
            val = trade[key]
            if val is not None:
                return float(val)
    return 0.0


# --- Core Kernels ---


def get_closed_trades(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter trades to realized closed trades only."""
    closed = []
    for t in trades:
        # Check if close_time or equivalent exists and is not empty
        close_time = t.get("close_time") or t.get("close_timestamp")
        # Ignore open trades
        is_open = t.get("is_open", False)
        if close_time is not None and not is_open:
            closed.append(t)
    return closed


def classify_trades(
    trades: list[dict[str, Any]], breakeven_epsilon: float = 1e-5
) -> dict[str, list[dict[str, Any]]]:
    """Classify trades into wins, losses, and breakevens."""
    wins = []
    losses = []
    breakevens = []
    for t in trades:
        pnl = _get_trade_pnl(t)
        if pnl > breakeven_epsilon:
            wins.append(t)
        elif pnl < -breakeven_epsilon:
            losses.append(t)
        else:
            breakevens.append(t)
    return {"wins": wins, "losses": losses, "breakevens": breakevens}


def get_r_multiples(trades: list[dict[str, Any]]) -> list[float]:
    """Calculate R-multiples for trades."""
    r_multiples = []
    for t in trades:
        pnl = _get_trade_pnl(t)
        risk = t.get("initial_risk") or t.get("risk") or t.get("risk_amount")
        if risk is None or float(risk) <= 0:
            # Degraded fallback proxy
            risk = 1.0
        r_multiples.append(pnl / float(risk))
    return r_multiples


def _parse_time(t_val: Any) -> datetime | None:
    if isinstance(t_val, datetime):
        return t_val
    if isinstance(t_val, str):
        try:
            return datetime.fromisoformat(t_val.replace("Z", "+00:00"))
        except ValueError:
            return None
    if isinstance(t_val, int | float):
        return datetime.fromtimestamp(float(t_val))
    return None


def get_ordered_closed_trades(trades: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter and sort trades chronologically by close time."""
    closed = get_closed_trades(trades)

    def get_time(t: dict[str, Any]) -> float:
        ct = t.get("close_time") or t.get("close_timestamp")
        dt = _parse_time(ct)
        return dt.timestamp() if dt else 0.0

    return sorted(closed, key=get_time)


def total_trades(trades: Any, request_id: str | None = None) -> StandardResponse:
    """Return the total number of closed trades."""
    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="total_trades",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        t_list = _to_trade_list(trades)
        closed = get_closed_trades(t_list)
        return success_response(
            message="Calculated total closed trades.",
            data=len(closed),
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)


def win_rate(trades: Any, request_id: str | None = None) -> StandardResponse:
    """Return the win rate on a 0-to-1 scale."""
    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="win_rate",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        t_list = _to_trade_list(trades)
        closed = get_closed_trades(t_list)
        if not closed:
            return success_response(
                message="No closed trades to calculate win rate.",
                data=0.0,
                metadata=meta,
            )
        classes = classify_trades(closed)
        rate = len(classes["wins"]) / len(closed)
        return success_response(
            message="Calculated win rate.",
            data=rate,
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)


def profit_factor(trades: Any, request_id: str | None = None) -> StandardResponse:
    """Return the profit factor (gross profit / gross loss)."""
    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="profit_factor",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        t_list = _to_trade_list(trades)
        closed = get_closed_trades(t_list)
        if not closed:
            return success_response(
                message="No closed trades to calculate profit factor.",
                data=0.0,
                metadata=meta,
            )
        gross_prof = sum(_get_trade_pnl(t) for t in closed if _get_trade_pnl(t) > 0)
        gross_l = sum(abs(_get_trade_pnl(t)) for t in closed if _get_trade_pnl(t) < 0)
        factor = gross_prof / gross_l if gross_l > 0 else float("inf")
        if math.isinf(factor):
            factor = 999.0
        return success_response(
            message="Calculated profit factor.",
            data=factor,
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)


# --- Supporting Metric Kernels ---


def winning_trades(trades: list[dict[str, Any]]) -> int:
    return len(classify_trades(trades)["wins"])


def losing_trades(trades: list[dict[str, Any]]) -> int:
    return len(classify_trades(trades)["losses"])


def breakeven_trades(trades: list[dict[str, Any]]) -> int:
    return len(classify_trades(trades)["breakevens"])


def long_trades(trades: list[dict[str, Any]]) -> int:
    return sum(
        1 for t in trades if str(t.get("direction", "")).lower() in ("long", "buy")
    )


def short_trades(trades: list[dict[str, Any]]) -> int:
    return sum(
        1 for t in trades if str(t.get("direction", "")).lower() in ("short", "sell")
    )


def count_open_trades(trades: list[dict[str, Any]]) -> int:
    return sum(
        1 for t in trades if t.get("is_open", False) or t.get("close_time") is None
    )


def loss_rate(trades: list[dict[str, Any]]) -> float:
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    return losing_trades(closed) / len(closed)


def avg_win(trades: list[dict[str, Any]]) -> float:
    wins = classify_trades(trades)["wins"]
    if not wins:
        return 0.0
    return sum(_get_trade_pnl(t) for t in wins) / len(wins)


def avg_loss(trades: list[dict[str, Any]]) -> float:
    losses = classify_trades(trades)["losses"]
    if not losses:
        return 0.0
    return sum(_get_trade_pnl(t) for t in losses) / len(losses)


def largest_win(trades: list[dict[str, Any]]) -> float:
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    return max((_get_trade_pnl(t) for t in closed), default=0.0)


def largest_loss(trades: list[dict[str, Any]]) -> float:
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    return min((_get_trade_pnl(t) for t in closed), default=0.0)


def median_win(trades: list[dict[str, Any]]) -> float:
    wins = sorted([_get_trade_pnl(t) for t in classify_trades(trades)["wins"]])
    if not wins:
        return 0.0
    n = len(wins)
    if n % 2 == 1:
        return wins[n // 2]
    return (wins[n // 2 - 1] + wins[n // 2]) / 2.0


def median_loss(trades: list[dict[str, Any]]) -> float:
    losses = sorted([_get_trade_pnl(t) for t in classify_trades(trades)["losses"]])
    if not losses:
        return 0.0
    n = len(losses)
    if n % 2 == 1:
        return losses[n // 2]
    return (losses[n // 2 - 1] + losses[n // 2]) / 2.0


def expectancy(trades: list[dict[str, Any]]) -> float:
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    pnl_sum = sum(_get_trade_pnl(t) for t in closed)
    return pnl_sum / len(closed)


def max_consecutive_wins(trades: list[dict[str, Any]]) -> int:
    ordered = get_ordered_closed_trades(trades)
    max_streak = 0
    current_streak = 0
    for t in ordered:
        pnl = _get_trade_pnl(t)
        if pnl > 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    return max_streak


def max_consecutive_losses(trades: list[dict[str, Any]]) -> int:
    ordered = get_ordered_closed_trades(trades)
    max_streak = 0
    current_streak = 0
    for t in ordered:
        pnl = _get_trade_pnl(t)
        if pnl < 0:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
    return max_streak


def _get_trade_duration(t: dict[str, Any]) -> float:
    ot = _parse_time(t.get("open_time") or t.get("open_timestamp"))
    ct = _parse_time(t.get("close_time") or t.get("close_timestamp"))
    if ot and ct:
        return max((ct - ot).total_seconds() / 3600.0, 0.0)
    return 0.0


def avg_time_in_trade(trades: list[dict[str, Any]]) -> float:
    durations = [_get_trade_duration(t) for t in get_closed_trades(trades)]
    if not durations:
        return 0.0
    return sum(durations) / len(durations)


def median_time_in_trade(trades: list[dict[str, Any]]) -> float:
    durations = sorted([_get_trade_duration(t) for t in get_closed_trades(trades)])
    if not durations:
        return 0.0
    n = len(durations)
    if n % 2 == 1:
        return durations[n // 2]
    return (durations[n // 2 - 1] + durations[n // 2]) / 2.0


def max_time_in_trade(trades: list[dict[str, Any]]) -> float:
    durations = [_get_trade_duration(t) for t in get_closed_trades(trades)]
    return max(durations, default=0.0)


def min_time_in_trade(trades: list[dict[str, Any]]) -> float:
    durations = [_get_trade_duration(t) for t in get_closed_trades(trades)]
    return min(durations, default=0.0)


def compute_r_trade_metrics(r_multiples: list[float]) -> dict[str, float]:
    if not r_multiples:
        return {"avg": 0.0, "std": 0.0, "expectancy": 0.0}
    avg = sum(r_multiples) / len(r_multiples)
    var = sum((x - avg) ** 2 for x in r_multiples) / max(len(r_multiples) - 1, 1)
    return {"avg": avg, "std": math.sqrt(var), "expectancy": avg}


def compute_trade_metrics(
    r_values: list[float],
    mae: list[float] | None = None,
    mfe: list[float] | None = None,
) -> dict[str, float]:
    return compute_r_trade_metrics(r_values)


def trade_efficiency(trade: dict[str, Any]) -> float:
    pnl = _get_trade_pnl(trade)
    mfe = float(trade.get("mfe") or 0.0)
    if mfe <= 0:
        return 0.0
    return max(pnl / mfe, -1.0)


def trade_outcome_entropy(trades: list[dict[str, Any]]) -> float:
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    classes = classify_trades(closed)
    n = len(closed)
    p_win = len(classes["wins"]) / n
    p_loss = len(classes["losses"]) / n
    p_be = len(classes["breakevens"]) / n
    entropy = 0.0
    for p in (p_win, p_loss, p_be):
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def longest_flat_period_duration(
    trades: list[dict[str, Any]], period_start: Any = None, period_end: Any = None
) -> float:
    ordered = get_ordered_closed_trades(trades)
    if not ordered:
        return 0.0
    max_flat = 0.0
    prev_close = _parse_time(period_start) if period_start else None

    for t in ordered:
        ot = _parse_time(t.get("open_time") or t.get("open_timestamp"))
        ct = _parse_time(t.get("close_time") or t.get("close_timestamp"))
        if prev_close and ot:
            flat = (ot - prev_close).total_seconds() / 3600.0
            max_flat = max(max_flat, flat)
        prev_close = ct

    if period_end and prev_close:
        end = _parse_time(period_end)
        if end:
            flat = (end - prev_close).total_seconds() / 3600.0
            max_flat = max(max_flat, flat)

    return max_flat


def return_over_drawdown(net_prof: float, max_dd: float) -> float:
    if max_dd <= 0:
        return 0.0
    return net_prof / max_dd


def net_profit_as_percent_of_max_trade_drawdown(
    net_prof: float, max_dd: float
) -> float:
    return return_over_drawdown(net_prof, max_dd) * 100.0


def select_net_profit_as_percent_of_max_trade_drawdown(
    net_prof: float, max_dd: float
) -> float:
    return return_over_drawdown(net_prof, max_dd) * 100.0


def adjusted_net_profit_as_percent_of_max_trade_drawdown(
    net_prof: float, max_dd: float
) -> float:
    return return_over_drawdown(net_prof, max_dd) * 100.0


def net_profit(trades: list[dict[str, Any]]) -> float:
    return sum(_get_trade_pnl(t) for t in get_closed_trades(trades))


def gross_profit(trades: list[dict[str, Any]]) -> float:
    return sum(
        _get_trade_pnl(t) for t in get_closed_trades(trades) if _get_trade_pnl(t) > 0
    )


def gross_loss(trades: list[dict[str, Any]]) -> float:
    return sum(
        _get_trade_pnl(t) for t in get_closed_trades(trades) if _get_trade_pnl(t) < 0
    )


def balance_curve_from_closed_trades(
    trades: list[dict[str, Any]], initial_balance: float = 10000.0
) -> list[dict[str, Any]]:
    ordered = get_ordered_closed_trades(trades)
    curve = []
    current_balance = initial_balance
    start_time = "1970-01-01T00:00:00Z"
    if ordered:
        ot = ordered[0].get("open_time") or ordered[0].get("open_timestamp")
        if ot:
            parsed = _parse_time(ot)
            start_time = (
                ot
                if isinstance(ot, str)
                else (parsed.isoformat() if parsed else "1970-01-01T00:00:00Z")
            )
    curve.append(
        {"timestamp": start_time, "equity": current_balance, "currency": "USD"}
    )

    for t in ordered:
        current_balance += _get_trade_pnl(t)
        ct = t.get("close_time") or t.get("close_timestamp")
        parsed = _parse_time(ct)
        timestamp = (
            ct
            if isinstance(ct, str)
            else (parsed.isoformat() if parsed else "1970-01-01T00:00:00Z")
        )
        curve.append(
            {"timestamp": timestamp, "equity": current_balance, "currency": "USD"}
        )

    return curve


def balance_curve(
    trades: list[dict[str, Any]], initial_balance: float = 10000.0
) -> list[dict[str, Any]]:
    return balance_curve_from_closed_trades(trades, initial_balance)


def equity_curve(
    trades: list[dict[str, Any]], initial_balance: float = 10000.0
) -> list[dict[str, Any]]:
    return balance_curve_from_closed_trades(trades, initial_balance)


def max_loss_probability(trades: list[dict[str, Any]], threshold: float) -> float:
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    bad_count = sum(1 for t in closed if _get_trade_pnl(t) <= -abs(threshold))
    return bad_count / len(closed)


def risk_of_ruin(
    trades: list[dict[str, Any]],
    initial_balance: float,
    ruin_threshold: float,
    iterations: int = 1000,
) -> float:
    closed = get_closed_trades(trades)
    if not closed or initial_balance <= ruin_threshold:
        return 0.0
    pnl_outcomes = [_get_trade_pnl(t) for t in closed]
    import random

    ruined_sims = 0
    rng = random.Random(42)
    for _ in range(iterations):
        balance = initial_balance
        for _ in range(100):
            outcome = rng.choice(pnl_outcomes)
            balance += outcome
            if balance <= ruin_threshold:
                ruined_sims += 1
                break
    return ruined_sims / iterations


def avg_trade_nominal_exposure(trades: list[dict[str, Any]]) -> float:
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    exposures = []
    for t in closed:
        size = float(t.get("size") or t.get("volume") or 0.0)
        price = float(t.get("open_price") or t.get("entry_price") or 1.0)
        exposures.append(size * price)
    return sum(exposures) / len(exposures) if exposures else 0.0


def max_single_trade_margin_utilization(trades: list[dict[str, Any]]) -> float:
    closed = get_closed_trades(trades)
    return max((float(t.get("margin") or 0.0) for t in closed), default=0.0)


def avg_single_trade_margin_utilization(trades: list[dict[str, Any]]) -> float:
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    margins = [float(t.get("margin") or 0.0) for t in closed]
    return sum(margins) / len(margins)


def risk_of_ruin_with_custom_horizon(
    trades: list[dict[str, Any]],
    initial_balance: float,
    ruin_threshold: float,
    horizon: int = 50,
) -> float:
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    pnl_outcomes = [_get_trade_pnl(t) for t in closed]
    import random

    rng = random.Random(42)
    ruined_sims = 0
    for _ in range(1000):
        balance = initial_balance
        for _ in range(horizon):
            balance += rng.choice(pnl_outcomes)
            if balance <= ruin_threshold:
                ruined_sims += 1
                break
    return ruined_sims / 1000.0


def max_gross_size_held(trades: list[dict[str, Any]]) -> float:
    return max(
        (float(t.get("size") or t.get("volume") or 0.0) for t in trades), default=0.0
    )


def time_in_market_duration(trades: list[dict[str, Any]]) -> float:
    closed = get_ordered_closed_trades(trades)
    if not closed:
        return 0.0
    intervals: list[tuple[float, float]] = []
    for t in closed:
        ot = _parse_time(t.get("open_time") or t.get("open_timestamp"))
        ct = _parse_time(t.get("close_time") or t.get("close_timestamp"))
        if ot and ct:
            intervals.append((ot.timestamp(), ct.timestamp()))

    if not intervals:
        return 0.0

    intervals.sort()
    merged = []
    curr = intervals[0]
    for nxt in intervals[1:]:
        if nxt[0] <= curr[1]:
            curr = (curr[0], max(curr[1], nxt[1]))
        else:
            merged.append(curr)
            curr = nxt
    merged.append(curr)

    duration_seconds = sum(end - start for start, end in merged)
    return duration_seconds / 3600.0


def percent_time_in_market(
    trades: list[dict[str, Any]], period_duration_hours: float
) -> float:
    if period_duration_hours <= 0:
        return 0.0
    return time_in_market_duration(trades) / period_duration_hours


def win_rate_fraction(trades: list[dict[str, Any]]) -> float:
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    return winning_trades(closed) / len(closed)


def avg_win_loss(trades: list[dict[str, Any]]) -> float:
    aw = avg_win(trades)
    al = abs(avg_loss(trades))
    if al == 0:
        return 0.0
    return aw / al


def consecutive_wins_losses(trades: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "wins": max_consecutive_wins(trades),
        "losses": max_consecutive_losses(trades),
    }


def median_mae_mfe(trades: list[dict[str, Any]]) -> dict[str, float]:
    maes = sorted([float(t.get("mae") or 0.0) for t in trades if "mae" in t])
    mfes = sorted([float(t.get("mfe") or 0.0) for t in trades if "mfe" in t])
    med_mae = maes[len(maes) // 2] if maes else 0.0
    med_mfe = mfes[len(mfes) // 2] if mfes else 0.0
    return {"mae": med_mae, "mfe": med_mfe}


def get_mae_mfe_r(trades: list[dict[str, Any]]) -> list[dict[str, float]]:
    res = []
    for t in trades:
        risk = float(t.get("initial_risk") or 1.0)
        mae = float(t.get("mae") or 0.0)
        mfe = float(t.get("mfe") or 0.0)
        res.append({"mae_r": mae / risk, "mfe_r": mfe / risk})
    return res


def t_statistic(trades: list[dict[str, Any]]) -> float:
    closed = get_closed_trades(trades)
    n = len(closed)
    if n < 2:
        return 0.0
    pnls = [_get_trade_pnl(t) for t in closed]
    mean = sum(pnls) / n
    var = sum((x - mean) ** 2 for x in pnls) / (n - 1)
    if var == 0:
        return 0.0
    return mean / (math.sqrt(var) / math.sqrt(n))


def open_position_pnl(trades: list[dict[str, Any]]) -> float:
    return sum(
        float(t.get("unrealized_pnl") or t.get("pnl") or 0.0)
        for t in trades
        if t.get("is_open", False) or t.get("close_time") is None
    )


def slippage_paid(trades: list[dict[str, Any]]) -> float:
    return sum(abs(float(t.get("slippage") or 0.0)) for t in trades)


def commission_paid(trades: list[dict[str, Any]]) -> float:
    return sum(abs(float(t.get("commission") or 0.0)) for t in trades)


def swap_paid(trades: list[dict[str, Any]]) -> float:
    return sum(abs(float(t.get("swap") or 0.0)) for t in trades)


def expectancy_r(trades: list[dict[str, Any]]) -> float:
    r_mults = get_r_multiples(trades)
    if not r_mults:
        return 0.0
    return sum(r_mults) / len(r_mults)


def max_size_held(trades: list[dict[str, Any]]) -> float:
    return max_gross_size_held(trades)


def max_net_size_held(trades: list[dict[str, Any]]) -> float:
    return max((abs(float(t.get("size") or 0.0)) for t in trades), default=0.0)


def max_long_size_held(trades: list[dict[str, Any]]) -> float:
    longs = [
        float(t.get("size") or 0.0)
        for t in trades
        if str(t.get("direction", "")).lower() in ("long", "buy")
    ]
    return max(longs, default=0.0)


def max_short_size_held(trades: list[dict[str, Any]]) -> float:
    shorts = [
        float(t.get("size") or 0.0)
        for t in trades
        if str(t.get("direction", "")).lower() in ("short", "sell")
    ]
    return max(shorts, default=0.0)


def avg_r_multiple(trades: list[dict[str, Any]]) -> float:
    return expectancy_r(trades)


def median_r_multiple(trades: list[dict[str, Any]]) -> float:
    r_mults = sorted(get_r_multiples(trades))
    if not r_mults:
        return 0.0
    n = len(r_mults)
    if n % 2 == 1:
        return r_mults[n // 2]
    return (r_mults[n // 2 - 1] + r_mults[n // 2]) / 2.0


def max_r_multiple(trades: list[dict[str, Any]]) -> float:
    r_mults = get_r_multiples(trades)
    return max(r_mults, default=0.0)


def min_r_multiple(trades: list[dict[str, Any]]) -> float:
    r_mults = get_r_multiples(trades)
    return min(r_mults, default=0.0)


def median_mae_r(trades: list[dict[str, Any]]) -> float:
    r_maes = sorted(
        [
            float(t.get("mae") or 0.0) / float(t.get("initial_risk") or 1.0)
            for t in trades
        ]
    )
    if not r_maes:
        return 0.0
    return r_maes[len(r_maes) // 2]


def median_mfe_r(trades: list[dict[str, Any]]) -> float:
    r_mfes = sorted(
        [
            float(t.get("mfe") or 0.0) / float(t.get("initial_risk") or 1.0)
            for t in trades
        ]
    )
    if not r_mfes:
        return 0.0
    return r_mfes[len(r_mfes) // 2]


def avg_consecutive_wins(trades: list[dict[str, Any]]) -> float:
    ordered = get_ordered_closed_trades(trades)
    streaks = []
    curr = 0
    for t in ordered:
        if _get_trade_pnl(t) > 0:
            curr += 1
        else:
            if curr > 0:
                streaks.append(curr)
            curr = 0
    if curr > 0:
        streaks.append(curr)
    return sum(streaks) / len(streaks) if streaks else 0.0


def avg_consecutive_losses(trades: list[dict[str, Any]]) -> float:
    ordered = get_ordered_closed_trades(trades)
    streaks = []
    curr = 0
    for t in ordered:
        if _get_trade_pnl(t) < 0:
            curr += 1
        else:
            if curr > 0:
                streaks.append(curr)
            curr = 0
    if curr > 0:
        streaks.append(curr)
    return sum(streaks) / len(streaks) if streaks else 0.0


def win_loss_streaks(trades: list[dict[str, Any]]) -> dict[str, list[int]]:
    ordered = get_ordered_closed_trades(trades)
    wins = []
    losses = []
    curr_w = 0
    curr_l = 0
    for t in ordered:
        pnl = _get_trade_pnl(t)
        if pnl > 0:
            curr_w += 1
            if curr_l > 0:
                losses.append(curr_l)
            curr_l = 0
        elif pnl < 0:
            curr_l += 1
            if curr_w > 0:
                wins.append(curr_w)
            curr_w = 0
    if curr_w > 0:
        wins.append(curr_w)
    if curr_l > 0:
        losses.append(curr_l)
    return {"wins": wins, "losses": losses}


def sqn(trades: list[dict[str, Any]]) -> float:
    closed = get_closed_trades(trades)
    n = len(closed)
    if n == 0:
        return 0.0
    pnls = [_get_trade_pnl(t) for t in closed]
    mean = sum(pnls) / n
    if n < 2:
        return 0.0
    var = sum((x - mean) ** 2 for x in pnls) / (n - 1)
    if var == 0:
        return 0.0
    return math.sqrt(n) * mean / math.sqrt(var)


def kelly_criterion(trades: list[dict[str, Any]]) -> float:
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    w = win_rate_fraction(closed)
    r = avg_win_loss(closed)
    if r <= 0:
        return 0.0
    return w - (1.0 - w) / r


def r_signal_to_noise(trades: list[dict[str, Any]]) -> float:
    r_mults = get_r_multiples(trades)
    if not r_mults:
        return 0.0
    avg = sum(r_mults) / len(r_mults)
    if len(r_mults) < 2:
        return 0.0
    var = sum((x - avg) ** 2 for x in r_mults) / (len(r_mults) - 1)
    if var == 0:
        return 0.0
    return avg / math.sqrt(var)


def rolling_expectancy_stability(
    trades: list[dict[str, Any]], window: int = 10
) -> float:
    closed = get_ordered_closed_trades(trades)
    if len(closed) < window:
        return 0.0
    pnls = [_get_trade_pnl(t) for t in closed]
    expectancies = []
    for i in range(len(pnls) - window + 1):
        window_pnls = pnls[i : i + window]
        expectancies.append(sum(window_pnls) / window)
    avg_exp = sum(expectancies) / len(expectancies)
    var = sum((x - avg_exp) ** 2 for x in expectancies) / (len(expectancies) - 1)
    return math.sqrt(var)


def win_after_win_probability(trades: list[dict[str, Any]]) -> float:
    ordered = get_ordered_closed_trades(trades)
    if len(ordered) < 2:
        return 0.0
    wins_after_win = 0
    total_wins = 0
    for i in range(len(ordered) - 1):
        if _get_trade_pnl(ordered[i]) > 0:
            total_wins += 1
            if _get_trade_pnl(ordered[i + 1]) > 0:
                wins_after_win += 1
    return wins_after_win / total_wins if total_wins > 0 else 0.0


def runs_test_zscore(trades: list[dict[str, Any]]) -> float:
    ordered = get_ordered_closed_trades(trades)
    n = len(ordered)
    if n < 2:
        return 0.0
    signs = [1 if _get_trade_pnl(t) > 0 else -1 for t in ordered]
    runs = 1
    for i in range(1, n):
        if signs[i] != signs[i - 1]:
            runs += 1
    n1 = sum(1 for x in signs if x == 1)
    n2 = sum(1 for x in signs if x == -1)
    if n1 == 0 or n2 == 0:
        return 0.0
    mu = (2.0 * n1 * n2) / n + 1.0
    var = (2.0 * n1 * n2 * (2.0 * n1 * n2 - n)) / (n * n * (n - 1.0))
    if var == 0:
        return 0.0
    return (runs - mu) / math.sqrt(var)


def trading_period_duration(trades: list[dict[str, Any]]) -> float:
    ordered = get_ordered_closed_trades(trades)
    if len(ordered) < 2:
        return 0.0
    ot = _parse_time(ordered[0].get("open_time") or ordered[0].get("open_timestamp"))
    ct = _parse_time(
        ordered[-1].get("close_time") or ordered[-1].get("close_timestamp")
    )
    if ot and ct:
        return (ct - ot).total_seconds() / 3600.0
    return 0.0


def calculate_spread_cost_impact(trades: list[dict[str, Any]]) -> float:
    return sum(float(t.get("spread_cost") or 0.0) for t in trades)


def calculate_slippage_impact(trades: list[dict[str, Any]]) -> float:
    return slippage_paid(trades)


def calculate_commission_impact(trades: list[dict[str, Any]]) -> float:
    return commission_paid(trades)


def adjusted_gross_profit(
    trades: list[dict[str, Any]], outlier_std_factor: float = 3.0
) -> float:
    wins = [_get_trade_pnl(t) for t in classify_trades(trades)["wins"]]
    if not wins:
        return 0.0
    avg = sum(wins) / len(wins)
    std = (
        math.sqrt(sum((x - avg) ** 2 for x in wins) / len(wins))
        if len(wins) > 1
        else 0.0
    )
    limit = avg + outlier_std_factor * std
    return sum(x for x in wins if x <= limit)


def adjusted_gross_loss(
    trades: list[dict[str, Any]], outlier_std_factor: float = 3.0
) -> float:
    losses = [_get_trade_pnl(t) for t in classify_trades(trades)["losses"]]
    if not losses:
        return 0.0
    avg = sum(losses) / len(losses)
    std = (
        math.sqrt(sum((x - avg) ** 2 for x in losses) / len(losses))
        if len(losses) > 1
        else 0.0
    )
    limit = avg - outlier_std_factor * std
    return sum(x for x in losses if x >= limit)


def adjusted_net_profit(trades: list[dict[str, Any]]) -> float:
    return adjusted_gross_profit(trades) + adjusted_gross_loss(trades)


def select_net_profit(trades: list[dict[str, Any]]) -> float:
    pnls = sorted([_get_trade_pnl(t) for t in get_closed_trades(trades)])
    if not pnls:
        return 0.0
    trim = int(len(pnls) * 0.02)
    trimmed = pnls[trim : len(pnls) - trim] if trim > 0 else pnls
    return sum(trimmed)


def select_gross_profit(trades: list[dict[str, Any]]) -> float:
    wins = sorted([_get_trade_pnl(t) for t in classify_trades(trades)["wins"]])
    if not wins:
        return 0.0
    trim = int(len(wins) * 0.02)
    trimmed = wins[: len(wins) - trim] if trim > 0 else wins
    return sum(trimmed)


def select_gross_loss(trades: list[dict[str, Any]]) -> float:
    losses = sorted([_get_trade_pnl(t) for t in classify_trades(trades)["losses"]])
    if not losses:
        return 0.0
    trim = int(len(losses) * 0.02)
    trimmed = losses[trim:] if trim > 0 else losses
    return sum(trimmed)


def return_on_account(net_prof: float, account_size: float) -> float:
    if account_size <= 0:
        return 0.0
    return (net_prof / account_size) * 100.0


def max_runup(trades: list[dict[str, Any]], initial_balance: float = 10000.0) -> float:
    curve = balance_curve(trades, initial_balance)
    if not curve:
        return 0.0
    equities = [c["equity"] for c in curve]
    running_min = equities[0]
    max_run = 0.0
    for eq in equities:
        running_min = min(running_min, eq)
        max_run = max(max_run, eq - running_min)
    return max_run


def max_runup_date(
    trades: list[dict[str, Any]], initial_balance: float = 10000.0
) -> str:
    curve = balance_curve(trades, initial_balance)
    if not curve:
        return "1970-01-01T00:00:00Z"
    equities = [c["equity"] for c in curve]
    running_min = equities[0]
    max_run = 0.0
    peak_idx = 0
    for i, eq in enumerate(equities):
        running_min = min(running_min, eq)
        run = eq - running_min
        if run > max_run:
            max_run = run
            peak_idx = i
    return str(curve[peak_idx]["timestamp"])


def calculate_period_analysis(
    trades: list[dict[str, Any]], bucket: str = "monthly"
) -> dict[str, float]:
    ordered = get_ordered_closed_trades(trades)
    results: dict[str, float] = {}
    for t in ordered:
        ct = _parse_time(t.get("close_time") or t.get("close_timestamp"))
        if not ct:
            continue
        key = ct.strftime("%Y-%m") if bucket == "monthly" else ct.strftime("%Y")
        results[key] = results.get(key, 0.0) + _get_trade_pnl(t)
    return results


def calculate_long_short_split(trades: list[dict[str, Any]]) -> dict[str, float]:
    closed = get_closed_trades(trades)
    longs = [
        t for t in closed if str(t.get("direction", "")).lower() in ("long", "buy")
    ]
    shorts = [
        t for t in closed if str(t.get("direction", "")).lower() in ("short", "sell")
    ]
    long_pnl = sum(_get_trade_pnl(t) for t in longs)
    short_pnl = sum(_get_trade_pnl(t) for t in shorts)
    return {"long_pnl": long_pnl, "short_pnl": short_pnl}


def calculate_session_performance(trades: list[dict[str, Any]]) -> dict[str, float]:
    ordered = get_ordered_closed_trades(trades)
    sessions = {"asian": 0.0, "london": 0.0, "newyork": 0.0}
    for t in ordered:
        ct = _parse_time(t.get("close_time") or t.get("close_timestamp"))
        if not ct:
            continue
        hr = ct.hour
        if 0 <= hr < 8:
            sessions["asian"] += _get_trade_pnl(t)
        elif 8 <= hr < 16:
            sessions["london"] += _get_trade_pnl(t)
        else:
            sessions["newyork"] += _get_trade_pnl(t)
    return sessions


def trade_pnl_distribution(trades: list[dict[str, Any]]) -> dict[str, float]:
    pnls = sorted([_get_trade_pnl(t) for t in get_closed_trades(trades)])
    if not pnls:
        return {}
    n = len(pnls)
    return {
        "mean": sum(pnls) / n,
        "std": math.sqrt(sum((x - (sum(pnls) / n)) ** 2 for x in pnls) / max(n - 1, 1)),
        "min": pnls[0],
        "max": pnls[-1],
        "median": pnls[n // 2],
    }


def trade_level_drawdowns(trades: list[dict[str, Any]]) -> list[float]:
    closed = get_ordered_closed_trades(trades)
    if not closed:
        return []
    balance = 10000.0
    balances = [balance]
    for t in closed:
        balance += _get_trade_pnl(t)
        balances.append(balance)
    peak = balances[0]
    drawdowns = []
    for b in balances:
        peak = max(peak, b)
        drawdowns.append(peak - b)
    return drawdowns


def max_close_to_close_drawdown(trades: list[dict[str, Any]]) -> float:
    dds = trade_level_drawdowns(trades)
    return max(dds, default=0.0)


def avg_trade_drawdown(trades: list[dict[str, Any]]) -> float:
    dds = trade_level_drawdowns(trades)
    return sum(dds) / len(dds) if dds else 0.0


def max_consecutive_drawdown_trades(trades: list[dict[str, Any]]) -> int:
    dds = trade_level_drawdowns(trades)
    max_con = 0
    curr_con = 0
    for d in dds:
        if d > 0:
            curr_con += 1
            max_con = max(max_con, curr_con)
        else:
            curr_con = 0
    return max_con


def max_close_to_close_drawdown_date(trades: list[dict[str, Any]]) -> str:
    closed = get_ordered_closed_trades(trades)
    if not closed:
        return "1970-01-01T00:00:00Z"
    dds = trade_level_drawdowns(trades)
    if not dds:
        return "1970-01-01T00:00:00Z"
    max_dd = max(dds)
    max_idx = dds.index(max_dd)
    if max_idx == 0:
        return "1970-01-01T00:00:00Z"
    t = closed[max_idx - 1]
    ct = t.get("close_time") or t.get("close_timestamp")
    parsed = _parse_time(ct)
    return (
        ct
        if isinstance(ct, str)
        else (parsed.isoformat() if parsed else "1970-01-01T00:00:00Z")
    )


def avg_trade_notional_efficiency(trades: list[dict[str, Any]]) -> float:
    closed = get_closed_trades(trades)
    if not closed:
        return 0.0
    effs = []
    for t in closed:
        pnl = abs(_get_trade_pnl(t))
        exposure = float(t.get("size", 0.0)) * float(t.get("open_price", 1.0))
        if exposure > 0:
            effs.append(pnl / exposure)
    return sum(effs) / len(effs) if effs else 0.0


def avg_return_per_risk_unit(trades: list[dict[str, Any]]) -> float:
    r_mults = get_r_multiples(trades)
    return sum(r_mults) / len(r_mults) if r_mults else 0.0


def return_per_trade_hour(trades: list[dict[str, Any]]) -> float:
    closed = get_closed_trades(trades)
    pnl = sum(_get_trade_pnl(t) for t in closed)
    tot_hours = sum(_get_trade_duration(t) for t in closed)
    return pnl / tot_hours if tot_hours > 0 else 0.0


def return_per_market_hour(trades: list[dict[str, Any]]) -> float:
    closed = get_closed_trades(trades)
    pnl = sum(_get_trade_pnl(t) for t in closed)
    tot_hours = time_in_market_duration(trades)
    return pnl / tot_hours if tot_hours > 0 else 0.0


def trades_per_day(trades: list[dict[str, Any]], duration_days: float = 30.0) -> float:
    closed = get_closed_trades(trades)
    if duration_days <= 0:
        return 0.0
    return len(closed) / duration_days


def profit_per_trade_per_day(
    trades: list[dict[str, Any]], duration_days: float = 30.0
) -> float:
    closed = get_closed_trades(trades)
    if not closed or duration_days <= 0:
        return 0.0
    return expectancy(closed) / duration_days


def mfe_efficiency(trades: list[dict[str, Any]]) -> float:
    wins = classify_trades(trades)["wins"]
    if not wins:
        return 1.0
    effs = []
    for t in wins:
        mfe = float(t.get("mfe") or 0.0)
        pnl = _get_trade_pnl(t)
        if mfe > 0:
            effs.append(pnl / mfe)
    return sum(effs) / len(effs) if effs else 1.0


def aggregate_mfe_capture_ratio(trades: list[dict[str, Any]]) -> float:
    return mfe_efficiency(trades)


def mae_efficiency(trades: list[dict[str, Any]]) -> float:
    from app.services.analytics.efficiency import loss_containment_efficiency

    return loss_containment_efficiency(trades)


def aggregate_loss_containment_efficiency(trades: list[dict[str, Any]]) -> float:
    from app.services.analytics.efficiency import loss_containment_efficiency

    return loss_containment_efficiency(trades)


def position_size_efficiency(trades: list[dict[str, Any]]) -> float:
    closed = get_closed_trades(trades)
    if len(closed) < 2:
        return 0.0
    sizes = [float(t.get("size") or 0.0) for t in closed]
    pnls = [_get_trade_pnl(t) for t in closed]
    mean_s = sum(sizes) / len(sizes)
    mean_p = sum(pnls) / len(pnls)
    num = sum((sizes[i] - mean_s) * (pnls[i] - mean_p) for i in range(len(closed)))
    den_s = sum((x - mean_s) ** 2 for x in sizes)
    den_p = sum((x - mean_p) ** 2 for x in pnls)
    if den_s == 0 or den_p == 0:
        return 0.0
    return num / math.sqrt(den_s * den_p)


def calculate_efficiency_metrics(trades: list[dict[str, Any]]) -> dict[str, float]:
    from app.services.analytics.efficiency import loss_containment_efficiency

    return {
        "mfe_efficiency": mfe_efficiency(trades),
        "mae_efficiency": loss_containment_efficiency(trades),
    }


def calculate_trade_metrics(
    trades: Any, request_id: str | None = None
) -> StandardResponse:
    """Calculate aggregate core trade metrics from normalized trade records."""
    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="calculate_trade_metrics",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        t_list = _to_trade_list(trades)
        closed = get_closed_trades(t_list)
        data = {
            "total_trades": len(closed),
            "winning_trades": winning_trades(closed),
            "losing_trades": losing_trades(closed),
            "breakeven_trades": breakeven_trades(closed),
            "long_trades": long_trades(closed),
            "short_trades": short_trades(closed),
            "win_rate": len(classify_trades(closed)["wins"]) / len(closed)
            if closed
            else 0.0,
            "avg_win": avg_win(closed),
            "avg_loss": avg_loss(closed),
            "largest_win": largest_win(closed),
            "largest_loss": largest_loss(closed),
            "median_win": median_win(closed),
            "median_loss": median_loss(closed),
            "expectancy": expectancy(closed),
            "max_consecutive_wins": max_consecutive_wins(closed),
            "max_consecutive_losses": max_consecutive_losses(closed),
            "avg_time_in_trade": avg_time_in_trade(closed),
            "median_time_in_trade": median_time_in_trade(closed),
        }
        return success_response(
            message="Successfully calculated trade metrics.",
            data=data,
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)


def calculate_analytics_for_subset(trades: list[dict[str, Any]]) -> dict[str, Any]:
    closed = get_closed_trades(trades)
    return {
        "total_trades": len(closed),
        "win_rate": len(classify_trades(closed)["wins"]) / len(closed)
        if closed
        else 0.0,
        "net_profit": sum(_get_trade_pnl(t) for t in closed),
        "gross_profit": sum(_get_trade_pnl(t) for t in closed if _get_trade_pnl(t) > 0),
        "gross_loss": sum(_get_trade_pnl(t) for t in closed if _get_trade_pnl(t) < 0),
    }


def get_analytics_overview(
    trades: Any,
    initial_balance: float = 10000.0,
    start_time: Any = None,
    end_time: Any = None,
    request_id: str | None = None,
) -> StandardResponse:
    """Calculate comprehensive analytics across all, long, and short subsets."""
    _validate_request_id(request_id)
    meta = build_metadata(
        tool_name="get_analytics_overview",
        tool_category="analytics",
        tool_risk_level="low",
        request_id=request_id,
        reads=True,
    )
    try:
        t_list = _to_trade_list(trades)
        closed = get_closed_trades(t_list)

        start_dt = _parse_time(start_time)
        end_dt = _parse_time(end_time)
        filtered = []
        for t in closed:
            ct = _parse_time(t.get("close_time") or t.get("close_timestamp"))
            if not ct:
                continue
            if start_dt and ct < start_dt:
                continue
            if end_dt and ct > end_dt:
                continue
            filtered.append(t)

        long_subset = [
            t
            for t in filtered
            if str(t.get("direction", "")).lower() in ("long", "buy")
        ]
        short_subset = [
            t
            for t in filtered
            if str(t.get("direction", "")).lower() in ("short", "sell")
        ]

        data = {
            "all": calculate_analytics_for_subset(filtered),
            "long": calculate_analytics_for_subset(long_subset),
            "short": calculate_analytics_for_subset(short_subset),
            "initial_balance": initial_balance,
        }
        return success_response(
            message="Successfully generated analytics overview.",
            data=data,
            metadata=meta,
        )
    except Exception as e:
        return response_from_exception(exception=e, metadata=meta)
