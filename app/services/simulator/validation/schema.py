"""Simulator schema validation helpers.

Exports request parsing and safe strategy-payload checks for simulator public
entry points. The module has no import-time side effects.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from app.services.simulator.models import (
    SimulatorActorContext,
    SimulatorBacktestRequestV1,
)
from app.services.strategies.registry import validate_config_security
from app.utils.errors import SimArbitraryCodeRejectedError, ValidationError
from app.utils.standard import canonical_json

MAX_BACKTEST_REQUEST_BYTES = 65536


def reject_arbitrary_strategy_code(payload: object) -> None:
    """Reject raw Python strategy code or known injection strings.

    Args:
        payload: Candidate strategy payload.

    Returns:
        None.

    Raises:
        SimArbitraryCodeRejectedError: If unsafe code-like content is detected.
    """
    if isinstance(payload, str):
        blocked = ("def ", "class ", "import ", "exec(", "eval(", "__import__")
        if any(token in payload for token in blocked):
            raise SimArbitraryCodeRejectedError(
                "Raw arbitrary Python strategy code is not accepted.",
                code="SIM_ARBITRARY_CODE_REJECTED",
            )
    if isinstance(payload, Mapping):
        for value in payload.values():
            reject_arbitrary_strategy_code(value)
    if isinstance(payload, list | tuple | set):
        for value in payload:
            reject_arbitrary_strategy_code(value)


def parse_backtest_request(payload: Mapping[str, Any]) -> SimulatorBacktestRequestV1:
    """Parse a mapping into a validated simulator backtest request.

    Args:
        payload: Raw user or service request payload.

    Returns:
        SimulatorBacktestRequestV1: Validated request.

    Raises:
        ValidationError: If fields are malformed.
        SimArbitraryCodeRejectedError: If raw Python code is detected.
    """
    encoded = canonical_json(payload).encode("utf-8")
    if len(encoded) > MAX_BACKTEST_REQUEST_BYTES:
        raise ValidationError(
            "Simulator request exceeds maximum payload size.",
            code="SIM_INVALID_CONFIG",
        )
    allowed_fields = {
        "schema_version",
        "request_id",
        "actor_context",
        "strategy_ref",
        "strategy_config",
        "symbols",
        "timeframe",
        "start",
        "end",
        "initial_balance",
        "account_currency",
        "tick_model",
        "spread_model",
        "slippage_model",
        "commission_model",
        "swap_model",
        "broker_profile_ref",
        "market_data_authority_ref",
        "journal_persistence",
        "artifact_root_ref",
        "realism_profile",
        "metadata",
    }
    unknown = set(payload).difference(allowed_fields)
    if unknown:
        message = f"Unknown simulator request fields: {sorted(unknown)}"
        raise ValidationError(message)
    reject_arbitrary_strategy_code(payload.get("strategy_ref"))
    reject_arbitrary_strategy_code(payload.get("strategy_config", {}))
    validate_config_security(payload.get("strategy_config", {}))
    actor_raw = payload.get("actor_context")
    if not isinstance(actor_raw, Mapping):
        raise ValidationError("actor_context is required.")
    roles_raw = actor_raw.get("roles", ("researcher",))
    if not isinstance(roles_raw, list | tuple):
        raise ValidationError("actor_context.roles must be a list or tuple.")
    actor = SimulatorActorContext(
        actor_id=str(actor_raw.get("actor_id", "")),
        roles=tuple(str(role) for role in roles_raw),
        auth_source=str(actor_raw.get("auth_source", "local")),
    )
    symbols_raw = payload.get("symbols")
    if not isinstance(symbols_raw, list | tuple):
        raise ValidationError("symbols must be a list or tuple.")
    metadata_raw = payload.get("metadata", {})
    if not isinstance(metadata_raw, Mapping):
        raise ValidationError("metadata must be a mapping.")
    artifact_root_raw = payload.get("artifact_root_ref")
    if artifact_root_raw is not None:
        artifact_root_ref = str(artifact_root_raw)
        if any(token in artifact_root_ref for token in ("..", "/", "\\", ":")):
            raise ValidationError(
                "artifact_root_ref must be an allowlisted artifact-root reference.",
                code="SIM_INVALID_CONFIG",
            )
    else:
        artifact_root_ref = None
    return SimulatorBacktestRequestV1(
        schema_version=str(payload.get("schema_version", "1.0.0")),
        request_id=str(payload.get("request_id", "")),
        actor_context=actor,
        strategy_ref=str(payload.get("strategy_ref", "")),
        strategy_config=dict(payload.get("strategy_config", {})),
        symbols=tuple(str(symbol) for symbol in symbols_raw),
        timeframe=str(payload.get("timeframe", "")),
        start=str(payload.get("start", "")),
        end=str(payload.get("end", "")),
        initial_balance=float(payload.get("initial_balance", 100000.0)),
        account_currency=str(payload.get("account_currency", "USD")),
        tick_model=str(payload.get("tick_model", "deterministic_midpoint_v1")),
        spread_model=str(payload.get("spread_model", "fixed_points_v1")),
        slippage_model=str(payload.get("slippage_model", "none_v1")),
        commission_model=str(payload.get("commission_model", "none_v1")),
        swap_model=str(payload.get("swap_model", "none_v1")),
        broker_profile_ref=str(
            payload.get("broker_profile_ref", "mt5_demo_reference_fx_v1")
        ),
        market_data_authority_ref=str(
            payload.get("market_data_authority_ref", "local_synthetic_v1")
        ),
        journal_persistence=str(payload.get("journal_persistence", "memory")),  # type: ignore[arg-type]
        artifact_root_ref=artifact_root_ref,
        realism_profile=str(payload.get("realism_profile", "research_approximation")),  # type: ignore[arg-type]
        metadata=dict(metadata_raw),
    )
