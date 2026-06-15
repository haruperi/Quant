"""ReadinessService implementation for checking trade readiness.

Verifies terminal connection, market availability, account permissions,
and rate limiting availability before allowing order placement.
"""

from typing import Any

from app.services.trader.account_info import AccountInfo
from app.services.trader.rate_limiter import get_rate_limiter
from app.services.trader.terminal_info import TerminalInfo
from app.utils.logger import logger


class ReadinessService:
    """Aggregates execution readiness checks before sending requests to the broker."""

    def run_execution_readiness_check(
        self,
        provider: str,
        symbol: str,
        term: TerminalInfo,
        acc: AccountInfo,
    ) -> dict[str, Any]:
        """Aggregate readiness checks before trade execution.

        Args:
            provider: Broker provider name ('mt5', 'ctrader', 'sim').
            symbol: Target trade symbol.
            term: TerminalInfo instance.
            acc: AccountInfo instance.

        Returns:
            dict[str, Any]: A dict containing:
                "passed": bool
                "errors": list[str]
                "details": dict[str, Any]
        """
        errors: list[str] = []
        details: dict[str, Any] = {}

        # 1. Connection check
        connected = term.connected()
        details["connected"] = connected
        if not connected:
            errors.append("Broker terminal is not connected to the server.")

        # 2. Market open check (terminal trade_allowed check)
        trade_allowed_term = term.trade_allowed()
        details["terminal_trade_allowed"] = trade_allowed_term
        if not trade_allowed_term:
            errors.append("Trading is disabled at the terminal level.")

        # 3. Account trade permission
        trade_allowed_acc = acc.trade_allowed()
        details["account_trade_allowed"] = trade_allowed_acc
        if not trade_allowed_acc:
            errors.append("Trading is disabled for this account.")

        # 4. Check if rate-limited
        limiter = get_rate_limiter(provider)
        rate_ok = limiter.check_rate_limit()
        details["rate_limit_ok"] = rate_ok
        if not rate_ok:
            errors.append(f"Rate limit exceeded for provider '{provider}'.")

        passed = len(errors) == 0
        if not passed:
            logger.warning(
                "Execution readiness check failed",
                extra={"provider": provider, "symbol": symbol, "errors": errors},
            )
        else:
            logger.info(
                "Execution readiness check passed",
                extra={"provider": provider, "symbol": symbol},
            )

        return {
            "passed": passed,
            "errors": errors,
            "details": details,
        }
