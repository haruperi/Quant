# ruff: noqa: E501, RUF022, RUF100
"""Strategies service module entry point.

This module exposes thread-safe registry methods, execution wrappers,
type protocols, schemas, and deterministic domain errors.
"""

from __future__ import annotations

from typing import cast

from app.services.strategies.base import BaseStrategy
from app.services.strategies.event import (
    StrategyStateCheckpoint,
    create_state_checkpoint,
    run_strategy_hook,
    validate_and_restore_checkpoint,
)
from app.services.strategies.protocols import (
    ReadOnlyExecutionStateQuery,
    ReadOnlyExecutionStateSnapshot,
    StrategyConfigInput,
    StrategyDiagnostics,
    StrategyEnvironment,
    StrategyExecutionContext,
    StrategyIntentType,
    StrategyProtocol,
    StrategyRefInput,
    StrategyRiskProfile,
    StrategySide,
    StrategyTimingPolicy,
    TradeIntent,
)
from app.services.strategies.registry import (
    StrategyRegistry,
    get_strategy,
    global_registry,
    list_strategies,
    register_strategy,
    unregister_strategy,
    validate_strategy_config,
    validate_strategy_ref,
)
from app.services.strategies.sandbox import vet_and_sandbox_code
from app.services.strategies.source.random_walk import RandomWalkStrategy
from app.services.strategies.source.trend_following import TrendFollowingStrategy
from app.services.strategies.vectorized import run_vectorized_strategy_signals
from app.utils.errors import (
    IndicatorModuleError,
    SimArbitraryCodeRejectedError,
    StrategyArtifactHashMismatchError,
    StrategyCheckpointIncompatibleError,
    StrategyCheckpointInvalidError,
    StrategyCircuitBreakerTriggeredError,
    StrategyConfigError,
    StrategyDataNotReadyError,
    StrategyDataQualityGateFailedError,
    StrategyDeprecatedError,
    StrategyDriftDetectedError,
    StrategyDuplicateIntentError,
    StrategyEnvironmentNotPermittedError,
    StrategyError,
    StrategyHardKilledError,
    StrategyIndicatorNotReadyError,
    StrategyInternalError,
    StrategyLifecycleNotApprovedError,
    StrategyLookaheadDetectedError,
    StrategyMarketAccessRevokedError,
    StrategyMissingRequiredDataError,
    StrategyNotFoundError,
    StrategyPerformanceDegradedError,
    StrategyPositionLimitExceededError,
    StrategyRegulatoryLimitBreachedError,
    StrategyResourceLimitExceededError,
    StrategyRiskProfileRequiredError,
    StrategySchemaValidationFailedError,
    StrategyStaleDataError,
    StrategyTimeoutError,
    StrategyUnsupportedTimingPolicyError,
    StrategyValidationArtifactRequiredError,
    StrategyVersionConstraintUnsatisfiableError,
    map_exception_to_strategy_error,
)

__all__ = [
    # Protocols and Schemas
    "BaseStrategy",
    "StrategyEnvironment",
    "StrategySide",
    "StrategyIntentType",
    "StrategyTimingPolicy",
    "StrategyRefInput",
    "StrategyConfigInput",
    "ReadOnlyExecutionStateQuery",
    "ReadOnlyExecutionStateSnapshot",
    "StrategyExecutionContext",
    "TradeIntent",
    "StrategyDiagnostics",
    "StrategyRiskProfile",
    "StrategyProtocol",
    "TrendFollowingStrategy",
    "RandomWalkStrategy",
    # Registry Catalog
    "StrategyRegistry",
    "global_registry",
    "register_strategy",
    "get_strategy",
    "unregister_strategy",
    "list_strategies",
    "validate_strategy_ref",
    "validate_strategy_config",
    # Run Wrappers
    "run_vectorized_strategy_signals",
    "run_strategy_hook",
    "StrategyStateCheckpoint",
    "create_state_checkpoint",
    "validate_and_restore_checkpoint",
    "vet_and_sandbox_code",
    # Errors
    "StrategyError",
    "StrategyConfigError",
    "StrategyNotFoundError",
    "StrategyVersionConstraintUnsatisfiableError",
    "StrategyDeprecatedError",
    "StrategyUnapprovedModuleError",
    "StrategySchemaValidationFailedError",
    "StrategyUnsupportedTimingPolicyError",
    "StrategyLookaheadDetectedError",
    "SimArbitraryCodeRejectedError",
    "StrategyInternalError",
    "StrategyLifecycleNotApprovedError",
    "StrategyEnvironmentNotPermittedError",
    "StrategyArtifactHashMismatchError",
    "StrategyDependencyHashMismatchError",
    "IndicatorModuleError",
    "StrategyCheckpointInvalidError",
    "StrategyCheckpointIncompatibleError",
    "StrategyDataNotReadyError",
    "StrategyIndicatorNotReadyError",
    "StrategyMissingRequiredDataError",
    "StrategyStaleDataError",
    "StrategyDuplicateIntentError",
    "StrategyResourceLimitExceededError",
    "StrategyTimeoutError",
    "StrategyValidationArtifactRequiredError",
    "StrategyRiskProfileRequiredError",
    "StrategyCircuitBreakerTriggeredError",
    "StrategyPositionLimitExceededError",
    "StrategyVolumeParticipationExceededError",
    "StrategyDataQualityGateFailedError",
    "StrategyPerformanceDegradedError",
    "StrategyDriftDetectedError",
    "StrategyRegulatoryLimitBreachedError",
    "StrategyMarketAccessRevokedError",
    "StrategyHardKilledError",
    "map_exception_to_strategy_error",
]

# Auto-register standard implementations
register_strategy(cast("type[StrategyProtocol]", TrendFollowingStrategy))
register_strategy(cast("type[StrategyProtocol]", RandomWalkStrategy))
