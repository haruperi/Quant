"""Correlation and Cluster Risk Engine.

Computes price return series, aligns timestamps across multiple assets,
calculates Pearson correlation matrices, detects correlation spikes,
and evaluates the marginal correlation impact of proposed trades.
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.services.risk.models import (
    CorrelationSnapshot,
    PortfolioState,
    ProposedTrade,
    RiskConfig,
    RiskDecisionStatus,
)
from app.utils.errors import ValidationError
from app.utils.logger import logger

# Constants
MIN_BARS_FOR_RETURNS = 2
MIN_SAMPLES_FOR_PEARSON = 2


class ReturnType:
    """Supported returns calculation types."""

    CLOSE_TO_CLOSE = "close_to_close"
    LOG = "log"
    OPEN_TO_CLOSE = "open_to_close"
    SIGMA_NORMALIZED = "sigma_normalized"


class CorrelationMethod:
    """Supported correlation calculation methods."""

    PEARSON = "pearson"


def _parse_bar_fields(
    bar: dict[str, Any] | object,
) -> tuple[datetime, Decimal, Decimal]:
    """Parse opening time, open price, and close price from a bar dict or object."""
    if isinstance(bar, dict):
        time_val = bar.get("time") or bar.get("timestamp")
        open_val = bar.get("open")
        close_val = bar.get("close")
    else:
        time_val = getattr(bar, "time", None) or getattr(bar, "timestamp", None)
        open_val = getattr(bar, "open", None)
        close_val = getattr(bar, "close", None)

    if time_val is None or open_val is None or close_val is None:
        msg = f"Missing required fields (time, open, close) in bar: {bar}"
        raise ValidationError(msg)

    if isinstance(time_val, str):
        try:
            from app.utils.normalization import to_utc_datetime

            dt = to_utc_datetime(time_val)
        except (ValueError, TypeError, AttributeError):
            dt = datetime.fromisoformat(time_val)
    elif isinstance(time_val, datetime):
        dt = time_val
    else:
        dt = datetime.fromtimestamp(float(time_val), UTC)

    return dt, Decimal(str(open_val)), Decimal(str(close_val))


def _calculate_open_to_close(
    parsed_bars: list[tuple[datetime, Decimal, Decimal]],
) -> dict[datetime, Decimal]:
    """Compute open-to-close returns."""
    returns = {}
    for dt, o, c in parsed_bars:
        returns[dt] = (c - o) / o if o != 0 else Decimal("0.0")
    return returns


def _calculate_close_to_close(
    parsed_bars: list[tuple[datetime, Decimal, Decimal]],
) -> dict[datetime, Decimal]:
    """Compute close-to-close returns."""
    returns = {}
    for i in range(1, len(parsed_bars)):
        dt = parsed_bars[i][0]
        prev_c = parsed_bars[i - 1][2]
        curr_c = parsed_bars[i][2]
        returns[dt] = (curr_c - prev_c) / prev_c if prev_c != 0 else Decimal("0.0")
    return returns


def _calculate_log(
    parsed_bars: list[tuple[datetime, Decimal, Decimal]],
) -> dict[datetime, Decimal]:
    """Compute logarithmic returns."""
    returns = {}
    for i in range(1, len(parsed_bars)):
        dt = parsed_bars[i][0]
        prev_c = parsed_bars[i - 1][2]
        curr_c = parsed_bars[i][2]
        if prev_c <= 0 or curr_c <= 0:
            returns[dt] = Decimal("0.0")
        else:
            ratio = float(curr_c / prev_c)
            returns[dt] = Decimal(str(math.log(ratio)))
    return returns


def _calculate_sigma_normalized(
    parsed_bars: list[tuple[datetime, Decimal, Decimal]],
) -> dict[datetime, Decimal]:
    """Compute standard-deviation normalized returns."""
    raw_rets = []
    dts = []
    for i in range(1, len(parsed_bars)):
        dt = parsed_bars[i][0]
        prev_c = parsed_bars[i - 1][2]
        curr_c = parsed_bars[i][2]
        val = (curr_c - prev_c) / prev_c if prev_c != 0 else Decimal("0.0")
        raw_rets.append(val)
        dts.append(dt)

    if not raw_rets:
        return {}

    n = len(raw_rets)
    mean_val = sum(raw_rets, Decimal("0.0")) / Decimal(n)
    var_val = sum(((r - mean_val) ** 2 for r in raw_rets), Decimal("0.0")) / Decimal(n)
    std_val = Decimal(str(math.sqrt(float(var_val))))

    returns = {}
    if std_val == 0:
        for dt in dts:
            returns[dt] = Decimal("0.0")
    else:
        for dt, r in zip(dts, raw_rets, strict=True):
            returns[dt] = r / std_val
    return returns


def _get_parsed_sorted_bars(
    bars: list[Any],
    exclude_last: bool,
) -> list[tuple[datetime, Decimal, Decimal]]:
    """Parse, sort, and optionally exclude the last bar."""
    parsed_bars = []
    for bar in bars:
        try:
            parsed_bars.append(_parse_bar_fields(bar))
        except ValidationError:
            continue

    parsed_bars.sort(key=lambda x: x[0])
    if exclude_last and parsed_bars:
        parsed_bars.pop()
    return parsed_bars


def _compute_returns_by_type(
    parsed_bars: list[tuple[datetime, Decimal, Decimal]],
    return_type: str,
) -> dict[datetime, Decimal]:
    """Helper to route return computation to specific formula."""
    if return_type == ReturnType.OPEN_TO_CLOSE:
        return _calculate_open_to_close(parsed_bars) if parsed_bars else {}

    if return_type in (
        ReturnType.CLOSE_TO_CLOSE,
        ReturnType.LOG,
        ReturnType.SIGMA_NORMALIZED,
    ):
        if len(parsed_bars) < MIN_BARS_FOR_RETURNS:
            return {}
        if return_type == ReturnType.CLOSE_TO_CLOSE:
            return _calculate_close_to_close(parsed_bars)
        if return_type == ReturnType.LOG:
            return _calculate_log(parsed_bars)
        return _calculate_sigma_normalized(parsed_bars)

    msg = f"Unsupported return type: {return_type}"
    raise ValueError(msg)


def calculate_returns(
    bars: list[Any],
    return_type: str,
    exclude_last: bool = True,
) -> dict[datetime, Decimal]:
    """Calculate returns series for a list of bars.

    Args:
        bars: List of bar dicts or objects containing time, open, and close.
        return_type: Method of calculating returns (log, close_to_close, etc.).
        exclude_last: If True, excludes the last bar.

    Returns:
        A dictionary mapping bar datetime to calculated Decimal return value.
    """
    if not bars:
        return {}

    parsed_bars = _get_parsed_sorted_bars(bars, exclude_last)
    return _compute_returns_by_type(parsed_bars, return_type)


def align_return_series(
    returns_a: dict[datetime, Decimal],
    returns_b: dict[datetime, Decimal],
) -> tuple[list[Decimal], list[Decimal]]:
    """Align two return series by their common timestamps.

    Args:
        returns_a: Dict of returns for asset A.
        returns_b: Dict of returns for asset B.

    Returns:
        Tuple of aligned returns list for A and B.
    """
    common_keys = sorted(set(returns_a.keys()) & set(returns_b.keys()))
    aligned_a = [returns_a[k] for k in common_keys]
    aligned_b = [returns_b[k] for k in common_keys]
    return aligned_a, aligned_b


def calculate_pearson(x: list[Decimal], y: list[Decimal]) -> Decimal:
    """Calculate Pearson correlation coefficient between two aligned list series.

    Args:
        x: Return series of asset A.
        y: Return series of asset B.

    Returns:
        Pearson correlation coefficient as Decimal.
    """
    n = len(x)
    if n < MIN_SAMPLES_FOR_PEARSON:
        return Decimal("0.0")

    mean_x = sum(x, Decimal("0.0")) / Decimal(n)
    mean_y = sum(y, Decimal("0.0")) / Decimal(n)

    diff_x = [val - mean_x for val in x]
    diff_y = [val - mean_y for val in y]

    numerator = sum(dx * dy for dx, dy in zip(diff_x, diff_y, strict=True))
    denom_x = sum(dx * dx for dx in diff_x)
    denom_y = sum(dy * dy for dy in diff_y)

    if denom_x == 0 or denom_y == 0:
        return Decimal("0.0")

    denom = Decimal(str(math.sqrt(float(denom_x * denom_y))))
    if denom == 0:
        return Decimal("0.0")

    return numerator / denom


def calculate_correlation_snapshot(
    market_data: dict[str, list[Any]],
    lookback: int = 50,
    timeframe: str = "M1",
    method: str = CorrelationMethod.PEARSON,
    return_type: str = ReturnType.CLOSE_TO_CLOSE,
    min_samples: int = 20,
    fallback_correlation: Decimal | None = None,
    exclude_last: bool = True,
) -> CorrelationSnapshot:
    """Compute rolling correlation matrix for multiple symbol price series.

    Args:
        market_data: Dict of lists of bars per symbol.
        lookback: Maximum number of return samples to use after alignment.
        timeframe: Bar timeframe string (e.g. M1, M5, H1).
        method: Correlation formula method (Pearson).
        return_type: Return type formula to compute.
        min_samples: Minimum required aligned samples to avoid failure.
        fallback_correlation: Fallback value if samples are insufficient.
        exclude_last: Exclude the last bar.

    Returns:
        CorrelationSnapshot containing the correlation matrix and details.

    Raises:
        ValidationError: If samples are insufficient and fallback is not set.
    """
    symbols = sorted(market_data.keys())
    returns_db: dict[str, dict[datetime, Decimal]] = {}
    for sym in symbols:
        returns_db[sym] = calculate_returns(market_data[sym], return_type, exclude_last)

    matrix: dict[str, dict[str, Decimal]] = {}
    fallback_applied = False
    total_aligned_samples = 0

    for i, s1 in enumerate(symbols):
        if s1 not in matrix:
            matrix[s1] = {}
        matrix[s1][s1] = Decimal("1.0")

        for s2 in symbols[i + 1 :]:
            if s2 not in matrix:
                matrix[s2] = {}

            aligned_1, aligned_2 = align_return_series(returns_db[s1], returns_db[s2])
            n = len(aligned_1)
            total_aligned_samples = max(total_aligned_samples, n)

            if n > lookback:
                aligned_1 = aligned_1[-lookback:]
                aligned_2 = aligned_2[-lookback:]
                n = lookback

            if n < min_samples:
                if fallback_correlation is not None:
                    corr = Decimal(str(fallback_correlation))
                    fallback_applied = True
                else:
                    msg = (
                        f"Insufficient aligned sample size ({n} < {min_samples}) "
                        f"for pair {s1}-{s2}."
                    )
                    raise ValidationError(msg)
            else:
                corr = calculate_pearson(aligned_1, aligned_2)

            matrix[s1][s2] = corr
            matrix[s2][s1] = corr

    return CorrelationSnapshot(
        matrix=matrix,
        lookback=lookback,
        timeframe=timeframe,
        method=method,
        sample_count=total_aligned_samples,
        fallback_status=fallback_applied,
    )


def calculate_portfolio_returns(
    portfolio_state: PortfolioState,
    market_data: dict[str, list[Any]],
    return_type: str = ReturnType.CLOSE_TO_CLOSE,
    exclude_last: bool = True,
) -> dict[datetime, Decimal]:
    """Calculate weighted historical portfolio returns.

    Args:
        portfolio_state: Active portfolio state containing positions.
        market_data: Historical bars for positions' symbols.
        return_type: Return calculation method.
        exclude_last: Exclude the last bar.

    Returns:
        Dict mapping datetime to Decimal return value.
    """
    positions = portfolio_state.positions
    if not positions:
        return {}

    pos_returns: dict[str, dict[datetime, Decimal]] = {}
    total_gross_size = sum(abs(pos.quantity) for pos in positions)

    if total_gross_size == 0:
        return {}

    weights: dict[str, Decimal] = {}
    for pos in positions:
        pos_returns[pos.symbol] = calculate_returns(
            market_data.get(pos.symbol, []), return_type, exclude_last
        )
        weights[pos.symbol] = abs(pos.quantity) / total_gross_size

    common_times = None
    for rets in pos_returns.values():
        if common_times is None:
            common_times = set(rets.keys())
        else:
            common_times &= set(rets.keys())

    if not common_times:
        return {}

    portfolio_returns: dict[datetime, Decimal] = {}
    for t in sorted(common_times):
        weighted_ret = Decimal("0.0")
        for pos in positions:
            direction = pos.direction.lower()
            sign = Decimal("1.0") if direction in {"buy", "long"} else Decimal("-1.0")
            weighted_ret += weights[pos.symbol] * sign * pos_returns[pos.symbol][t]
        portfolio_returns[t] = weighted_ret

    return portfolio_returns


def calculate_marginal_correlation(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade,
    market_data: dict[str, list[Any]],
    lookback: int = 50,
    return_type: str = ReturnType.CLOSE_TO_CLOSE,
    min_samples: int = 20,
    fallback_correlation: Decimal | None = None,
    exclude_last: bool = True,
) -> tuple[Decimal, bool]:
    """Calculate marginal correlation coefficient of proposed trade with portfolio.

    Args:
        portfolio_state: Active portfolio state containing open positions.
        proposed_trade: Candidate proposed trade.
        market_data: Historical bars for active symbols + candidate symbol.
        lookback: Maximum lookback elements to use.
        return_type: Return type formula.
        min_samples: Minimum required samples.
        fallback_correlation: Fallback value if samples are insufficient.
        exclude_last: Exclude the last bar.

    Returns:
        Tuple of (marginal_correlation, fallback_status).
    """
    candidate_sym = proposed_trade.symbol
    candidate_rets = calculate_returns(
        market_data.get(candidate_sym, []), return_type, exclude_last
    )

    if not portfolio_state.positions:
        return Decimal("0.0"), False

    port_rets = calculate_portfolio_returns(
        portfolio_state, market_data, return_type, exclude_last
    )

    aligned_p, aligned_c = align_return_series(port_rets, candidate_rets)
    n = len(aligned_p)

    if n > lookback:
        aligned_p = aligned_p[-lookback:]
        aligned_c = aligned_c[-lookback:]
        n = lookback

    if n < min_samples:
        if fallback_correlation is not None:
            return Decimal(str(fallback_correlation)), True
        msg = (
            f"Insufficient aligned sample size ({n} < {min_samples}) "
            f"between portfolio and proposed trade asset {candidate_sym}."
        )
        raise ValidationError(msg)

    corr = calculate_pearson(aligned_p, aligned_c)

    trade_side = proposed_trade.side.lower()
    if trade_side in {"sell", "short"}:
        corr = -corr

    return corr, False


def calculate_correlation_multiplier(
    marginal_correlation: Decimal,
    config_multiplier_factor: Decimal = Decimal("0.5"),
) -> Decimal:
    """Calculate the correlation-adjusted sizing multiplier.

    Args:
        marginal_correlation: Pearson correlation to portfolio.
        config_multiplier_factor: Scaling factor (e.g. 0.5 means a correlation
            of 1.0 reduces sizing by 50%).

    Returns:
        Sizing multiplier between 0.1 and 1.0.
    """
    if marginal_correlation <= 0:
        return Decimal("1.0")
    mult = Decimal("1.0") - marginal_correlation * config_multiplier_factor
    return max(Decimal("0.1"), min(Decimal("1.0"), mult))


def detect_correlation_spikes(
    snapshot: CorrelationSnapshot,
    threshold: Decimal,
) -> list[tuple[str, str, Decimal]]:
    """Detect asset pairs whose correlation exceeds the given threshold.

    Args:
        snapshot: The CorrelationSnapshot containing the correlation matrix.
        threshold: Correlation threshold above which it is considered a spike.

    Returns:
        A list of tuples of (symbol_a, symbol_b, correlation_value)
        where symbol_a < symbol_b.
    """
    spikes = []
    symbols = sorted(snapshot.matrix.keys())
    for i, s1 in enumerate(symbols):
        for s2 in symbols[i + 1 :]:
            corr = snapshot.matrix[s1].get(s2)
            if corr is not None and abs(corr) >= threshold:
                spikes.append((s1, s2, corr))
    return spikes


def _get_symbol_gross_exposure(
    symbol: str,
    quantity: Decimal,
    _price: Decimal,
    market_context: dict[str, Any],
    account_ccy: str,
) -> Decimal:
    """Calculate gross exposure of a position/trade in account currency."""
    c_size_raw = market_context.get(f"{symbol}_contract_size") or market_context.get(
        "contract_size", "100000.0"
    )
    contract_size = Decimal(str(c_size_raw))

    from app.services.risk.exposure import (
        _resolve_base_quote,
        _resolve_conversion_rate,
    )

    base_ccy, _ = _resolve_base_quote(symbol, market_context)

    base_exposure = quantity * contract_size
    rate = _resolve_conversion_rate(base_ccy, account_ccy, market_context)
    return abs(base_exposure * rate)


def _get_all_symbols(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
) -> set[str]:
    """Collect unique symbols from positions and proposed trade."""
    symbols = {pos.symbol for pos in portfolio_state.positions}
    if proposed_trade is not None:
        symbols.add(proposed_trade.symbol)
    return symbols


def _calculate_symbol_exposures(
    symbols: set[str],
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    account_ccy: str,
) -> dict[str, Decimal]:
    """Calculate gross exposure in account currency for each symbol."""
    sym_exposures: dict[str, Decimal] = {}
    for sym in symbols:
        gross = Decimal("0.0")
        for pos in portfolio_state.positions:
            if pos.symbol == sym:
                gross += _get_symbol_gross_exposure(
                    pos.symbol,
                    pos.quantity,
                    pos.current_price,
                    market_context,
                    account_ccy,
                )
        if proposed_trade is not None and proposed_trade.symbol == sym:
            p_price = proposed_trade.price
            if p_price <= 0:
                p_price = Decimal(str(market_context.get(f"{sym}_price", "1.0")))
            gross += _get_symbol_gross_exposure(
                sym, proposed_trade.volume, p_price, market_context, account_ccy
            )
        sym_exposures[sym] = gross
    return sym_exposures


def _build_adjacency_list(
    symbols_list: list[str],
    snapshot: CorrelationSnapshot,
    threshold: Decimal,
) -> dict[str, set[str]]:
    """Build adjacency list based on pairwise correlation threshold."""
    adj: dict[str, set[str]] = {s: set() for s in symbols_list}
    for i, s1 in enumerate(symbols_list):
        for s2 in symbols_list[i + 1 :]:
            corr = snapshot.matrix.get(s1, {}).get(s2)
            if corr is not None and abs(corr) >= threshold:
                adj[s1].add(s2)
                adj[s2].add(s1)
    return adj


def _find_connected_components(
    symbols_list: list[str],
    adj: dict[str, set[str]],
) -> list[list[str]]:
    """Group symbols into connected components (clusters)."""
    visited = set()
    clusters: list[list[str]] = []
    for s in symbols_list:
        if s not in visited:
            comp = []
            queue = [s]
            visited.add(s)
            while queue:
                curr = queue.pop(0)
                comp.append(curr)
                for neighbor in adj[curr]:
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            clusters.append(comp)
    return clusters


def calculate_cluster_exposures(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    snapshot: CorrelationSnapshot,
    threshold: Decimal,
    market_context: dict[str, Any],
) -> dict[str, Decimal]:
    """Calculate gross exposure in account currency for correlated asset clusters.

    Assets are grouped into the same cluster if their pairwise correlation
    magnitude is >= threshold.

    Args:
        portfolio_state: Current portfolio state.
        proposed_trade: Proposed trade to include in projected exposure.
        snapshot: CorrelationSnapshot containing the correlation matrix.
        threshold: Pairwise correlation threshold to group assets.
        market_context: Symbol market context (contract sizes, conversions, etc.).

    Returns:
        A dict mapping cluster identifier ("Cluster_0", "Cluster_1", etc.)
        to its gross exposure.
    """
    symbols = _get_all_symbols(portfolio_state, proposed_trade)
    account_ccy = portfolio_state.currency.upper()
    sym_exposures = _calculate_symbol_exposures(
        symbols, portfolio_state, proposed_trade, market_context, account_ccy
    )

    symbols_list = sorted(symbols)
    adj = _build_adjacency_list(symbols_list, snapshot, threshold)
    clusters = _find_connected_components(symbols_list, adj)

    # Sort components deterministically
    sorted_clusters = []
    for comp in clusters:
        sorted_clusters.append(sorted(comp))
    sorted_clusters.sort(key=lambda x: x[0])

    cluster_exposures: dict[str, Decimal] = {}
    for idx, comp in enumerate(sorted_clusters):
        c_name = f"Cluster_{idx}"
        c_exp = sum((sym_exposures[sym] for sym in comp), Decimal("0.0"))
        cluster_exposures[c_name] = c_exp

    return cluster_exposures


def evaluate_proposed_trade_correlation(
    proposed_trade: ProposedTrade,
    portfolio_state: PortfolioState,
    snapshot: CorrelationSnapshot,
    config: RiskConfig,
    market_context: dict[str, Any],
) -> tuple[RiskDecisionStatus, Decimal, str]:
    """Evaluate a proposed trade's correlation impact and recommend action.

    Checks marginal correlation against threshold to recommend APPROVE,
    REDUCE_SIZE, or REJECT.

    Args:
        proposed_trade: Proposed trade.
        portfolio_state: Current portfolio state.
        snapshot: CorrelationSnapshot.
        config: RiskConfig.
        market_context: Market context dictionary.

    Returns:
        Tuple of (status, adjusted_volume, message)
    """
    if not portfolio_state.positions:
        return (
            RiskDecisionStatus.APPROVE,
            proposed_trade.volume,
            "Portfolio has no active positions.",
        )

    market_data = market_context.get("market_data")
    if not isinstance(market_data, dict):
        market_data = market_context

    env = market_context.get("environment", "local")
    is_live = env in {
        "paper",
        "shadow",
        "live_readonly",
        "micro_live",
        "full_live",
    } or getattr(config, "allow_live_execution", False)
    fallback_val = Decimal("1.0") if is_live else Decimal("0.0")

    min_samples = int(
        market_context.get(
            "min_correlation_samples",
            getattr(config, "min_correlation_samples", 20),
        )
    )

    try:
        marginal_corr, _ = calculate_marginal_correlation(
            portfolio_state=portfolio_state,
            proposed_trade=proposed_trade,
            market_data=market_data,
            lookback=snapshot.lookback,
            return_type=snapshot.method
            if snapshot.method
            in {
                ReturnType.CLOSE_TO_CLOSE,
                ReturnType.LOG,
                ReturnType.OPEN_TO_CLOSE,
                ReturnType.SIGMA_NORMALIZED,
            }
            else ReturnType.CLOSE_TO_CLOSE,
            min_samples=min_samples,
            fallback_correlation=fallback_val,
            exclude_last=True,
        )
    except (ValueError, TypeError, KeyError, ValidationError) as e:
        logger.warning(f"Failed to calculate marginal correlation, falling back: {e}")
        marginal_corr = fallback_val

    threshold = config.correlation_threshold
    reject_thresh = min(
        Decimal("0.95"),
        max(Decimal("0.80"), threshold * Decimal("1.5")),
    )

    if abs(marginal_corr) >= reject_thresh:
        return (
            RiskDecisionStatus.REJECT,
            Decimal("0.0"),
            f"Marginal correlation {marginal_corr:.2f} exceeds "
            f"hard rejection ceiling of {reject_thresh:.2f}.",
        )

    if abs(marginal_corr) >= threshold:
        mult = calculate_correlation_multiplier(
            marginal_corr,
            config_multiplier_factor=Decimal("0.5"),
        )
        adjusted_vol = proposed_trade.volume * mult

        sym = proposed_trade.symbol
        volume_step = market_context.get(f"{sym}_volume_step") or market_context.get(
            "volume_step"
        )
        if volume_step is not None:
            v_step = Decimal(str(volume_step))
            adjusted_vol = (adjusted_vol / v_step).quantize(
                Decimal(1), rounding="ROUND_DOWN"
            ) * v_step

        return (
            RiskDecisionStatus.REDUCE_SIZE,
            adjusted_vol,
            f"Marginal correlation {marginal_corr:.2f} exceeds "
            f"threshold {threshold:.2f}. Sizing reduced by factor of "
            f"{mult:.2f}.",
        )

    return (
        RiskDecisionStatus.APPROVE,
        proposed_trade.volume,
        f"Marginal correlation {marginal_corr:.2f} within safe "
        f"threshold {threshold:.2f}.",
    )


def calculate_correlation_matrix(
    market_data: dict[str, list[Any]],
    lookback: int = 50,
    timeframe: str = "M1",
    method: str = CorrelationMethod.PEARSON,
    return_type: str = ReturnType.CLOSE_TO_CLOSE,
    min_samples: int = 20,
    fallback_correlation: Decimal | None = None,
    exclude_last: bool = True,
) -> dict[str, dict[str, Decimal]]:
    """Compute rolling correlation matrix for multiple symbol price series.

    Args:
        market_data: Dict of lists of bars per symbol.
        lookback: Maximum number of return samples to use after alignment.
        timeframe: Bar timeframe string (e.g. M1, M5, H1).
        method: Correlation formula method (Pearson).
        return_type: Return type formula to compute.
        min_samples: Minimum required aligned samples to avoid failure.
        fallback_correlation: Fallback value if samples are insufficient.
        exclude_last: Exclude the last bar.

    Returns:
        dict: Pairwise correlation matrix.
    """
    snapshot = calculate_correlation_snapshot(
        market_data=market_data,
        lookback=lookback,
        timeframe=timeframe,
        method=method,
        return_type=return_type,
        min_samples=min_samples,
        fallback_correlation=fallback_correlation,
        exclude_last=exclude_last,
    )
    return snapshot.matrix


def calculate_correlation_impact(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade,
    market_data: dict[str, list[Any]],
    lookback: int = 50,
    return_type: str = ReturnType.CLOSE_TO_CLOSE,
    min_samples: int = 20,
    fallback_correlation: Decimal | None = None,
    exclude_last: bool = True,
) -> Decimal:
    """Compute marginal correlation impact of a proposed trade before approval.

    Args:
        portfolio_state: Current portfolio state.
        proposed_trade: Candidate proposed trade.
        market_data: Historical price bars for symbols.
        lookback: Maximum number of return samples.
        return_type: Return formula type.
        min_samples: Minimum required samples.
        fallback_correlation: Fallback value if samples are insufficient.
        exclude_last: Exclude the last bar.

    Returns:
        Decimal: Pearson marginal correlation coefficient between the portfolio returns
            and the proposed trade asset returns (adjusted for trade direction).
    """
    corr, _ = calculate_marginal_correlation(
        portfolio_state=portfolio_state,
        proposed_trade=proposed_trade,
        market_data=market_data,
        lookback=lookback,
        return_type=return_type,
        min_samples=min_samples,
        fallback_correlation=fallback_correlation,
        exclude_last=exclude_last,
    )
    return corr


def calculate_cluster_exposure(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    snapshot: CorrelationSnapshot,
    threshold: Decimal,
    market_context: dict[str, Any],
) -> dict[str, Decimal]:
    """Calculate gross exposure for correlated asset clusters (singular alias)."""
    return calculate_cluster_exposures(
        portfolio_state=portfolio_state,
        proposed_trade=proposed_trade,
        snapshot=snapshot,
        threshold=threshold,
        market_context=market_context,
    )


def calculate_symbol_cluster_exposure(
    symbol: str,
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    snapshot: CorrelationSnapshot,
    threshold: Decimal,
    market_context: dict[str, Any],
) -> Decimal:
    """Calculate gross exposure for the cluster containing a specific symbol.

    Args:
        symbol: The target symbol to evaluate.
        portfolio_state: Current portfolio state.
        proposed_trade: Proposed trade to include in projected exposure.
        snapshot: CorrelationSnapshot containing the correlation matrix.
        threshold: Pairwise correlation threshold to group assets.
        market_context: Symbol market context (contract sizes, conversions, etc.).

    Returns:
        Decimal: Gross exposure of the correlated cluster containing the symbol.
    """
    symbols = _get_all_symbols(portfolio_state, proposed_trade)
    if symbol not in symbols:
        return Decimal("0.0")

    account_ccy = portfolio_state.currency.upper()
    sym_exposures = _calculate_symbol_exposures(
        symbols, portfolio_state, proposed_trade, market_context, account_ccy
    )

    symbols_list = sorted(symbols)
    adj = _build_adjacency_list(symbols_list, snapshot, threshold)
    clusters = _find_connected_components(symbols_list, adj)

    for comp in clusters:
        if symbol in comp:
            return sum((sym_exposures[sym] for sym in comp), Decimal("0.0"))

    return Decimal("0.0")


class CorrelationEngine:
    """Orchestrator for correlation calculations and cluster risk analysis."""

    def __init__(self, config: RiskConfig | None = None) -> None:
        """Initialize with active risk configuration.

        Args:
            config: Optional active risk config profile.
        """
        self.config = config

    def calculate_returns(
        self,
        bars: list[Any],
        return_type: str,
        exclude_last: bool = True,
    ) -> dict[datetime, Decimal]:
        """Calculate returns series for a list of bars."""
        return calculate_returns(bars, return_type, exclude_last)

    def align_return_series(
        self,
        returns_a: dict[datetime, Decimal],
        returns_b: dict[datetime, Decimal],
    ) -> tuple[list[Decimal], list[Decimal]]:
        """Align two return series by common timestamps."""
        return align_return_series(returns_a, returns_b)

    def calculate_correlation_matrix(
        self,
        market_data: dict[str, list[Any]],
        lookback: int = 50,
        timeframe: str = "M1",
        method: str = CorrelationMethod.PEARSON,
        return_type: str = ReturnType.CLOSE_TO_CLOSE,
        min_samples: int = 20,
        fallback_correlation: Decimal | None = None,
        exclude_last: bool = True,
    ) -> dict[str, dict[str, Decimal]]:
        """Compute rolling correlation matrix for multiple symbol price series."""
        return calculate_correlation_matrix(
            market_data=market_data,
            lookback=lookback,
            timeframe=timeframe,
            method=method,
            return_type=return_type,
            min_samples=min_samples,
            fallback_correlation=fallback_correlation,
            exclude_last=exclude_last,
        )

    def calculate_correlation_impact(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade,
        market_data: dict[str, list[Any]],
        lookback: int = 50,
        return_type: str = ReturnType.CLOSE_TO_CLOSE,
        min_samples: int = 20,
        fallback_correlation: Decimal | None = None,
        exclude_last: bool = True,
    ) -> Decimal:
        """Compute marginal correlation impact of a proposed trade."""
        return calculate_correlation_impact(
            portfolio_state=portfolio_state,
            proposed_trade=proposed_trade,
            market_data=market_data,
            lookback=lookback,
            return_type=return_type,
            min_samples=min_samples,
            fallback_correlation=fallback_correlation,
            exclude_last=exclude_last,
        )

    def calculate_cluster_exposure(
        self,
        portfolio_state: PortfolioState,
        proposed_trade: ProposedTrade | None,
        snapshot: CorrelationSnapshot,
        threshold: Decimal,
        market_context: dict[str, Any],
    ) -> dict[str, Decimal]:
        """Calculate gross exposure for correlated asset clusters."""
        return calculate_cluster_exposure(
            portfolio_state=portfolio_state,
            proposed_trade=proposed_trade,
            snapshot=snapshot,
            threshold=threshold,
            market_context=market_context,
        )
