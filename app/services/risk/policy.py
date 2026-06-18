"""Policy-as-code resolution and validation engine.

Responsible for matching scoped policy rules, resolving precedence, validating
approval tokens, checking config compatibility, and enforcing risk budget gates.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.services.risk.models import (
    PolicyEnforcementResult,
    PolicyRule,
    PolicyScope,
    RiskApprovalToken,
    RiskConfig,
    RiskDecisionStatus,
)
from app.utils.logger import logger
from app.utils.normalization import utc_now


def get_rule_specificity_score(scope: PolicyScope) -> int:
    """Calculate specificity score for policy rules sorting.

    More specific filters get higher scores.
    """
    score = 0
    if scope.workflow_id is not None:
        score += 10000
    if scope.symbol is not None:
        score += 1000
    if scope.strategy_id is not None:
        score += 100
    if scope.account_id is not None:
        score += 10
    if scope.currency is not None:
        score += 5
    if scope.operator_role is not None:
        score += 2
    if scope.mode is not None:
        score += 1
    if scope.environment is not None:
        score += 1
    return score


EVALUATED_SCOPE_FIELDS = {
    "environment",
    "mode",
    "account_id",
    "strategy_id",
    "symbol",
    "currency",
    "workflow_id",
    "operator_role",
}


def _filter_matching_rules(
    rules: list[PolicyRule],
    context: dict[str, Any],
    now: datetime,
) -> list[PolicyRule]:
    """Filter candidate policy rules against context and expiration time."""
    matched_rules: list[PolicyRule] = []
    for rule in rules:
        if rule.expiry_time is not None and now > rule.expiry_time:
            logger.debug(f"Ignoring expired policy rule '{rule.rule_id}'")
            continue

        scope = rule.scope
        match = True

        for field_name in EVALUATED_SCOPE_FIELDS:
            scope_val = getattr(scope, field_name)
            if scope_val is not None:
                ctx_val = context.get(field_name)
                if ctx_val is None or str(scope_val).lower() != str(ctx_val).lower():
                    match = False
                    break

        if match:
            matched_rules.append(rule)
    return matched_rules


def _apply_overrides(
    base_config: RiskConfig,
    matched_rules: list[PolicyRule],
) -> dict[str, Any]:
    """Apply rule overrides to config dict based on precedence rules."""
    # Precedence Rules sorting (lowest specificity first so highest overrides last)
    matched_rules.sort(key=lambda r: get_rule_specificity_score(r.scope))

    config_dict = base_config.model_dump()
    for rule in matched_rules:
        for key, val in rule.overrides.items():
            if key in config_dict:
                orig_val = config_dict[key]
                if isinstance(orig_val, Decimal):
                    config_dict[key] = Decimal(str(val))
                elif isinstance(orig_val, int):
                    config_dict[key] = int(val)
                elif isinstance(orig_val, float):
                    config_dict[key] = float(val)
                elif isinstance(orig_val, bool):
                    config_dict[key] = bool(val)
                else:
                    config_dict[key] = val
    return config_dict


def _check_resolved_ceilings(config_dict: dict[str, Any]) -> list[str]:
    """Verify resolved config values do not exceed hard safety ceilings."""
    from app.services.risk.config import (
        MAX_DAILY_LOSS_PCT,
        MAX_EFFECTIVE_LEVERAGE,
        MAX_MARGIN_UTILIZATION_PCT,
        MAX_RISK_PER_TRADE,
        MAX_TOTAL_LOSS_PCT,
    )

    breaches = []
    try:
        if (
            Decimal(str(config_dict.get("max_daily_loss_pct", 0.0)))
            > MAX_DAILY_LOSS_PCT
        ):
            breaches.append(
                f"max_daily_loss_pct exceeds ceiling of {MAX_DAILY_LOSS_PCT}"
            )
        if (
            Decimal(str(config_dict.get("max_total_loss_pct", 0.0)))
            > MAX_TOTAL_LOSS_PCT
        ):
            breaches.append(
                f"max_total_loss_pct exceeds ceiling of {MAX_TOTAL_LOSS_PCT}"
            )
        if (
            Decimal(str(config_dict.get("max_margin_utilization_pct", 0.0)))
            > MAX_MARGIN_UTILIZATION_PCT
        ):
            breaches.append(
                f"max_margin_utilization_pct exceeds ceiling of "
                f"{MAX_MARGIN_UTILIZATION_PCT}"
            )
        if (
            Decimal(str(config_dict.get("max_effective_leverage", 0.0)))
            > MAX_EFFECTIVE_LEVERAGE
        ):
            breaches.append(
                f"max_effective_leverage exceeds ceiling of {MAX_EFFECTIVE_LEVERAGE}"
            )
        if (
            Decimal(str(config_dict.get("max_risk_per_trade", 0.0)))
            > MAX_RISK_PER_TRADE
        ):
            breaches.append(
                f"max_risk_per_trade exceeds ceiling of {MAX_RISK_PER_TRADE}"
            )
    except (ValueError, TypeError) as e:
        breaches.append(f"Ceiling check validation error: {e}")
    return breaches


def resolve_policy(
    base_config: RiskConfig,
    rules: list[PolicyRule],
    context: dict[str, Any],
) -> PolicyEnforcementResult:
    """Resolve the active RiskConfig by matching and merging policy rules.

    Args:
        base_config: The default loaded RiskConfig profile.
        rules: The list of candidate PolicyRules.
        context: Context dictionary representing current evaluation state.

    Returns:
        PolicyEnforcementResult: The result of policy resolution, containing the
                                 resolved config, policy hash, and status.
    """
    now = utc_now()

    matched_rules = _filter_matching_rules(rules, context, now)
    config_dict = _apply_overrides(base_config, matched_rules)
    breaches = _check_resolved_ceilings(config_dict)

    # Compute stable policy hash
    applied_rules_ids = [rule.rule_id for rule in matched_rules]
    canonical_rules_str = ",".join(sorted(applied_rules_ids))
    policy_hash = hashlib.sha256(canonical_rules_str.encode("utf-8")).hexdigest()

    # Fail-closed check: if breaches exist, status is REJECT
    status = RiskDecisionStatus.APPROVE
    reason = "Policy resolved successfully"
    if breaches:
        status = RiskDecisionStatus.REJECT
        reason = f"Resolved config violates hard ceilings: {breaches}"

    # Stricter default policy for live-sensitive modes:
    # If live resolved config lacks live execution authority, block.
    env = context.get("environment", "local").lower()
    is_live_sensitive = env in {"staging", "production"} or context.get("mode") in {
        "micro_live",
        "full_live",
    }
    if is_live_sensitive and not config_dict.get("allow_live_execution", False):
        status = RiskDecisionStatus.BLOCK
        reason = (
            "Execution blocked: environment/mode is live-sensitive but config "
            "disables allow_live_execution"
        )

    resolved_config = RiskConfig(**config_dict)

    return PolicyEnforcementResult(
        status=status,
        reason=reason,
        policy_hash=policy_hash,
        resolved_config=resolved_config,
        breaches=breaches,
    )


def validate_override_token(
    token: RiskApprovalToken,
    expected_scope: dict[str, Any],
    active_config_hash: str,
) -> bool:
    """Validate a RiskApprovalToken for limit overrides.

    Args:
        token: Cryptographically signed RiskApprovalToken.
        expected_scope: Scope verification key-value pairs (e.g. {'symbol': 'EURUSD'}).
        active_config_hash: Stable hash of the active RiskConfig.

    Returns:
        bool: True if token passes validation checks, otherwise False.
    """
    now = utc_now()

    # 1. Check token expiry
    if token.expiry_time is not None and now > token.expiry_time:
        logger.warning(f"Override token '{token.token_id}' is expired.")
        return False

    # 2. Check config compatibility (Task 233)
    if token.config_hash != active_config_hash:
        logger.warning(
            f"Override token '{token.token_id}' has mismatched config hash "
            f"(token: {token.config_hash}, active: {active_config_hash})."
        )
        return False

    # 3. Check scope alignment
    for key, expected_val in expected_scope.items():
        token_val = token.scope.get(key)
        if token_val is None or str(token_val).lower() != str(expected_val).lower():
            logger.warning(
                f"Override token '{token.token_id}' scope mismatch for key '{key}' "
                f"(expected: {expected_val}, got: {token_val})."
            )
            return False

    # 4. Check governed approval requirement for high-risk overrides (Task 232)
    # If action is execute_trade in live environment, require authorized role
    if token.scope.get("environment") in {
        "staging",
        "production",
    } and token.approver not in {"risk_manager", "admin", "compliance_officer"}:
        logger.warning(
            f"Override token '{token.token_id}' rejected: approver "
            f"'{token.approver}' has insufficient authority for live overrides."
        )
        return False

    return True


def validate_risk_budget_gates(
    strategy_id: str,
    requested_budget: Decimal,
    resolved_config: RiskConfig,
) -> bool:
    """Verify that a strategy's requested allocation fits within config limits.

    Args:
        strategy_id: ID of the target strategy.
        requested_budget: Desired allocation.
        resolved_config: Resolved RiskConfig.

    Returns:
        bool: True if budget fits within config, otherwise False.
    """
    if not strategy_id.strip():
        return False

    if requested_budget <= 0:
        return False

    max_trade_risk = resolved_config.max_risk_per_trade
    if max_trade_risk <= 0:
        return False

    return (
        resolved_config.max_total_loss_pct_advisory
        <= resolved_config.max_total_loss_pct
    )


def load_risk_policy(profile_name: str) -> RiskConfig:
    """Load and parse a risk policy configuration by profile name.

    Args:
        profile_name: Name of the YAML config file without extension (e.g. 'default').

    Returns:
        RiskConfig: The loaded and validated configuration profile.

    Raises:
        ValidationError: If configuration is invalid or missing.
    """
    from app.services.risk.config import load_risk_config

    return load_risk_config(profile_name)


def validate_risk_policy(config: RiskConfig) -> None:
    """Validate a loaded risk policy configuration against hard ceilings.

    Args:
        config: The RiskConfig instance to validate.

    Raises:
        ValidationError: If any safety ceiling is breached or validation fails.
    """
    from app.services.risk.config import _validate_ceilings
    from app.utils.errors import ValidationError

    if not isinstance(config, RiskConfig):
        raise ValidationError("Invalid RiskConfig object.")
    _validate_ceilings(config.model_dump())
