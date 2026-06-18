"""Value-at-Risk (VaR) and Expected Shortfall (ES) Engine.

Computes parametric and historical VaR and Expected Shortfall,
calculates covariance matrices (with EWMA and shrinkage options),
and performs Euler risk decomposition (marginal and component risk contributions).
"""

from __future__ import annotations

import math
from datetime import datetime
from decimal import Decimal
from statistics import NormalDist
from typing import Any

from app.services.risk.models import (
    ExpectedShortfallSnapshot,
    PortfolioState,
    ProposedTrade,
    RiskConfig,
    VaRSnapshot,
)
from app.utils.errors import ValidationError

MIN_SAMPLES_FOR_COVARIANCE = 2


class VaRMethod:
    """Supported Value-at-Risk computation methods."""

    PARAMETRIC = "parametric"
    HISTORICAL = "historical"


class ExpectedShortfallMethod:
    """Supported Expected Shortfall computation methods."""

    PARAMETRIC = "parametric"
    HISTORICAL = "historical"


def calculate_covariance(x: list[Decimal], y: list[Decimal]) -> Decimal:
    """Calculate sample covariance between two aligned series.

    Args:
        x: First returns list.
        y: Second returns list.

    Returns:
        The calculated sample covariance as Decimal.
    """
    n = len(x)
    if n < MIN_SAMPLES_FOR_COVARIANCE:
        return Decimal("0.0")

    mean_x = sum(x, Decimal("0.0")) / Decimal(n)
    mean_y = sum(y, Decimal("0.0")) / Decimal(n)

    sum_prod = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y, strict=True))
    return sum_prod / Decimal(n - 1)


def calculate_ewma_covariance(
    x: list[Decimal],
    y: list[Decimal],
    decay: Decimal = Decimal("0.94"),
) -> Decimal:
    """Calculate Exponentially Weighted Moving Average (EWMA) covariance.

    Args:
        x: First returns list.
        y: Second returns list.
        decay: Decay factor lambda (typically 0.94).

    Returns:
        The calculated EWMA covariance as Decimal.
    """
    n = len(x)
    if n < MIN_SAMPLES_FOR_COVARIANCE:
        return Decimal("0.0")

    mean_x = sum(x, Decimal("0.0")) / Decimal(n)
    mean_y = sum(y, Decimal("0.0")) / Decimal(n)

    weights = [decay ** (n - 1 - i) for i in range(n)]
    sum_weights = sum(weights, Decimal("0.0"))
    if sum_weights == Decimal("0.0"):
        return Decimal("0.0")

    weighted_sum = sum(
        (
            (w * (xi - mean_x) * (yi - mean_y))
            for w, xi, yi in zip(weights, x, y, strict=True)
        ),
        Decimal("0.0"),
    )

    return weighted_sum / sum_weights


def calculate_covariance_matrix(
    returns_db: dict[str, list[Decimal]],
    method: str = "parametric",
    ewma_decay: Decimal = Decimal("0.94"),
) -> dict[str, dict[str, Decimal]]:
    """Compute pairwise covariance matrix for return series.

    Args:
        returns_db: A dictionary mapping symbol to list of aligned returns.
        method: Method used ('parametric' or 'ewma').
        ewma_decay: EWMA decay factor.

    Returns:
        Covariance matrix mapping symbol to dictionary of covariances.
    """
    symbols = sorted(returns_db.keys())
    matrix: dict[str, dict[str, Decimal]] = {}

    for i, s1 in enumerate(symbols):
        if s1 not in matrix:
            matrix[s1] = {}
        for s2 in symbols[i:]:
            if s2 not in matrix:
                matrix[s2] = {}

            if method == "ewma":
                cov = calculate_ewma_covariance(
                    returns_db[s1], returns_db[s2], decay=ewma_decay
                )
            else:
                cov = calculate_covariance(returns_db[s1], returns_db[s2])

            matrix[s1][s2] = cov
            matrix[s2][s1] = cov

    return matrix


def shrink_covariance_matrix(
    matrix: dict[str, dict[str, Decimal]],
    shrinkage_intensity: Decimal = Decimal("0.1"),
) -> dict[str, dict[str, Decimal]]:
    """Apply shrinkage towards diagonal target (constant variance target).

    Args:
        matrix: Covariance matrix.
        shrinkage_intensity: Shrinkage intensity delta (0.0 to 1.0).

    Returns:
        The shrunk covariance matrix.
    """
    symbols = sorted(matrix.keys())
    shrunk: dict[str, dict[str, Decimal]] = {}

    for s1 in symbols:
        shrunk[s1] = {}
        for s2 in symbols:
            val = matrix[s1][s2]
            if s1 == s2:
                shrunk[s1][s2] = val
            else:
                shrunk[s1][s2] = val * (Decimal("1.0") - shrinkage_intensity)

    return shrunk


def calculate_portfolio_volatility(
    weights: dict[str, Decimal],
    matrix: dict[str, dict[str, Decimal]],
) -> Decimal:
    """Calculate portfolio volatility using signed weights and covariance matrix.

    Args:
        weights: Dictionary mapping symbol to signed weight.
        matrix: Covariance matrix.

    Returns:
        Portfolio volatility as Decimal.
    """
    symbols = sorted(weights.keys())
    variance = Decimal("0.0")

    for s1 in symbols:
        w1 = weights[s1]
        for s2 in symbols:
            w2 = weights[s2]
            cov = matrix[s1].get(s2, Decimal("0.0"))
            variance += w1 * w2 * cov

    if variance <= 0:
        return Decimal("0.0")

    return Decimal(str(math.sqrt(float(variance))))


def validate_covariance_matrix(matrix: dict[str, dict[str, Decimal]]) -> None:
    """Verify covariance matrix has non-negative diagonal values and is symmetric.

    Args:
        matrix: Covariance matrix.

    Raises:
        ValidationError: If covariance matrix validation checks fail.
    """
    for s1, row1 in matrix.items():
        diag = row1.get(s1, Decimal("0.0"))
        if diag < 0:
            msg = f"Invalid covariance matrix: negative variance for {s1} ({diag})"
            raise ValidationError(msg)
        for s2, val in row1.items():
            val2 = matrix[s2].get(s1)
            if val is None or val2 is None:
                msg = f"Invalid covariance matrix: missing elements for {s1}-{s2}"
                raise ValidationError(msg)
            if abs(val - val2) > Decimal("1e-6"):
                msg = f"Invalid covariance matrix: asymmetry detected between {s1}-{s2}"
                raise ValidationError(msg)


def calculate_risk_contributions(
    weights: dict[str, Decimal],
    matrix: dict[str, dict[str, Decimal]],
    portfolio_vol: Decimal,
    confidence: Decimal,
    total_gross_exposure: Decimal,
) -> tuple[dict[str, Decimal], dict[str, Decimal]]:
    """Calculate marginal and component risk contributions.

    Args:
        weights: Signed portfolio weights.
        matrix: Covariance matrix.
        portfolio_vol: Portfolio volatility.
        confidence: Confidence level (e.g. 0.95).
        total_gross_exposure: Total portfolio gross exposure in account currency.

    Returns:
        Tuple containing marginal risk contributions (MRC) and component risk
        contributions (CRC) per symbol.
    """
    symbols = sorted(weights.keys())
    mrc: dict[str, Decimal] = {}
    crc: dict[str, Decimal] = {}

    nd = NormalDist()
    z = Decimal(str(nd.inv_cdf(float(confidence))))

    if portfolio_vol <= 0:
        for s in symbols:
            mrc[s] = Decimal("0.0")
            crc[s] = Decimal("0.0")
        return mrc, crc

    for s1 in symbols:
        sigma_w_i = sum(
            matrix[s1].get(s2, Decimal("0.0")) * weights[s2] for s2 in symbols
        )
        mrc_val = sigma_w_i / portfolio_vol
        mrc[s1] = mrc_val

        # Component VaR = w_i * Z_alpha * MRC_i * Total Gross Exposure
        crc_val = weights[s1] * z * mrc_val * total_gross_exposure
        crc[s1] = crc_val

    return mrc, crc


def get_position_signed_exposure(
    symbol: str,
    quantity: Decimal,
    direction: str,
    market_context: dict[str, Any],
    account_ccy: str,
) -> Decimal:
    """Calculate signed exposure of a position in account currency.

    Args:
        symbol: Position symbol.
        quantity: Position volume/quantity in lots.
        direction: Direction ('long' or 'short').
        market_context: Market data environment.
        account_ccy: Account base currency.

    Returns:
        Signed exposure value.
    """
    c_size_raw = market_context.get(f"{symbol}_contract_size") or market_context.get(
        "contract_size", "100000.0"
    )
    contract_size = Decimal(str(c_size_raw))

    from app.services.risk.exposure import (
        _resolve_base_quote,
        _resolve_conversion_rate,
    )

    base_ccy, _ = _resolve_base_quote(symbol, market_context)

    sign = Decimal("1.0") if direction.lower() in {"buy", "long"} else Decimal("-1.0")
    base_exposure = abs(quantity) * contract_size * sign
    rate = _resolve_conversion_rate(base_ccy, account_ccy, market_context)
    return base_exposure * rate


def get_proposed_trade_signed_exposure(
    proposed_trade: ProposedTrade,
    market_context: dict[str, Any],
    account_ccy: str,
) -> Decimal:
    """Calculate signed exposure of a proposed trade in account currency.

    Args:
        proposed_trade: Candidate proposed trade.
        market_context: Market data environment.
        account_ccy: Account base currency.

    Returns:
        Signed exposure value.
    """
    symbol = proposed_trade.symbol
    c_size_raw = market_context.get(f"{symbol}_contract_size") or market_context.get(
        "contract_size", "100000.0"
    )
    contract_size = Decimal(str(c_size_raw))

    from app.services.risk.exposure import (
        _resolve_base_quote,
        _resolve_conversion_rate,
    )

    base_ccy, _ = _resolve_base_quote(symbol, market_context)

    sign = (
        Decimal("1.0")
        if proposed_trade.side.lower() in {"buy", "long"}
        else Decimal("-1.0")
    )
    base_exposure = proposed_trade.volume * contract_size * sign
    rate = _resolve_conversion_rate(base_ccy, account_ccy, market_context)
    return base_exposure * rate


def align_multiple_return_series(
    returns_db: dict[str, dict[datetime, Decimal]],
) -> dict[str, list[Decimal]]:
    """Align multiple return series by their common timestamps.

    Args:
        returns_db: Dictionary of returns series per symbol.

    Returns:
        Dictionary of aligned return series list per symbol.
    """
    if not returns_db:
        return {}

    common_times = None
    for rets in returns_db.values():
        if common_times is None:
            common_times = set(rets.keys())
        else:
            common_times &= set(rets.keys())

    if not common_times:
        return {s: [] for s in returns_db}

    sorted_times = sorted(common_times)
    aligned: dict[str, list[Decimal]] = {}
    for s, rets in returns_db.items():
        aligned[s] = [rets[t] for t in sorted_times]
    return aligned


def calculate_parametric_var_es(
    weights: dict[str, Decimal],
    matrix: dict[str, dict[str, Decimal]],
    confidence: Decimal,
    total_gross_exposure: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    """Calculate parametric portfolio VaR and Expected Shortfall.

    Args:
        weights: Signed portfolio weights.
        matrix: Covariance matrix.
        confidence: Confidence level.
        total_gross_exposure: Total portfolio gross exposure in account currency.

    Returns:
        Tuple of (portfolio_volatility, parametric_var, parametric_expected_shortfall).
    """
    vol = calculate_portfolio_volatility(weights, matrix)
    nd = NormalDist()
    z = Decimal(str(nd.inv_cdf(float(confidence))))

    var_val = z * vol * total_gross_exposure

    z_f = float(z)
    phi_z = Decimal(str(math.exp(-0.5 * z_f * z_f) / math.sqrt(2.0 * math.pi)))

    tail_prob = Decimal("1.0") - confidence
    if tail_prob <= 0:
        es_val = var_val
    else:
        es_val = vol * (phi_z / tail_prob) * total_gross_exposure

    return vol, var_val, es_val


def calculate_historical_var_es(
    aligned_returns: dict[str, list[Decimal]],
    weights: dict[str, Decimal],
    confidence: Decimal,
    total_gross_exposure: Decimal,
) -> tuple[Decimal, Decimal]:
    """Calculate historical portfolio VaR and Expected Shortfall.

    Args:
        aligned_returns: Aligned returns per symbol.
        weights: Signed portfolio weights.
        confidence: Confidence level.
        total_gross_exposure: Total portfolio gross exposure in account currency.

    Returns:
        Tuple of (historical_var, historical_expected_shortfall).
    """
    if not aligned_returns:
        return Decimal("0.0"), Decimal("0.0")

    first_sym = next(iter(aligned_returns))
    n = len(aligned_returns[first_sym])
    if n == 0:
        return Decimal("0.0"), Decimal("0.0")

    port_returns = []
    symbols = sorted(weights.keys())
    for i in range(n):
        r_p = sum(weights[s] * aligned_returns[s][i] for s in symbols)
        port_returns.append(r_p)

    port_returns.sort()

    idx = max(0, min(n - 1, int((Decimal("1.0") - confidence) * Decimal(n))))
    var_pct = -port_returns[idx]

    tail_returns = port_returns[: idx + 1]
    if not tail_returns:
        es_pct = var_pct
    else:
        es_pct = -sum(tail_returns, Decimal("0.0")) / Decimal(len(tail_returns))

    return var_pct * total_gross_exposure, es_pct * total_gross_exposure


def _compute_exposures_and_weights(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    account_ccy: str,
) -> tuple[Decimal, dict[str, Decimal]]:
    """Compute gross exposure and net weights per symbol."""
    symbol_exposures: dict[str, Decimal] = {}
    for pos in portfolio_state.positions:
        symbol_exposures[pos.symbol] = symbol_exposures.get(
            pos.symbol, Decimal("0.0")
        ) + get_position_signed_exposure(
            pos.symbol, pos.quantity, pos.direction, market_context, account_ccy
        )

    if proposed_trade is not None:
        symbol_exposures[proposed_trade.symbol] = symbol_exposures.get(
            proposed_trade.symbol, Decimal("0.0")
        ) + get_proposed_trade_signed_exposure(
            proposed_trade, market_context, account_ccy
        )

    total_gross_exposure = sum(
        (abs(v) for v in symbol_exposures.values()), Decimal("0.0")
    )

    weights: dict[str, Decimal] = {}
    if total_gross_exposure > 0:
        for s, exp in symbol_exposures.items():
            weights[s] = exp / total_gross_exposure
    else:
        for s in symbol_exposures:
            weights[s] = Decimal("0.0")

    return total_gross_exposure, weights


def _resolve_var_es_values(
    var_method: str,
    es_method: str,
    weights: dict[str, Decimal],
    shrunk_matrix: dict[str, dict[str, Decimal]],
    sliced_returns: dict[str, list[Decimal]],
    var_confidence: Decimal,
    es_confidence: Decimal,
    total_gross_exposure: Decimal,
    portfolio_vol: Decimal,
) -> tuple[Decimal, Decimal, Decimal]:
    """Resolve metric outcomes for VaR and ES using chosen methods."""
    # 1. Resolve VaR
    if var_method == VaRMethod.PARAMETRIC:
        vol, var_val, _ = calculate_parametric_var_es(
            weights, shrunk_matrix, var_confidence, total_gross_exposure
        )
    elif var_method == VaRMethod.HISTORICAL:
        var_val, _ = calculate_historical_var_es(
            sliced_returns, weights, var_confidence, total_gross_exposure
        )
        vol = portfolio_vol
    else:
        msg = f"Unsupported VaR method: {var_method}"
        raise ValidationError(msg)

    # 2. Resolve ES
    if es_method == ExpectedShortfallMethod.PARAMETRIC:
        _, _, es_val = calculate_parametric_var_es(
            weights, shrunk_matrix, es_confidence, total_gross_exposure
        )
    elif es_method == ExpectedShortfallMethod.HISTORICAL:
        _, es_val = calculate_historical_var_es(
            sliced_returns, weights, es_confidence, total_gross_exposure
        )
    else:
        msg = f"Unsupported Expected Shortfall method: {es_method}"
        raise ValidationError(msg)

    return vol, var_val, es_val


def calculate_var_es_snapshots(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    config: RiskConfig,
    lookback: int = 50,
    var_confidence: Decimal = Decimal("0.95"),
    es_confidence: Decimal = Decimal("0.95"),
    var_method: str = VaRMethod.PARAMETRIC,
    es_method: str = ExpectedShortfallMethod.PARAMETRIC,
    cov_method: str = "parametric",
    ewma_decay: Decimal = Decimal("0.94"),
    shrinkage_intensity: Decimal = Decimal("0.1"),
    min_samples: int = 20,
    exclude_last: bool = True,
) -> tuple[VaRSnapshot, ExpectedShortfallSnapshot]:
    """Execute pre-trade Value-at-Risk and Expected Shortfall checks.

    Args:
        portfolio_state: Portfolio state snapshot.
        proposed_trade: Proposed trade candidate.
        market_context: Market context data (prices, returns history).
        config: Active risk configuration.
        lookback: Returns lookback length.
        var_confidence: Confidence level for VaR.
        es_confidence: Confidence level for ES.
        var_method: Method to evaluate VaR ('parametric', 'historical').
        es_method: Method to evaluate ES ('parametric', 'historical').
        cov_method: Method for covariance matrix estimation ('parametric',
          'ewma').
        ewma_decay: EWMA decay factor.
        shrinkage_intensity: Shrinkage intensity.
        min_samples: Minimum required returns samples.
        exclude_last: Exclude the last bar.

    Returns:
        Tuple of (VaRSnapshot, ExpectedShortfallSnapshot).

    Raises:
        ValidationError: If return history is insufficient or results are non-finite.
    """
    _ = config
    account_ccy = portfolio_state.currency.upper()

    # Collect unique symbols
    symbols = {pos.symbol for pos in portfolio_state.positions}
    if proposed_trade is not None:
        symbols.add(proposed_trade.symbol)

    if not symbols:
        return (
            VaRSnapshot(
                method=var_method,
                confidence=var_confidence,
                portfolio_volatility=Decimal("0.0"),
                exposure=Decimal("0.0"),
                result=Decimal("0.0"),
                assumptions={},
            ),
            ExpectedShortfallSnapshot(
                confidence=es_confidence,
                threshold_loss=Decimal("0.0"),
                average_tail_loss=Decimal("0.0"),
                sample_count=0,
                method=es_method,
            ),
        )

    # 1. Fetch return series from market data context
    market_data = market_context.get("market_data", market_context)
    from app.services.risk.correlation import calculate_returns

    returns_db: dict[str, dict[datetime, Decimal]] = {}
    for s in symbols:
        bars = market_data.get(s, [])
        returns_db[s] = calculate_returns(
            bars, return_type="close_to_close", exclude_last=exclude_last
        )

    # 2. Align return series
    aligned_returns = align_multiple_return_series(returns_db)
    if not aligned_returns:
        msg = "Fail-Closed: Return series alignment returned empty dataset."
        raise ValidationError(msg)

    # Check sample size limit
    first_sym = next(iter(aligned_returns))
    sample_count = len(aligned_returns[first_sym])
    if sample_count < min_samples:
        msg = (
            f"Fail-Closed: Insufficient aligned samples "
            f"({sample_count} < {min_samples}) for VaR/ES calculations."
        )
        raise ValidationError(msg)

    # Slice to lookback limit
    sliced_returns: dict[str, list[Decimal]] = {}
    for s, rets in aligned_returns.items():
        sliced_returns[s] = rets[-lookback:]

    # 3. Calculate portfolio weights based on net signed exposures
    total_gross_exposure, weights = _compute_exposures_and_weights(
        portfolio_state, proposed_trade, market_context, account_ccy
    )

    # 4. Generate Covariance Matrix
    raw_matrix = calculate_covariance_matrix(
        sliced_returns, method=cov_method, ewma_decay=ewma_decay
    )
    shrunk_matrix = shrink_covariance_matrix(
        raw_matrix, shrinkage_intensity=shrinkage_intensity
    )
    validate_covariance_matrix(shrunk_matrix)

    # 5. Compute parametric portfolio volatility
    portfolio_vol = calculate_portfolio_volatility(weights, shrunk_matrix)

    # 6. Resolve VaR and ES Values
    vol, var_val, es_val = _resolve_var_es_values(
        var_method,
        es_method,
        weights,
        shrunk_matrix,
        sliced_returns,
        var_confidence,
        es_confidence,
        total_gross_exposure,
        portfolio_vol,
    )

    # Euler risk contributions
    mrc, crc = calculate_risk_contributions(
        weights,
        shrunk_matrix,
        portfolio_vol,
        var_confidence,
        total_gross_exposure,
    )

    # Check finite values
    for val in (vol, var_val, es_val):
        if not math.isfinite(float(val)):
            msg = f"Non-finite calculations detected in VaR/ES snapshots: {val}"
            raise ValidationError(msg)

    assumptions = {
        "covariance_method": cov_method,
        "ewma_decay": float(ewma_decay),
        "shrinkage_intensity": float(shrinkage_intensity),
        "marginal_contributions": {k: float(v) for k, v in mrc.items()},
        "component_contributions": {k: float(v) for k, v in crc.items()},
    }

    var_snap = VaRSnapshot(
        method=var_method,
        confidence=var_confidence,
        portfolio_volatility=vol,
        exposure=total_gross_exposure,
        result=var_val,
        assumptions=assumptions,
    )

    es_snap = ExpectedShortfallSnapshot(
        confidence=es_confidence,
        threshold_loss=var_val,
        average_tail_loss=es_val,
        sample_count=sample_count,
        method=es_method,
    )

    return var_snap, es_snap


def calculate_portfolio_var(
    portfolio_state: PortfolioState,
    market_context: dict[str, Any],
    config: RiskConfig,
    proposed_trade: ProposedTrade | None = None,
    lookback: int = 50,
    confidence: Decimal = Decimal("0.95"),
    method: str = VaRMethod.PARAMETRIC,
) -> Decimal:
    """Calculate portfolio Value-at-Risk.

    Args:
        portfolio_state: Current portfolio state.
        market_context: Market context containing returns/prices history.
        config: Active risk configuration profile.
        proposed_trade: Optional candidate proposed trade.
        lookback: Returns lookback length.
        confidence: Confidence level.
        method: VaR calculation method.

    Returns:
        Decimal: Value-at-Risk amount.
    """
    var_snap, _ = calculate_var_es_snapshots(
        portfolio_state=portfolio_state,
        proposed_trade=proposed_trade,
        market_context=market_context,
        config=config,
        lookback=lookback,
        var_confidence=confidence,
        var_method=method,
    )
    return var_snap.result


def calculate_expected_shortfall(
    portfolio_state: PortfolioState,
    market_context: dict[str, Any],
    config: RiskConfig,
    proposed_trade: ProposedTrade | None = None,
    lookback: int = 50,
    confidence: Decimal = Decimal("0.95"),
    method: str = ExpectedShortfallMethod.PARAMETRIC,
) -> Decimal:
    """Calculate portfolio Expected Shortfall.

    Args:
        portfolio_state: Current portfolio state.
        market_context: Market context containing returns/prices history.
        config: Active risk configuration profile.
        proposed_trade: Optional candidate proposed trade.
        lookback: Returns lookback length.
        confidence: Confidence level.
        method: ES calculation method.

    Returns:
        Decimal: Expected Shortfall amount.
    """
    _, es_snap = calculate_var_es_snapshots(
        portfolio_state=portfolio_state,
        proposed_trade=proposed_trade,
        market_context=market_context,
        config=config,
        lookback=lookback,
        es_confidence=confidence,
        es_method=method,
    )
    return es_snap.average_tail_loss
