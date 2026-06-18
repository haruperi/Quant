# ruff: noqa: PLR2004
"""Market regime detection and validation engine.

Responsible for spread z-score thresholds, rolling volatility
classification, stale quote checks, session status, rollover
blackout windows, and calendar news matching.
"""

from __future__ import annotations

import math
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from app.services.risk.models import (
    MarketRiskSnapshot,
    RiskConfig,
    RiskContract,
    RiskDecisionStatus,
    RiskReasonCode,
)
from app.utils.logger import logger
from app.utils.normalization import parse_datetime, to_utc_datetime, utc_now


class RiskRegime(StrEnum):
    """Overall synthesized market regime classification."""

    NORMAL = "normal"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    WIDE_SPREAD = "wide_spread"
    ILLIQUID = "illiquid"
    NEWS_BLACKOUT = "news_blackout"
    ROLLOVER_BLACKOUT = "rollover_blackout"
    MARKET_CLOSED = "market_closed"
    STALE_DATA = "stale_data"
    SUSPENDED = "suspended"
    INVALID_QUOTE = "invalid_quote"
    UNKNOWN = "unknown"


class SpreadRegime(StrEnum):
    """Spread widening classification."""

    NORMAL = "normal"
    WIDE = "wide"
    EXTREME = "extreme"


class VolatilityRegime(StrEnum):
    """Volatility classification."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    SPIKE = "spike"


class LiquidityRegime(StrEnum):
    """Liquidity classification based on quotes/ticks."""

    NORMAL = "normal"
    THIN = "thin"
    ILLIQUID = "illiquid"


class NewsRegime(StrEnum):
    """News impact/blackout classification."""

    NORMAL = "normal"
    HIGH_IMPACT = "high_impact"
    BLACKOUT = "blackout"


class SessionRegime(StrEnum):
    """Market session status classification."""

    CLOSED = "closed"
    ACTIVE = "active"


class RolloverRegime(StrEnum):
    """Broker rollover blackout status classification."""

    NORMAL = "normal"
    BLACKOUT = "blackout"


class RegimeResult(RiskContract):
    """Contract representing the outcome of a market regime assessment."""

    regime: RiskRegime
    spread_regime: SpreadRegime
    volatility_regime: VolatilityRegime
    liquidity_regime: LiquidityRegime
    news_regime: NewsRegime
    session_regime: SessionRegime
    rollover_regime: RolloverRegime
    status: RiskDecisionStatus
    reason: str
    reason_code: RiskReasonCode
    timestamp: datetime


def _compute_stats(values: list[Decimal]) -> tuple[Decimal, Decimal]:
    """Compute mean and standard deviation of Decimal values."""
    if not values:
        return Decimal(0), Decimal(0)
    n = len(values)
    float_vals = [float(v) for v in values]
    mean_val = sum(float_vals) / n
    variance = sum((x - mean_val) ** 2 for x in float_vals) / n
    std_val = math.sqrt(variance)
    return Decimal(str(mean_val)), Decimal(str(std_val))


def _calculate_rolling_vol(prices: list[Decimal], lookback: int) -> Decimal:
    """Calculate volatility (std of log returns) over lookback window."""
    if len(prices) <= lookback:
        return Decimal(0)
    # Take the last lookback + 1 prices to get lookback returns
    subset = prices[-(lookback + 1) :]
    returns = []
    for i in range(1, len(subset)):
        p1 = float(subset[i - 1])
        p2 = float(subset[i])
        if p1 <= 0 or p2 <= 0:
            returns.append(Decimal(0))
        else:
            returns.append(Decimal(str(math.log(p2 / p1))))
    _, std = _compute_stats(returns)
    return std


class RegimeRiskEngine:
    """Deterministic engine evaluating all market regime conditions.

    Evaluates spread widening, volatility regimes, liquidity freshness,
    session indicators, news schedules, and midnight blackouts.
    """

    def __init__(self, config: RiskConfig) -> None:
        """Initialize engine with active risk config."""
        self.config = config

    def assess(
        self,
        market_snapshot: MarketRiskSnapshot,
        calendar_evidence: list[dict[str, Any]],
        market_context: dict[str, Any],
    ) -> RegimeResult:
        """Assess all market regime components and determine decision status.

        Args:
            market_snapshot: Current market snapshot including spread,
                volatility, freshness.
            calendar_evidence: List of upcoming news/calendar event dictionaries.
            market_context: Context inputs containing spread/price history or
                custom indicators.

        Returns:
            RegimeResult: The resolved market regimes and risk status block.
        """
        now = utc_now()

        # 1. Input sanitization and quote validations
        if market_snapshot.spread < 0:
            return self._build_error_result(
                RiskRegime.INVALID_QUOTE,
                RiskReasonCode.INVALID_INPUT,
                "Inverted or negative spread detected",
                now,
            )

        # 2. Reject stale quotes and stale market data snapshots
        freshness = to_utc_datetime(market_snapshot.freshness)
        age_seconds = (now - freshness).total_seconds()
        # Default max quote age is 60 seconds
        max_age = float(market_context.get("max_stale_seconds", 60.0))
        if age_seconds > max_age:
            return self._build_error_result(
                RiskRegime.STALE_DATA,
                RiskReasonCode.STALE_EVIDENCE,
                f"Market data is stale. Age: {age_seconds:.1f}s (max: {max_age:.1f}s)",
                now,
            )

        # 3. Classify session regime
        session_state = market_snapshot.session.lower()
        if session_state in {"closed", "suspended"} or market_context.get(
            "is_suspended", False
        ):
            reg = (
                RiskRegime.MARKET_CLOSED
                if session_state == "closed"
                else RiskRegime.SUSPENDED
            )
            return self._build_error_result(
                reg,
                RiskReasonCode.LIFECYCLE_GATES_BREACH,
                f"Trading disabled: market session is '{session_state}' "
                "or symbol is suspended",
                now,
            )
        session_regime = SessionRegime.ACTIVE

        # 4. Classify spread regime (spread-to-sigma thresholds)
        spread_regime = self._classify_spread(market_snapshot.spread, market_context)

        # 5. Classify volatility regime using rolling windows
        volatility_regime = self._classify_volatility(
            market_snapshot.volatility, market_context
        )

        # 6. Classify liquidity regime
        liquidity_regime = self._classify_liquidity(market_context)

        # 7. Classify news regime
        news_regime = self._classify_news(calendar_evidence, market_context, now)

        # 8. Classify rollover regime
        rollover_regime = self._classify_rollover(
            market_snapshot.rollover_time, now, market_context
        )

        # Fail-closed calendar evidence check for live-sensitive profiles
        is_live = getattr(self.config, "allow_live_execution", False)
        require_calendar = market_context.get("require_news_calendar", True)
        if is_live and require_calendar and not calendar_evidence:
            return self._build_error_result(
                RiskRegime.STALE_DATA,
                RiskReasonCode.STALE_EVIDENCE,
                "Live profile execution blocked: news calendar evidence is missing",
                now,
                status=RiskDecisionStatus.BLOCK,
            )

        return self._synthesize_regime(
            spread_regime,
            volatility_regime,
            liquidity_regime,
            news_regime,
            rollover_regime,
            session_regime,
            now,
        )

    def _synthesize_regime(
        self,
        spread_regime: SpreadRegime,
        volatility_regime: VolatilityRegime,
        liquidity_regime: LiquidityRegime,
        news_regime: NewsRegime,
        rollover_regime: RolloverRegime,
        session_regime: SessionRegime,
        now: datetime,
    ) -> RegimeResult:
        """Synthesize final regime classification and status logic."""
        status = RiskDecisionStatus.APPROVE
        regime = RiskRegime.NORMAL
        reason = "Market regimes are within safe operating limits"
        reason_code = RiskReasonCode.OK

        if rollover_regime == RolloverRegime.BLACKOUT:
            status = RiskDecisionStatus.REJECT
            regime = RiskRegime.ROLLOVER_BLACKOUT
            reason = "Rollover blackout window is active"
            reason_code = RiskReasonCode.ROLLOVER_BLACKOUT
        elif news_regime == NewsRegime.BLACKOUT:
            status = RiskDecisionStatus.REJECT
            regime = RiskRegime.NEWS_BLACKOUT
            reason = "High impact news blackout window is active"
            reason_code = RiskReasonCode.NEWS_BLACKOUT
        elif volatility_regime == VolatilityRegime.SPIKE:
            status = RiskDecisionStatus.REJECT
            regime = RiskRegime.HIGH_VOLATILITY
            reason = "Abnormal volatility spike detected"
            reason_code = RiskReasonCode.DAILY_LOSS_BREACH
        elif spread_regime == SpreadRegime.EXTREME:
            status = RiskDecisionStatus.REJECT
            regime = RiskRegime.WIDE_SPREAD
            reason = "Extreme spread widening detected"
            reason_code = RiskReasonCode.SPREAD_BREACH
        elif liquidity_regime == LiquidityRegime.ILLIQUID:
            status = RiskDecisionStatus.REJECT
            regime = RiskRegime.ILLIQUID
            reason = "Illiquid market environment detected"
            reason_code = RiskReasonCode.STALE_EVIDENCE
        elif volatility_regime == VolatilityRegime.HIGH:
            regime = RiskRegime.HIGH_VOLATILITY
            reason = "High volatility regime active"
        elif volatility_regime == VolatilityRegime.LOW:
            regime = RiskRegime.LOW_VOLATILITY
            reason = "Low volatility regime active"
        elif spread_regime == SpreadRegime.WIDE:
            regime = RiskRegime.WIDE_SPREAD
            reason = "Wide spread regime active"

        return RegimeResult(
            regime=regime,
            spread_regime=spread_regime,
            volatility_regime=volatility_regime,
            liquidity_regime=liquidity_regime,
            news_regime=news_regime,
            session_regime=session_regime,
            rollover_regime=rollover_regime,
            status=status,
            reason=reason,
            reason_code=reason_code,
            timestamp=now,
        )

    def _classify_spread(
        self, current_spread: Decimal, context: dict[str, Any]
    ) -> SpreadRegime:
        """Classify spread regime based on historical standard deviation."""
        hist_spreads = context.get("historical_spreads")
        mean_spread = Decimal(0)
        std_spread = Decimal(0)

        if hist_spreads and len(hist_spreads) >= 2:
            mean_spread, std_spread = _compute_stats(
                [Decimal(str(x)) for x in hist_spreads]
            )
        else:
            mean_spread_val = context.get("spread_mean")
            std_spread_val = context.get("spread_std")
            if mean_spread_val is not None and std_spread_val is not None:
                mean_spread = Decimal(str(mean_spread_val))
                std_spread = Decimal(str(std_spread_val))

        if std_spread <= 0:
            return SpreadRegime.NORMAL

        z_score = abs(current_spread - mean_spread) / std_spread
        z_normal = Decimal(str(context.get("spread_z_score_threshold_normal", 1.5)))
        z_wide = Decimal(str(context.get("spread_z_score_threshold_wide", 3.0)))

        if z_score <= z_normal:
            return SpreadRegime.NORMAL
        if z_score <= z_wide:
            return SpreadRegime.WIDE
        return SpreadRegime.EXTREME

    def _fallback_volatility(self, current_vol: Decimal) -> VolatilityRegime:
        """Fallback classification when no history is present."""
        if current_vol > Decimal("0.05"):
            return VolatilityRegime.HIGH
        if current_vol < Decimal("0.005"):
            return VolatilityRegime.LOW
        return VolatilityRegime.NORMAL

    def _classify_volatility(
        self, current_vol: Decimal, context: dict[str, Any]
    ) -> VolatilityRegime:
        """Classify volatility regime using rolling window relationships."""
        prices = context.get("historical_prices")
        vol_short = Decimal(0)
        vol_long = Decimal(0)
        has_history = False

        if prices and len(prices) > 60:
            vol_short = _calculate_rolling_vol(prices, 5)
            vol_long = _calculate_rolling_vol(prices, 60)
            has_history = True
        else:
            v_short = context.get("vol_short")
            v_long = context.get("vol_long")
            if v_short is not None and v_long is not None:
                vol_short = Decimal(str(v_short))
                vol_long = Decimal(str(v_long))
                has_history = True

        if not has_history:
            return self._fallback_volatility(current_vol)

        if vol_long <= 0:
            return (
                VolatilityRegime.LOW
                if vol_short == Decimal(0)
                else VolatilityRegime.SPIKE
            )

        ratio_spike = Decimal(str(context.get("volatility_spike_multiplier", 2.0)))
        ratio_high = Decimal(str(context.get("volatility_high_multiplier", 1.3)))
        ratio_low = Decimal(str(context.get("volatility_low_multiplier", 0.5)))

        ratio = vol_short / vol_long

        if ratio >= ratio_spike:
            return VolatilityRegime.SPIKE
        if ratio >= ratio_high:
            return VolatilityRegime.HIGH
        if ratio <= ratio_low:
            return VolatilityRegime.LOW
        return VolatilityRegime.NORMAL

    def _classify_liquidity(self, context: dict[str, Any]) -> LiquidityRegime:
        """Classify liquidity regime from frequency, missing bars, and gaps."""
        tick_frequency = context.get("tick_frequency")  # Ticks per minute
        missing_bars = context.get("missing_bars", 0)
        stale_seconds = context.get("stale_seconds", 0)

        # Check for missing bars or quote staleness first
        if missing_bars >= 5 or stale_seconds >= 300:
            return LiquidityRegime.ILLIQUID
        if missing_bars >= 2 or stale_seconds >= 60:
            return LiquidityRegime.THIN

        if tick_frequency is not None:
            freq = Decimal(str(tick_frequency))
            if freq <= 2:
                return LiquidityRegime.ILLIQUID
            if freq <= 10:
                return LiquidityRegime.THIN

        return LiquidityRegime.NORMAL

    def _is_event_relevant(self, event: dict[str, Any], currencies: set[str]) -> bool:
        """Check if calendar event matches target currencies or symbol."""
        event_symbol = str(event.get("symbol", "")).upper()
        event_currency = str(event.get("currency", "")).upper()
        if not event_symbol and not event_currency:
            return True
        return event_symbol in currencies or event_currency in currencies

    def _classify_news(
        self,
        calendar_evidence: list[dict[str, Any]],
        context: dict[str, Any],
        now: datetime,
    ) -> NewsRegime:
        """Classify news blackout schedules from upcoming events."""
        if not calendar_evidence:
            return NewsRegime.NORMAL

        # Default blackout distance: 5 minutes before/after news release
        blackout_mins = float(context.get("news_blackout_mins", 5.0))

        symbol = context.get("symbol", "").upper()
        # Parse currency legs from symbol (e.g. EURUSD -> EUR, USD)
        currencies = {symbol}
        if len(symbol) == 6:
            currencies.add(symbol[:3])
            currencies.add(symbol[3:])

        for event in calendar_evidence:
            event_time_raw = event.get("time") or event.get("timestamp")
            if not event_time_raw:
                continue

            event_time = to_utc_datetime(
                parse_datetime(event_time_raw)
                if isinstance(event_time_raw, str)
                else event_time_raw
            )

            if not self._is_event_relevant(event, currencies):
                continue

            delta_seconds = abs((now - event_time).total_seconds())
            if delta_seconds <= blackout_mins * 60:
                impact = str(event.get("impact", "")).upper()
                if impact in {"HIGH", "BLACKOUT"}:
                    return NewsRegime.BLACKOUT
                if impact in {"MEDIUM", "HIGH_IMPACT"}:
                    return NewsRegime.HIGH_IMPACT

        return NewsRegime.NORMAL

    def _classify_rollover(
        self,
        rollover_time: datetime | None,
        now: datetime,
        context: dict[str, Any],
    ) -> RolloverRegime:
        """Classify rollover blackout window surrounding broker midnight."""
        if rollover_time is None:
            return RolloverRegime.NORMAL

        roll_utc = to_utc_datetime(rollover_time)
        before_mins = float(context.get("rollover_blackout_before_mins", 5.0))
        after_mins = float(context.get("rollover_blackout_after_mins", 5.0))

        # Check distance to rollover
        diff_seconds = (now - roll_utc).total_seconds()
        # If now is before rollover_time
        if diff_seconds < 0:
            if abs(diff_seconds) <= before_mins * 60:
                return RolloverRegime.BLACKOUT
        # If now is after rollover_time
        elif diff_seconds <= after_mins * 60:
            return RolloverRegime.BLACKOUT

        return RolloverRegime.NORMAL

    def _build_error_result(
        self,
        regime: RiskRegime,
        reason_code: RiskReasonCode,
        reason: str,
        timestamp: datetime,
        status: RiskDecisionStatus = RiskDecisionStatus.BLOCK,
    ) -> RegimeResult:
        """Helper to create fail-closed RegimeResult blocks."""
        logger.warning(f"Market regime assessment blocked: {reason}")
        return RegimeResult(
            regime=regime,
            spread_regime=SpreadRegime.EXTREME,
            volatility_regime=VolatilityRegime.SPIKE,
            liquidity_regime=LiquidityRegime.ILLIQUID,
            news_regime=NewsRegime.BLACKOUT,
            session_regime=SessionRegime.CLOSED,
            rollover_regime=RolloverRegime.BLACKOUT,
            status=status,
            reason=reason,
            reason_code=reason_code,
            timestamp=timestamp,
        )


def assess_risk_regime(
    market_snapshot: MarketRiskSnapshot,
    calendar_evidence: list[dict[str, Any]],
    risk_config: RiskConfig,
    market_context: dict[str, Any] | None = None,
) -> RegimeResult:
    """Assess market regime details through public stateless helper.

    Args:
        market_snapshot: The current quotes snapshot.
        calendar_evidence: List of upcoming news events.
        risk_config: Target active configuration settings.
        market_context: Extra parameters or historic lists.

    Returns:
        RegimeResult: Synthesized regime metrics and decision status.
    """
    ctx = market_context or {}
    engine = RegimeRiskEngine(config=risk_config)
    return engine.assess(market_snapshot, calendar_evidence, ctx)
