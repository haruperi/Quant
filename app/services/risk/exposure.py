"""FX Currency Exposure Engine.

Decomposes assets and portfolios into base/quote currency legs, calculates
gross/net exposures, and evaluates projected exposures under pending-order policies.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.services.risk.models import (
    CurrencyExposure,
    CurrencyLegExposure,
    PortfolioState,
    ProposedTrade,
    RiskConfig,
    RiskMode,
)
from app.utils.errors import ValidationError
from app.utils.logger import logger

FX_SYMBOL_LENGTH = 6


def _resolve_base_quote(symbol: str, market_context: dict[str, Any]) -> tuple[str, str]:
    """Resolve base and quote currencies for a symbol, with fallback."""
    spec = market_context.get(symbol, {})
    if isinstance(spec, dict):
        base = spec.get("base") or spec.get("base_currency")
        quote = spec.get("quote") or spec.get("quote_currency")
        if base and quote:
            return str(base).upper(), str(quote).upper()

    base = market_context.get(f"{symbol}_base")
    quote = market_context.get(f"{symbol}_quote")
    if base and quote:
        return str(base).upper(), str(quote).upper()

    sym = symbol.upper()
    if len(sym) == FX_SYMBOL_LENGTH:
        return sym[:3], sym[3:]
    for suffix in ("USD", "EUR", "JPY", "GBP", "AUD", "CAD", "CHF"):
        if sym.endswith(suffix) and len(sym) > len(suffix):
            return sym[: -len(suffix)], suffix
    return sym, "USD"


def _lookup_rates_dict(
    c_upper: str, a_upper: str, rates: dict[str, Any]
) -> Decimal | None:
    """Helper to look up rates from rates dict."""
    if c_upper in rates:
        return Decimal(str(rates[c_upper]))
    pair = f"{c_upper}{a_upper}"
    if pair in rates:
        return Decimal(str(rates[pair]))
    rev_pair = f"{a_upper}{c_upper}"
    if rev_pair in rates:
        val = Decimal(str(rates[rev_pair]))
        if val > 0:
            return Decimal("1.0") / val
    return None


def _lookup_context_keys(
    c_upper: str, a_upper: str, market_context: dict[str, Any]
) -> Decimal | None:
    """Helper to look up rates from direct context keys."""
    keys_direct = (
        f"{c_upper}{a_upper}",
        f"{c_upper}_{a_upper}",
        f"{c_upper}/{a_upper}",
    )
    for key in keys_direct:
        if key in market_context:
            return Decimal(str(market_context[key]))

    keys_rev = (
        f"{a_upper}{c_upper}",
        f"{a_upper}_{c_upper}",
        f"{a_upper}/{c_upper}",
    )
    for key in keys_rev:
        if key in market_context:
            val = Decimal(str(market_context[key]))
            if val > 0:
                return Decimal("1.0") / val
    return None


def _resolve_conversion_rate(
    ccy: str, account_ccy: str, market_context: dict[str, Any]
) -> Decimal:
    """Resolve conversion rate from ccy to account_ccy with fallback checks."""
    c_upper = ccy.upper()
    a_upper = account_ccy.upper()
    if c_upper == a_upper:
        return Decimal("1.0")

    rates = market_context.get("conversion_rates", {})
    if isinstance(rates, dict):
        res = _lookup_rates_dict(c_upper, a_upper, rates)
        if res is not None:
            return res

    res_context = _lookup_context_keys(c_upper, a_upper, market_context)
    if res_context is not None:
        return res_context

    fallback_rates = {
        ("EUR", "USD"): Decimal("1.10"),
        ("GBP", "USD"): Decimal("1.25"),
        ("USD", "JPY"): Decimal("150.0"),
        ("JPY", "USD"): Decimal("0.0067"),
        ("AUD", "USD"): Decimal("0.65"),
        ("CAD", "USD"): Decimal("0.75"),
        ("CHF", "USD"): Decimal("1.12"),
    }
    if (c_upper, a_upper) in fallback_rates:
        return fallback_rates[(c_upper, a_upper)]
    if (a_upper, c_upper) in fallback_rates:
        return Decimal("1.0") / fallback_rates[(a_upper, c_upper)]

    msg = f"Missing conversion rate for {c_upper} to {a_upper}."
    raise ValidationError(msg)


def decompose_position(
    symbol: str,  # noqa: ARG001
    side: str,
    quantity: Decimal,
    price: Decimal,
    contract_size: Decimal,
    base_ccy: str,
    quote_ccy: str,
) -> list[CurrencyLegExposure]:
    """Decompose a position/order on a symbol into its base and quote currency legs."""
    side_norm = side.lower()
    if side_norm in {"buy", "long"}:
        base_amt = quantity * contract_size
        quote_amt = -quantity * contract_size * price
    elif side_norm in {"sell", "short"}:
        base_amt = -quantity * contract_size
        quote_amt = quantity * contract_size * price
    else:
        msg = f"Invalid position/order side: {side}"
        raise ValueError(msg)

    return [
        CurrencyLegExposure(currency=base_ccy, signed_amount=base_amt),
        CurrencyLegExposure(currency=quote_ccy, signed_amount=quote_amt),
    ]


def _check_live_status(market_context: dict[str, Any], config: RiskConfig) -> None:
    """Validate live status checks fail-closed."""
    mode = market_context.get("mode")
    is_live = (
        mode in {RiskMode.FULL_LIVE, RiskMode.MICRO_LIVE, RiskMode.LIVE_READONLY}
        or config.allow_live_execution
    )
    if is_live:
        is_reconciled = market_context.get("is_reconciled", True)
        portfolio_reconciled = market_context.get("portfolio_reconciled", True)
        broker_connected = market_context.get("broker_connected", True)
        if not (is_reconciled and portfolio_reconciled and broker_connected):
            msg = (
                "Fail-Closed: Portfolio state is unreconciled or broker is "
                "disconnected."
            )
            logger.error(msg)
            raise ValidationError(msg)


def _add_leg_exposure(
    ccy: str,
    signed_val: Decimal,
    weight: Decimal,
    exposures: dict[str, dict[str, Decimal]],
    account_ccy: str,
    market_context: dict[str, Any],
) -> None:
    """Helper to convert and add leg exposure."""
    c_upper = ccy.upper()
    if c_upper not in exposures:
        exposures[c_upper] = {"gross": Decimal("0.0"), "net": Decimal("0.0")}

    rate = _resolve_conversion_rate(c_upper, account_ccy, market_context)
    equiv = signed_val * rate * weight

    exposures[c_upper]["net"] += equiv
    exposures[c_upper]["gross"] += abs(equiv)


def _process_positions(
    portfolio_state: PortfolioState,
    market_context: dict[str, Any],
    strategy_id: str | None,
    symbol: str | None,
    exposures: dict[str, dict[str, Decimal]],
    account_ccy: str,
) -> None:
    """Add exposure from open positions."""
    for pos in portfolio_state.positions:
        if strategy_id is not None and pos.strategy_id != strategy_id:
            continue
        if symbol is not None and pos.symbol != symbol:
            continue

        pos_symbol = pos.symbol
        c_size_raw = market_context.get(f"{pos_symbol}_contract_size", "100000.0")
        contract_size = Decimal(str(c_size_raw))
        base_ccy, quote_ccy = _resolve_base_quote(pos_symbol, market_context)

        legs = decompose_position(
            symbol=pos_symbol,
            side=pos.direction,
            quantity=pos.quantity,
            price=pos.current_price,
            contract_size=contract_size,
            base_ccy=base_ccy,
            quote_ccy=quote_ccy,
        )
        for leg in legs:
            _add_leg_exposure(
                leg.currency,
                leg.signed_amount,
                Decimal("1.0"),
                exposures,
                account_ccy,
                market_context,
            )


def _parse_order_fields(
    order: dict[str, object] | object,
) -> tuple[
    str | None,
    str | None,
    Decimal | None,
    Decimal | None,
    str,
    Decimal | None,
    Decimal | None,
]:
    """Parse fields from a dict or object order."""
    if isinstance(order, dict):
        o_symbol = order.get("symbol")
        o_side = order.get("side") or order.get("direction")
        o_vol = order.get("volume") or order.get("quantity")
        o_price = order.get("price") or order.get("trigger_price")
        o_status = order.get("status", "active")
        o_prob = order.get("probability")
        o_dist = order.get("distance_pips")
    else:
        o_symbol = getattr(order, "symbol", None)
        o_side = getattr(order, "side", None) or getattr(order, "direction", None)
        o_vol = getattr(order, "volume", None) or getattr(order, "quantity", None)
        o_price = getattr(order, "price", None) or getattr(order, "trigger_price", None)
        o_status = getattr(order, "status", "active")
        o_prob = getattr(order, "probability", None)
        o_dist = getattr(order, "distance_pips", None)

    o_vol_dec = Decimal(str(o_vol)) if o_vol is not None else None
    o_price_dec = Decimal(str(o_price)) if o_price is not None else None
    o_prob_dec = Decimal(str(o_prob)) if o_prob is not None else None
    o_dist_dec = Decimal(str(o_dist)) if o_dist is not None else None

    o_symbol_str = str(o_symbol) if o_symbol is not None else None
    o_side_str = str(o_side) if o_side is not None else None
    o_status_str = str(o_status) if o_status is not None else "active"

    return (
        o_symbol_str,
        o_side_str,
        o_vol_dec,
        o_price_dec,
        o_status_str,
        o_prob_dec,
        o_dist_dec,
    )


def _resolve_order_distance(
    o_symbol: str,
    o_price_dec: Decimal,
    o_dist_dec: Decimal | None,
    market_context: dict[str, Any],
) -> Decimal | None:
    """Resolve distance_pips if not explicitly provided."""
    if o_dist_dec is not None:
        return o_dist_dec

    curr_price = market_context.get(f"{o_symbol}_price") or market_context.get(
        "current_price"
    )
    if curr_price is not None:
        curr_dec = Decimal(str(curr_price))
        digits = int(market_context.get(f"{o_symbol}_digits", 5))
        pip_size = Decimal("0.01") if digits in {2, 3} else Decimal("0.0001")
        return abs(curr_dec - o_price_dec) / pip_size
    return None


def _should_filter_order(
    order: dict[str, object] | object,
    o_symbol: str | None,
    strategy_id: str | None,
    symbol: str | None,
) -> bool:
    """Filter by strategy or symbol. Returns True if order should be filtered out."""
    if strategy_id is not None:
        if isinstance(order, dict):
            o_strat = order.get("strategy_id")
        else:
            o_strat = getattr(order, "strategy_id", None)
        if o_strat != strategy_id:
            return True
    return symbol is not None and o_symbol != symbol


def _calculate_policy_weight(
    policy: str,
    o_symbol: str,
    o_price_dec: Decimal,
    o_dist: Decimal | None,
    o_prob: Decimal | None,
    market_context: dict[str, Any],
) -> Decimal | None:
    """Calculate the weight of a pending order under a policy.

    Returns None if skipped.
    """
    if policy == "near-market-only":
        resolved_dist = _resolve_order_distance(
            o_symbol, o_price_dec, o_dist, market_context
        )
        thresh_val = market_context.get("near_market_threshold_pips", "50.0")
        threshold = Decimal(str(thresh_val))
        if resolved_dist is not None and resolved_dist > threshold:
            return None

    elif policy == "probability-weighted":
        return o_prob if o_prob is not None else Decimal("0.5")

    return Decimal("1.0")


def _process_single_order(
    order: dict[str, object] | object,
    policy: str,
    is_live: bool,
    strategy_id: str | None,
    symbol: str | None,
    market_context: dict[str, Any],
    account_ccy: str,
    exposures: dict[str, dict[str, Decimal]],
) -> None:
    """Process a single order and aggregate its exposure legs."""
    o_symbol, o_side, o_vol, o_price, o_status, o_prob, o_dist = _parse_order_fields(
        order
    )

    if not o_symbol or not o_side or o_vol is None:
        if is_live:
            msg = "Missing required order fields in live mode."
            raise ValidationError(msg)
        return

    if _should_filter_order(order, o_symbol, strategy_id, symbol):
        return

    is_unknown = not o_status or str(o_status).lower() in {
        "unknown",
        "unresolved",
    }
    if is_live and is_unknown:
        msg = f"Fail-Closed: Unknown order status '{o_status}' encountered."
        logger.error(msg)
        raise ValidationError(msg)

    o_price_dec = o_price if o_price is not None else Decimal("1.0")

    weight = _calculate_policy_weight(
        policy, o_symbol, o_price_dec, o_dist, o_prob, market_context
    )
    if weight is None:
        return

    c_size_raw = market_context.get(f"{o_symbol}_contract_size", "100000.0")
    contract_size = Decimal(str(c_size_raw))
    base_ccy, quote_ccy = _resolve_base_quote(o_symbol, market_context)

    legs = decompose_position(
        symbol=o_symbol,
        side=o_side,
        quantity=o_vol,
        price=o_price_dec,
        contract_size=contract_size,
        base_ccy=base_ccy,
        quote_ccy=quote_ccy,
    )
    for leg in legs:
        _add_leg_exposure(
            leg.currency,
            leg.signed_amount,
            weight,
            exposures,
            account_ccy,
            market_context,
        )


def _process_orders(
    portfolio_state: PortfolioState,
    market_context: dict[str, Any],
    config: RiskConfig,
    strategy_id: str | None,
    symbol: str | None,
    exposures: dict[str, dict[str, Decimal]],
    account_ccy: str,
) -> None:
    """Aggregate exposures from pending and in-flight orders under policy."""
    policy = (config.pending_order_policy or "ignore").lower()
    if policy == "ignore":
        return

    mode = market_context.get("mode")
    is_live = (
        mode in {RiskMode.FULL_LIVE, RiskMode.MICRO_LIVE, RiskMode.LIVE_READONLY}
        or config.allow_live_execution
    )

    all_orders: list[dict[str, object] | object] = []
    if hasattr(portfolio_state, "orders") and portfolio_state.orders:
        all_orders.extend(portfolio_state.orders)

    in_flight = market_context.get("in_flight_orders", [])
    all_orders.extend(in_flight)

    for order in all_orders:
        _process_single_order(
            order=order,
            policy=policy,
            is_live=is_live,
            strategy_id=strategy_id,
            symbol=symbol,
            market_context=market_context,
            account_ccy=account_ccy,
            exposures=exposures,
        )


def _process_proposed_trade(
    proposed_trade: ProposedTrade | None,
    market_context: dict[str, Any],
    strategy_id: str | None,
    symbol: str | None,
    exposures: dict[str, dict[str, Decimal]],
    account_ccy: str,
) -> None:
    """Aggregate proposed trade exposure."""
    if (
        proposed_trade is not None
        and (strategy_id is None or proposed_trade.strategy_id == strategy_id)
        and (symbol is None or proposed_trade.symbol == symbol)
    ):
        p_symbol = proposed_trade.symbol
        p_contract_raw = market_context.get(f"{p_symbol}_contract_size", "100000.0")
        p_contract = Decimal(str(p_contract_raw))
        if proposed_trade.price > 0:
            p_price = Decimal(str(proposed_trade.price))
        else:
            p_price = Decimal(str(market_context.get(f"{p_symbol}_price", "1.0")))
        p_base, p_quote = _resolve_base_quote(p_symbol, market_context)

        p_legs = decompose_position(
            symbol=p_symbol,
            side=proposed_trade.side,
            quantity=proposed_trade.volume,
            price=p_price,
            contract_size=p_contract,
            base_ccy=p_base,
            quote_ccy=p_quote,
        )
        for leg in p_legs:
            _add_leg_exposure(
                leg.currency,
                leg.signed_amount,
                Decimal("1.0"),
                exposures,
                account_ccy,
                market_context,
            )


def _aggregate_clusters(
    config: RiskConfig,
    market_context: dict[str, Any],
    exposures: dict[str, dict[str, Decimal]],
    result: dict[str, CurrencyExposure],
) -> None:
    """Aggregate custom currency clusters exposure."""
    clusters = config.currency_clusters or market_context.get("currency_clusters", {})
    if not clusters:
        return

    for cluster_name, constituent_ccys in clusters.items():
        cluster_gross = Decimal("0.0")
        cluster_net = Decimal("0.0")
        for c in constituent_ccys:
            c_upper = c.upper()
            if c_upper in exposures:
                cluster_gross += exposures[c_upper]["gross"]
                cluster_net += exposures[c_upper]["net"]

        result[cluster_name] = CurrencyExposure(
            gross=cluster_gross,
            net=cluster_net,
            account_currency_equivalent=cluster_net,
        )


def calculate_currency_exposure(
    portfolio_state: PortfolioState,
    proposed_trade: ProposedTrade | None,
    config: RiskConfig,
    market_context: dict[str, Any],
    strategy_id: str | None = None,
    symbol: str | None = None,
) -> dict[str, CurrencyExposure]:
    """Decompose and aggregate gross/net exposures per currency.

    Can be filtered to aggregate by a specific strategy_id or symbol.
    """
    _check_live_status(market_context, config)

    account_ccy = portfolio_state.currency.upper()
    exposures: dict[str, dict[str, Decimal]] = {}

    _process_positions(
        portfolio_state,
        market_context,
        strategy_id,
        symbol,
        exposures,
        account_ccy,
    )

    _process_orders(
        portfolio_state,
        market_context,
        config,
        strategy_id,
        symbol,
        exposures,
        account_ccy,
    )

    _process_proposed_trade(
        proposed_trade,
        market_context,
        strategy_id,
        symbol,
        exposures,
        account_ccy,
    )

    # Populate final output
    result: dict[str, CurrencyExposure] = {}
    for ccy, vals in exposures.items():
        result[ccy] = CurrencyExposure(
            gross=vals["gross"],
            net=vals["net"],
            account_currency_equivalent=vals["net"],
        )

    _aggregate_clusters(config, market_context, exposures, result)

    return result
