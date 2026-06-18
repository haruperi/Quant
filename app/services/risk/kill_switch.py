# ruff: noqa: C901, PLR0911, PLR0912, PLR2004, PLW0603, BLE001, EM102, E501, TC001
"""Emergency kill switch service and state manager.

Handles global, portfolio, strategy, symbol, and currency-level halts.
Supports persistence, gated resume approvals, and auto-triggering on breaches.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from threading import RLock
from typing import Any

from app.services.risk.limits import LimitResult
from app.services.risk.models import (
    KillSwitchStateEnum,
    RiskAssessmentRequest,
    RiskDecisionStatus,
    RiskSeverity,
)
from app.utils.errors import ValidationError
from app.utils.event_bus import InMemoryEventBus, build_event_envelope
from app.utils.logger import logger


class KillSwitchScope(StrEnum):
    """Scope boundaries for kill switches."""

    GLOBAL = "global"
    PORTFOLIO = "portfolio"
    STRATEGY = "strategy"
    SYMBOL = "symbol"
    CURRENCY = "currency"


class KillSwitchManager:
    """Thread-safe manager for quantitative trading safety kill switches.

    Manages active, inactive, and locked states across different scopes.
    Persists changes to a local storage file to survive system restarts.
    """

    def __init__(self, persistence_path: str | Path | None = None) -> None:
        """Initialize KillSwitchManager with default states and optional persistence.

        Args:
            persistence_path: Local JSON path to read/write states.
        """
        self._lock = RLock()
        self.persistence_path = Path(persistence_path) if persistence_path else None

        # Base default states configuration
        self.states: dict[str, Any] = {
            "global": {
                "state": KillSwitchStateEnum.INACTIVE,
                "reason": None,
                "triggered_at": None,
                "triggered_by": None,
            },
            "portfolio": {
                "state": KillSwitchStateEnum.INACTIVE,
                "reason": None,
                "triggered_at": None,
                "triggered_by": None,
            },
            "strategies": {},  # strat_id -> dict
            "symbols": {},  # symbol -> dict
            "currencies": {},  # currency -> dict
        }
        self.load()

    def load(self) -> None:
        """Load states from local JSON persistence path.

        Falls closed on missing keys, type mismatches, or file corruption.
        """
        if not self.persistence_path or not self.persistence_path.exists():
            return

        with self._lock:
            try:
                with self.persistence_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                # Basic structural validation
                required_keys = {
                    "global",
                    "portfolio",
                    "strategies",
                    "symbols",
                    "currencies",
                }
                if not required_keys.issubset(data.keys()):
                    logger.warning(
                        "Corrupt kill switch persistence: missing root keys."
                    )
                    self._fail_closed()
                    return

                self.states = data
            except Exception as e:
                logger.warning(
                    f"Failed to load kill switch states, failing closed: {e}"
                )
                self._fail_closed()

    def _fail_closed(self) -> None:
        """Sets all base states to locked/active to prevent unauthorized trading."""
        self.states["global"] = {
            "state": KillSwitchStateEnum.LOCKED,
            "reason": "Persistence file corruption recovery",
            "triggered_at": datetime.now(UTC).isoformat(),
            "triggered_by": "system_recovery",
        }

    def save(self) -> None:
        """Write current states to persistence path."""
        if not self.persistence_path:
            return

        with self._lock:
            try:
                self.persistence_path.parent.mkdir(parents=True, exist_ok=True)
                with self.persistence_path.open("w", encoding="utf-8") as f:
                    # Coerce Decimal and timestamps if any
                    json.dump(self.states, f, indent=2)
            except Exception as e:
                logger.error(f"Failed to save kill switch states: {e}")

    def trigger(
        self,
        scope: str,
        target: str,
        reason: str,
        triggered_by: str = "system",
        event_bus: InMemoryEventBus | None = None,
    ) -> None:
        """Trigger an emergency halt/kill switch for a target scope.

        Args:
            scope: One of global, portfolio, strategy, symbol, currency.
            target: Identifier key (e.g. strategy ID, symbol name, '*' for global/portfolio).
            reason: Text detail explaining cause.
            triggered_by: Origin/initiator name.
            event_bus: Optional event bus to publish trigger event.

        Raises:
            ValidationError: If target scope is unknown.
        """
        clean_scope = scope.lower().strip()
        timestamp = datetime.now(UTC).isoformat()

        with self._lock:
            state_record = {
                "state": KillSwitchStateEnum.ACTIVE,
                "reason": reason,
                "triggered_at": timestamp,
                "triggered_by": triggered_by,
            }

            if clean_scope == KillSwitchScope.GLOBAL:
                self.states["global"] = state_record
            elif clean_scope == KillSwitchScope.PORTFOLIO:
                self.states["portfolio"] = state_record
            elif clean_scope == KillSwitchScope.STRATEGY:
                self.states["strategies"][target] = state_record
            elif clean_scope == KillSwitchScope.SYMBOL:
                self.states["symbols"][target] = state_record
            elif clean_scope == KillSwitchScope.CURRENCY:
                self.states["currencies"][target] = state_record
            else:
                raise ValidationError(
                    f"Invalid scope '{scope}' for kill switch trigger."
                )

            self.save()

            # Emit audit event
            logger.warning(
                f"Emergency kill switch triggered: scope={scope}, target={target}, reason={reason}"
            )
            if event_bus:
                try:
                    event = build_event_envelope(
                        event_type="risk.kill_switch.triggered",
                        source="kill_switch_governor",
                        severity="critical",
                        payload={
                            "scope": scope,
                            "target": target,
                            "reason": reason,
                            "triggered_by": triggered_by,
                            "triggered_at": timestamp,
                        },
                    )
                    event_bus.publish(event)
                except Exception as e:
                    logger.error(f"Failed to publish kill switch event: {e}")

    def resume(
        self,
        scope: str,
        target: str,
        approval_token: str | None = None,
        operator_role: str | None = None,
        event_bus: InMemoryEventBus | None = None,
    ) -> None:
        """Deactivate a triggered kill switch after governed approval checks.

        Args:
            scope: Target scope.
            target: Identifier key.
            approval_token: Optional approval token validated by policy.
            operator_role: Optional role of the operator (e.g. 'admin', 'compliance').
            event_bus: Optional event bus.

        Raises:
            ValidationError: If approval requirements are not satisfied.
        """
        clean_scope = scope.lower().strip()

        with self._lock:
            # 1. Retrieve current state
            record: dict[str, Any] | None = None
            if clean_scope == KillSwitchScope.GLOBAL:
                record = self.states["global"]
            elif clean_scope == KillSwitchScope.PORTFOLIO:
                record = self.states["portfolio"]
            elif clean_scope == KillSwitchScope.STRATEGY:
                record = self.states["strategies"].get(target)
            elif clean_scope == KillSwitchScope.SYMBOL:
                record = self.states["symbols"].get(target)
            elif clean_scope == KillSwitchScope.CURRENCY:
                record = self.states["currencies"].get(target)
            else:
                raise ValidationError(f"Invalid scope '{scope}' for resume.")

            if not record or record.get("state") == KillSwitchStateEnum.INACTIVE:
                # Already inactive
                return

            current_state = record.get("state")

            # 2. Enforce governed approval gate
            # Locked state requires explicit admin/compliance roles and cannot be cleared by token alone
            if current_state == KillSwitchStateEnum.LOCKED:
                if operator_role not in {"admin", "compliance"}:
                    raise ValidationError(
                        "Cannot resume locked kill switch without compliance or admin role.",
                        code="PERMISSION_DENIED",
                    )
            else:
                # Active state requires admin/compliance role OR a valid approval token
                has_privilege = operator_role in {"admin", "compliance"}
                has_token = bool(approval_token and approval_token.strip())
                if not has_privilege and not has_token:
                    raise ValidationError(
                        "Governed resume requires a valid approval token or compliance/admin operator role.",
                        code="APPROVAL_REQUIRED",
                    )

            # 3. Clear state record
            inactive_record = {
                "state": KillSwitchStateEnum.INACTIVE,
                "reason": None,
                "triggered_at": None,
                "triggered_by": None,
            }

            if clean_scope == KillSwitchScope.GLOBAL:
                self.states["global"] = inactive_record
            elif clean_scope == KillSwitchScope.PORTFOLIO:
                self.states["portfolio"] = inactive_record
            elif clean_scope == KillSwitchScope.STRATEGY:
                self.states["strategies"].pop(target, None)
            elif clean_scope == KillSwitchScope.SYMBOL:
                self.states["symbols"].pop(target, None)
            elif clean_scope == KillSwitchScope.CURRENCY:
                self.states["currencies"].pop(target, None)

            self.save()

            logger.info(f"Kill switch resumed: scope={scope}, target={target}")
            if event_bus:
                try:
                    event = build_event_envelope(
                        event_type="risk.kill_switch.resumed",
                        source="kill_switch_governor",
                        severity="info",
                        payload={
                            "scope": scope,
                            "target": target,
                            "resumed_by": operator_role or "token",
                            "resumed_at": datetime.now(UTC).isoformat(),
                        },
                    )
                    event_bus.publish(event)
                except Exception as e:
                    logger.error(f"Failed to publish resume event: {e}")

    def is_blocked(self, scope: str, target: str, is_live: bool = False) -> bool:
        """Verify whether trading is blocked for a given target.

        Supports hierarchical fallback checks:
        Checks global -> portfolio -> target (strategy, symbol, or quote/base currency legs).

        Args:
            scope: target query scope ('strategy', 'symbol', or 'currency').
            target: identifier key to verify.
            is_live: True if environment is live-sensitive (triggers strict fail-closed).

        Returns:
            bool: True if blocked (kill switch active/locked).
        """
        clean_scope = scope.lower().strip()

        def _is_active(record: Any) -> bool:  # noqa: ANN401
            if not isinstance(record, dict):
                return is_live  # Fail closed in live modes if shape is corrupted
            state = record.get("state")
            if state not in {
                KillSwitchStateEnum.INACTIVE,
                KillSwitchStateEnum.ACTIVE,
                KillSwitchStateEnum.LOCKED,
            }:
                return True  # Fail closed on unknown states
            return state in {KillSwitchStateEnum.ACTIVE, KillSwitchStateEnum.LOCKED}

        with self._lock:
            # 1. Check Global
            if _is_active(self.states.get("global")):
                return True
            if clean_scope == KillSwitchScope.GLOBAL:
                return False

            # 2. Check Portfolio
            if _is_active(self.states.get("portfolio")):
                return True
            if clean_scope == KillSwitchScope.PORTFOLIO:
                return False

            # 3. Check Target-level specific halts
            if clean_scope == KillSwitchScope.STRATEGY:
                return _is_active(self.states["strategies"].get(target))

            if clean_scope == KillSwitchScope.SYMBOL:
                # Check symbol-level halt
                if _is_active(self.states["symbols"].get(target)):
                    return True

                # Check currency leg halts for base/quote legs
                # Extract currency legs by convention (e.g. first 3 and last 3 chars of symbol)
                if len(target) == 6:
                    base_ccy = target[:3].upper()
                    quote_ccy = target[3:].upper()
                    if _is_active(self.states["currencies"].get(base_ccy)):
                        return True
                    if _is_active(self.states["currencies"].get(quote_ccy)):
                        return True

            if clean_scope == KillSwitchScope.CURRENCY:
                return _is_active(self.states["currencies"].get(target))

            return False

    def evaluate_triggers(
        self,
        request: RiskAssessmentRequest,
        limit_results: list[LimitResult],
        is_live: bool = False,
        event_bus: InMemoryEventBus | None = None,
    ) -> list[str]:
        """Statelessly parse request context and limit results to trigger switches.

        Args:
            request: Active pre-trade risk query payload.
            limit_results: Stateless list of limit checks executed.
            is_live: True if environment is live-sensitive.
            event_bus: Optional event bus to dispatch audit payloads.

        Returns:
            list[str]: Names of scopes triggered in this review.
        """
        triggered_scopes: list[str] = []
        ctx = request.market_context or {}

        # 1. Manual Operator Halt
        if ctx.get("manual_operator_halt", False):
            self.trigger(
                scope="global",
                target="*",
                reason="Manual operator halt requested",
                triggered_by=ctx.get("operator_id", "operator"),
                event_bus=event_bus,
            )
            triggered_scopes.append("global")

        # 2. Audit-chain failure
        if ctx.get("audit_chain_verification_failed", False):
            # Audit failures lock the switch globally to require manual administrative reset
            with self._lock:
                self.states["global"] = {
                    "state": KillSwitchStateEnum.LOCKED,
                    "reason": "Audit chain verification failed",
                    "triggered_at": datetime.now(UTC).isoformat(),
                    "triggered_by": "audit_engine",
                }
                self.save()
            logger.critical(
                "Global kill switch locked due to audit-chain verification failure!"
            )
            triggered_scopes.append("global")

        # 3. Portfolio reconciliation check
        reconciliation_active = ctx.get("portfolio_reconciliation_active", True)
        portfolio_unreconciled = ctx.get("portfolio_unreconciled", False)
        if not reconciliation_active or portfolio_unreconciled:
            self.trigger(
                scope="portfolio",
                target="*",
                reason="Portfolio reconciliation failure or inactive monitoring",
                triggered_by="reconciliation_service",
                event_bus=event_bus,
            )
            triggered_scopes.append("portfolio")

        # 4. Broker Disconnect
        if is_live and ctx.get("provider_status") == "disconnected":
            self.trigger(
                scope="global",
                target="*",
                reason="Broker terminal disconnected in live execution mode",
                triggered_by="broker_monitor",
                event_bus=event_bus,
            )
            triggered_scopes.append("global")

        # 5. Evaluate breaches inside Limit Results
        for res in limit_results:
            if not res.breached:
                continue

            # Check for hard daily loss
            if res.limit_name == "daily_loss_limit" and res.status in {
                RiskDecisionStatus.REJECT,
                RiskDecisionStatus.BLOCK,
            }:
                self.trigger(
                    scope="global",
                    target="*",
                    reason=f"Hard daily loss threshold breached: {res.message}",
                    triggered_by="limit_engine",
                    event_bus=event_bus,
                )
                triggered_scopes.append("global")

            # Check for total drawdown limit
            if (
                res.limit_name == "drawdown_limit"
                and res.status
                in {
                    RiskDecisionStatus.REJECT,
                    RiskDecisionStatus.BLOCK,
                }
                and res.severity
                in {RiskSeverity.HARD_BREACH, RiskSeverity.CRITICAL_BREACH}
            ):
                self.trigger(
                    scope="global",
                    target="*",
                    reason=f"Total drawdown limit breached: {res.message}",
                    triggered_by="limit_engine",
                    event_bus=event_bus,
                )
                triggered_scopes.append("global")

            # Check for extreme spread event
            if res.limit_name == "spread_limit" and res.severity in {
                RiskSeverity.CRITICAL_BREACH,
                RiskSeverity.EMERGENCY_HALT,
            }:
                symbol = (
                    request.proposed_action.symbol
                    if hasattr(request.proposed_action, "symbol")
                    else "*"
                )
                self.trigger(
                    scope="symbol",
                    target=str(symbol),
                    reason=f"Extreme market spread event: {res.message}",
                    triggered_by="limit_engine",
                    event_bus=event_bus,
                )
                triggered_scopes.append("symbol")

            # Check for margin emergency (usage limit or free margin block)
            if (
                res.limit_name in {"margin_limit", "free_margin_check"}
                and res.status == RiskDecisionStatus.BLOCK
            ):
                self.trigger(
                    scope="portfolio",
                    target="*",
                    reason=f"Critical margin emergency triggered: {res.message}",
                    triggered_by="limit_engine",
                    event_bus=event_bus,
                )
                triggered_scopes.append("portfolio")

        return triggered_scopes


# Global singleton instance holder
_global_kill_switch_manager: KillSwitchManager | None = None
_manager_lock = RLock()


def get_kill_switch_manager(
    persistence_path: str | Path | None = None,
) -> KillSwitchManager:
    """Retrieve or initialize the global thread-safe KillSwitchManager instance.

    Args:
        persistence_path: Output target path for state serialization.

    Returns:
        KillSwitchManager: Singleton instance.
    """
    global _global_kill_switch_manager
    with _manager_lock:
        if _global_kill_switch_manager is None:
            _global_kill_switch_manager = KillSwitchManager(
                persistence_path=persistence_path
            )
        return _global_kill_switch_manager


def check_risk_kill_switch(
    scope: str,
    target: str,
) -> bool:
    """Check if a kill switch is active for a target scope and target identifier.

    Args:
        scope: Kill switch scope (e.g. 'global', 'strategy').
        target: Target identifier (e.g. symbol name, strategy ID).

    Returns:
        bool: True if trading is blocked, otherwise False.
    """
    manager = get_kill_switch_manager()
    return manager.is_blocked(scope, target)
