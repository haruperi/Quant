# ruff: noqa: E501
"""Deterministic HaruQuant error utilities.

This module provides support helpers, not official AI tools. It exports typed
HaruQuant exceptions, the approved deterministic error-code registry, safe
error-code normalization, fallback messages, exception-to-error-payload
mapping helpers, and the error router.

Public exports:
    APPROVED_ERROR_CODES, ERROR_MESSAGES, Error, ValidationError,
    ConfigurationError, SecurityError, DataError, ExternalServiceError,
    error_name, message_for, normalize_error_code, code_for_exception,
    details_for_exception, exception_to_error_payload, raise_for_invalid_code,
    ErrorRouteResult, ErrorRouter, route_error,
    IndicatorError, IndicatorConfigError, IndicatorParameterError,
    UnsupportedIndicatorError, UnsupportedTimeframeError, UnsupportedDtypeError,
    InvalidInputSchemaError, MissingRequiredColumnError, InvalidOutputColumnError,
    OutputColumnConflictError, InvalidOutputModeError, InputMutationError,
    DuplicateTimestampError, NonMonotonicTimeError, AmbiguousTimestampError,
    InvalidTimezoneError, InvalidOHLCError, InsufficientDataError,
    LookaheadRiskError, UnknownAdjustmentStatusError, StateIncompatibleError,
    StateCorruptedError, ResourceLimitExceededError,
    UnsupportedIntraBarAdjustmentError, SymbolMappingRequiredError,
    StubQuoteRejectedError, InvertedMarketError, SpreadThresholdExceededError,
    FormulaVersionMismatchError, DeprecatedIndicatorError,
    UnsupportedOutOfCoreError, AccelerationBackendUnavailableError,
    IndicatorTimeoutError, CalculationCancelledError, PartialResultError,
    UnsupportedIncrementalModeError, CustomIndicatorRejectedError,
    AccessDeniedError, ProprietaryUnauthorizedError, SLOViolationError,
    StrategyError, StrategyConfigError, StrategyNotFoundError,
    StrategyVersionConstraintUnsatisfiableError, StrategyDeprecatedError,
    StrategyUnapprovedModuleError, StrategySchemaValidationFailedError,
    StrategyUnsupportedTimingPolicyError, StrategyLookaheadDetectedError,
    SimArbitraryCodeRejectedError, StrategyInternalError,
    StrategyLifecycleNotApprovedError, StrategyEnvironmentNotPermittedError,
    StrategyArtifactHashMismatchError, StrategyDependencyHashMismatchError,
    IndicatorModuleError, StrategyCheckpointInvalidError,
    StrategyCheckpointIncompatibleError, StrategyDataNotReadyError,
    StrategyIndicatorNotReadyError, StrategyMissingRequiredDataError,
    StrategyStaleDataError, StrategyDuplicateIntentError,
    StrategyResourceLimitExceededError, StrategyTimeoutError,
    StrategyValidationArtifactRequiredError, StrategyRiskProfileRequiredError,
    StrategyCircuitBreakerTriggeredError, StrategyPositionLimitExceededError,
    StrategyVolumeParticipationExceededError, StrategyDataQualityGateFailedError,
    StrategyPerformanceDegradedError, StrategyDriftDetectedError,
    StrategyRegulatoryLimitBreachedError, StrategyMarketAccessRevokedError,
    StrategyHardKilledError, TradingError, TradingTimeoutError,
    UnknownOutcomeError, classify_broker_error, trading_retry_delay,
    map_exception_to_strategy_error.

Side effects:
    None. Importing this module does not configure logging, read files, import
    optional dependencies, call networks, or mutate live trading state.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from random import random
from typing import TYPE_CHECKING, Literal, TypedDict

from app.utils.logger import logger
from app.utils.security import redact_mapping, redact_text

if TYPE_CHECKING:
    from app.utils.event_bus import InMemoryEventBus

APPROVED_ERROR_CODES = frozenset(
    {
        "INVALID_INPUT",
        "PERMISSION_DENIED",
        "DATA_NOT_FOUND",
        "EMPTY_RESULT",
        "SERVICE_UNAVAILABLE",
        "BROKER_UNAVAILABLE",
        "DATABASE_ERROR",
        "NETWORK_ERROR",
        "TIMEOUT",
        "VALIDATION_FAILED",
        "CONFIGURATION_ERROR",
        "TOOL_EXECUTION_FAILED",
        "UNKNOWN_ERROR",
        "INVALID_AUTH_CONTEXT",
        "AUTHORIZATION_FAILED",
        "INVALID_EVENT",
        "EVENT_PUBLISH_FAILED",
        "EVENT_HANDLER_FAILED",
        "EVENT_DEAD_LETTER_FAILED",
        "QUEUE_FULL",
        "BACKPRESSURE_EXCEEDED",
        "NOTIFICATION_FAILED",
        "NOTIFICATION_SUPPRESSED",
        "NOTIFICATION_THROTTLED",
        "OBSERVABILITY_ERROR",
        "METRICS_EXPORT_FAILED",
        "CLOCK_DRIFT_DETECTED",
        "CIRCUIT_OPEN",
        "SECRET_VERSION_NOT_FOUND",
        "SECRET_VERSION_CONFLICT",
        "DATA_DROPPED",
        "CIRCUIT_BREAKER_OPEN",
        "AUTHENTICATION_FAILED",
        "MISSING_ASSET_METADATA",
        "DB_CONNECTION_ERROR",
        "DB_WRITE_FAILED",
        "STATE_RECOVERY_FAILED",
        "CHECKPOINT_CORRUPTED",
        "CREDENTIALS_MISSING",
        "BUFFER_OVERFLOW",
        "FEED_HEARTBEAT_TIMEOUT",
        "FEED_RECONCILIATION_FAILED",
        "JOB_NOT_FOUND",
        "SCHEDULER_ERROR",
        "LICENSE_RESTRICTION",
        "UNSUPPORTED_OPERATION",
        # Custom Indicator Codes
        "IND_INVALID_CONFIG",
        "IND_INVALID_PARAMETER",
        "IND_UNSUPPORTED_INDICATOR",
        "IND_UNSUPPORTED_TIMEFRAME",
        "IND_UNSUPPORTED_DTYPE",
        "IND_INVALID_INPUT_SCHEMA",
        "IND_MISSING_REQUIRED_COLUMN",
        "IND_INVALID_OUTPUT_COLUMN",
        "IND_OUTPUT_COLUMN_CONFLICT",
        "IND_INVALID_OUTPUT_MODE",
        "IND_INPUT_MUTATION_DETECTED",
        "IND_DUPLICATE_TIMESTAMP",
        "IND_NON_MONOTONIC_TIME",
        "IND_AMBIGUOUS_TIMESTAMP",
        "IND_INVALID_TIMEZONE",
        "IND_INVALID_OHLC",
        "IND_INSUFFICIENT_DATA",
        "IND_LOOKAHEAD_RISK",
        "IND_UNKNOWN_ADJUSTMENT_STATUS",
        "IND_STATE_INCOMPATIBLE",
        "IND_STATE_CORRUPTED",
        "IND_RESOURCE_LIMIT_EXCEEDED",
        "IND_INTRA_BAR_ADJUSTMENT_UNSUPPORTED",
        "IND_SYMBOL_MAPPING_REQUIRED",
        "IND_STUB_QUOTE_REJECTED",
        "IND_INVERTED_MARKET",
        "IND_SPREAD_THRESHOLD_EXCEEDED",
        "IND_FORMULA_VERSION_MISMATCH",
        "IND_DEPRECATED",
        "IND_UNSUPPORTED_OUT_OF_CORE",
        "IND_ACCELERATION_BACKEND_UNAVAILABLE",
        "IND_TIMEOUT",
        "IND_CANCELLED",
        "IND_PARTIAL_RESULT",
        "IND_UNSUPPORTED_INCREMENTAL_MODE",
        "IND_CUSTOM_INDICATOR_REJECTED",
        "IND_ACCESS_DENIED",
        "IND_PROPRIETARY_UNAUTHORIZED",
        "IND_SLO_VIOLATION",
        # Custom Strategy Codes
        "STRATEGY_INVALID_CONFIG",
        "STRATEGY_NOT_FOUND",
        "STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE",
        "STRATEGY_DEPRECATED",
        "STRATEGY_UNAPPROVED_MODULE",
        "STRATEGY_SCHEMA_VALIDATION_FAILED",
        "STRATEGY_UNSUPPORTED_TIMING_POLICY",
        "STRATEGY_LOOKAHEAD_DETECTED",
        "SIM_ARBITRARY_CODE_REJECTED",
        "STRATEGY_INTERNAL_ERROR",
        "STRATEGY_LIFECYCLE_NOT_APPROVED",
        "STRATEGY_ENVIRONMENT_NOT_PERMITTED",
        "STRATEGY_ARTIFACT_HASH_MISMATCH",
        "STRATEGY_DEPENDENCY_HASH_MISMATCH",
        "INDICATOR_MODULE_ERROR",
        "STRATEGY_CHECKPOINT_INVALID",
        "STRATEGY_CHECKPOINT_INCOMPATIBLE",
        "STRATEGY_DATA_NOT_READY",
        "STRATEGY_INDICATOR_NOT_READY",
        "STRATEGY_MISSING_REQUIRED_DATA",
        "STRATEGY_STALE_DATA",
        "STRATEGY_DUPLICATE_INTENT",
        "STRATEGY_RESOURCE_LIMIT_EXCEEDED",
        "STRATEGY_TIMEOUT",
        "STRATEGY_VALIDATION_ARTIFACT_REQUIRED",
        "STRATEGY_RISK_PROFILE_REQUIRED",
        "STRATEGY_CIRCUIT_BREAKER_TRIGGERED",
        "STRATEGY_POSITION_LIMIT_EXCEEDED",
        "STRATEGY_VOLUME_PARTICIPATION_EXCEEDED",
        "STRATEGY_DATA_QUALITY_GATE_FAILED",
        "STRATEGY_PERFORMANCE_DEGRADED",
        "STRATEGY_DRIFT_DETECTED",
        "STRATEGY_REGULATORY_LIMIT_BREACHED",
        "STRATEGY_MARKET_ACCESS_REVOKED",
        "STRATEGY_HARD_KILLED",
        # Custom Risk Codes
        "INVALID_PORTFOLIO_STATE",
        "INVALID_RISK_CONFIG",
        "MISSING_EVIDENCE",
        "STALE_EVIDENCE",
        "LIMIT_FAILED",
        "POLICY_BLOCKED",
        "APPROVAL_REQUIRED",
        "APPROVAL_TOKEN_INVALID",
        "APPROVAL_TOKEN_EXPIRED",
        "APPROVAL_TOKEN_REVOKED",
        "APPROVAL_TOKEN_CONSUMED",
        "CONFIG_VERSION_MISMATCH",
        "CONFIG_COMPATIBILITY_NOT_APPROVED",
        "PARAMETRIC_VAR_GAUSSIAN_WARNING",
        "PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED",
        "PAYLOAD_TOO_LARGE",
        "MISSING_STOP_LOSS",
        "INSUFFICIENT_VOLATILITY_EVIDENCE",
        "INSUFFICIENT_K_EVIDENCE",
        "LIVE_STATE_STALE",
        "IN_FLIGHT_TOLERANCE_EXCEEDED",
        "CALCULATION_FAILED",
        "SNAPSHOT_BUILD_FAILED",
        "REPORT_GENERATION_FAILED",
        "STORAGE_ERROR",
        # Custom Simulation Codes
        "SIM_ACCOUNT_INVARIANT_BROKEN",
        "SIM_CALIBRATION_REQUIRED",
        "SIM_CANARY_DIVERGENCE",
        "SIM_CHECKPOINT_INCOMPATIBLE",
        "SIM_COMMISSION_CALCULATION_FAILED",
        "SIM_CONCENTRATION_LIMIT_EXCEEDED",
        "SIM_CORRELATION_LIMIT_EXCEEDED",
        "SIM_DATA_DUPLICATE_TIMESTAMP",
        "SIM_DATA_EMPTY",
        "SIM_DATA_INVALID_OHLC",
        "SIM_DATA_MISSING_COLUMN",
        "SIM_DATA_NEGATIVE_SPREAD",
        "SIM_DATA_NON_MONOTONIC_TIME",
        "SIM_DATA_PARTIAL",
        "SIM_DATA_PRICE_OUTLIER",
        "SIM_DATA_QUALITY_FAILED",
        "SIM_DATA_STALE",
        "SIM_ENVIRONMENT_DRIFT_WARNING",
        "SIM_EVENT_PRIORITY_CONFLICT",
        "SIM_FEATURE_LOOKAHEAD_DETECTED",
        "SIM_FREEZE_LEVEL_VIOLATION",
        "SIM_FX_CROSS_RATE_REJECTED",
        "SIM_FX_RATE_STALE",
        "SIM_GAP_HANDLING_REJECTED",
        "SIM_INSUFFICIENT_MARGIN",
        "SIM_INTERNAL_ERROR",
        "SIM_INVALID_CONFIG",
        "SIM_INVALID_DATE_RANGE",
        "SIM_INVALID_PRICE",
        "SIM_INVALID_STOPS_LEVEL",
        "SIM_INVALID_VOLUME",
        "SIM_IOC_REMAINDER_CANCELLED",
        "SIM_KILL_SWITCH_TRIGGERED",
        "SIM_LIMIT_QUEUE_NOT_FILLED",
        "SIM_LIQUIDITY_UNAVAILABLE",
        "SIM_LOOKAHEAD_DETECTED",
        "SIM_MARKET_CLOSED",
        "SIM_MARKET_HALT_ACTIVE",
        "SIM_MISSING_SYMBOL",
        "SIM_MODEL_GOVERNANCE_EXPIRED",
        "SIM_MONTE_CARLO_FAILED",
        "SIM_OPTIMIZATION_FAILED",
        "SIM_OPTIONAL_SERVICE_DEGRADED",
        "SIM_ORDER_NOT_FOUND",
        "SIM_PARTIAL_FILL_REMAINDER",
        "SIM_PENDING_ORDER_EXPIRED",
        "SIM_PERFORMANCE_GATE_FAILED",
        "SIM_PERSISTENCE_FAILED",
        "SIM_POISON_WORK_UNIT_QUARANTINED",
        "SIM_PORTFOLIO_RISK_REJECTED",
        "SIM_POSITION_NOT_FOUND",
        "SIM_PROMOTION_EVIDENCE_MISSING",
        "SIM_QUEUE_LIMIT_EXCEEDED",
        "SIM_RESEARCH_PROTOCOL_MISSING",
        "SIM_RESOURCE_QUOTA_EXCEEDED",
        "SIM_RUN_ID_CONFLICT",
        "SIM_SIZING_FAILED",
        "SIM_SIZING_INVALID_ATR",
        "SIM_SIZING_INVALID_KELLY_INPUTS",
        "SIM_SIZING_REQUIRES_STOP_LOSS",
        "SIM_SLIPPAGE_EXCEEDED",
        "SIM_SPREAD_MISSING",
        "SIM_SWAP_CALCULATION_FAILED",
        "SIM_SYNTHETIC_TICK_GENERATION_FAILED",
        "SIM_UNSUPPORTED_COMMISSION_MODEL",
        "SIM_UNSUPPORTED_FILL_POLICY",
        "SIM_UNSUPPORTED_LIQUIDITY_MODEL",
        "SIM_UNSUPPORTED_SLIPPAGE_MODEL",
        "SIM_UNSUPPORTED_SPREAD_MODEL",
        "SIM_UNSUPPORTED_SWAP_MODEL",
        "SIM_UNSUPPORTED_TICK_MODEL",
        "SIM_VENDOR_DATA_POLICY_VIOLATION",
        "SIM_VOLUME_ABOVE_MAX",
        "SIM_VOLUME_BELOW_MIN",
        "SIM_VOLUME_STEP_MISMATCH",
        "SIM_WORKER_LOST_REQUEUED",
        # Custom Live Runtime Codes
        "LIVE_DISABLED",
        "LIVE_GATE_FAILED",
        "LIVE_POLICY_UNDEFINED",
        "LIVE_APPROVAL_REQUIRED",
        "LIVE_KILL_SWITCH_ACTIVE",
        "LIVE_STALE_CONTEXT",
        "LIVE_RECONCILIATION_REQUIRED",
        "LIVE_UNKNOWN_OUTCOME",
        "LIVE_IDEMPOTENCY_CONFLICT",
        "LIVE_SESSION_INACTIVE",
        "LIVE_BROKER_READINESS_FAILED",
        "LIVE_AUDIT_WRITE_FAILED",
        "LIVE_COST_BUDGET_EXCEEDED",
        "WORKFLOW_TIMEOUT",
        "RETRY_AFTER_RECONCILIATION",
    }
)

ERROR_MESSAGES: dict[str, str] = {
    "INVALID_INPUT": "The request input is invalid.",
    "PERMISSION_DENIED": "The request is not permitted.",
    "DATA_NOT_FOUND": "The requested data was not found.",
    "EMPTY_RESULT": "The request completed but returned no results.",
    "SERVICE_UNAVAILABLE": "The required service is unavailable.",
    "BROKER_UNAVAILABLE": "The broker service is unavailable.",
    "DATABASE_ERROR": "A database operation failed.",
    "NETWORK_ERROR": "A network operation failed.",
    "TIMEOUT": "The operation timed out.",
    "VALIDATION_FAILED": "Response validation failed.",
    "CONFIGURATION_ERROR": "A configuration error occurred.",
    "TOOL_EXECUTION_FAILED": "The tool failed during execution.",
    "UNKNOWN_ERROR": "An unknown error occurred.",
    "INVALID_AUTH_CONTEXT": "The authentication context is invalid.",
    "AUTHORIZATION_FAILED": "Authorization failed.",
    "INVALID_EVENT": "The event payload is invalid.",
    "EVENT_PUBLISH_FAILED": "The event could not be published.",
    "EVENT_HANDLER_FAILED": "The event handler failed.",
    "EVENT_DEAD_LETTER_FAILED": "The event could not be dead-lettered.",
    "QUEUE_FULL": "The queue is full.",
    "BACKPRESSURE_EXCEEDED": "Backpressure limits were exceeded.",
    "NOTIFICATION_FAILED": "Notification delivery failed.",
    "NOTIFICATION_SUPPRESSED": "Notification delivery was suppressed.",
    "NOTIFICATION_THROTTLED": "Notification delivery was throttled.",
    "OBSERVABILITY_ERROR": "An observability operation failed.",
    "METRICS_EXPORT_FAILED": "Metrics export failed.",
    "CLOCK_DRIFT_DETECTED": "Clock drift was detected.",
    "CIRCUIT_OPEN": "The circuit is open and the operation was blocked.",
    "SECRET_VERSION_NOT_FOUND": "No active secret version was found.",  # pragma: allowlist secret
    "SECRET_VERSION_CONFLICT": "Secret conflict detected.",  # pragma: allowlist secret
    "DATA_DROPPED": "Data record was dropped due to buffer overflow or constraints.",
    "CIRCUIT_BREAKER_OPEN": "Circuit breaker is open for the source.",
    "AUTHENTICATION_FAILED": "Authentication failed for the data source.",
    "MISSING_ASSET_METADATA": "Asset/symbol metadata is missing.",
    "DB_CONNECTION_ERROR": "Database connection failed.",
    "DB_WRITE_FAILED": "Failed to write data to database.",
    "STATE_RECOVERY_FAILED": "Failed to recover scheduler/feed state.",
    "CHECKPOINT_CORRUPTED": "Job checkpoint is corrupted or invalid.",
    "CREDENTIALS_MISSING": "Credentials are missing for the source.",
    "BUFFER_OVERFLOW": "Feed buffer has overflowed.",
    "FEED_HEARTBEAT_TIMEOUT": "Feed heartbeat timeout detected.",
    "FEED_RECONCILIATION_FAILED": "Feed gap reconciliation failed.",
    "JOB_NOT_FOUND": "Scheduler job was not found.",
    "SCHEDULER_ERROR": "A scheduler/job error occurred.",
    "LICENSE_RESTRICTION": "Access denied due to license restrictions.",
    "UNSUPPORTED_OPERATION": "The requested operation is unsupported.",
    # Custom Indicator Messages
    "IND_INVALID_CONFIG": "Indicator configuration combination checks failed.",
    "IND_INVALID_PARAMETER": "Formula parameter checks failed.",
    "IND_UNSUPPORTED_INDICATOR": "An unrecognized indicator ID is requested.",
    "IND_UNSUPPORTED_TIMEFRAME": "Timeframe is invalid or missing.",
    "IND_UNSUPPORTED_DTYPE": "Inputs contain unsupported float or integer precision.",
    "IND_INVALID_INPUT_SCHEMA": "DataFrame structure or column types failed validation.",
    "IND_MISSING_REQUIRED_COLUMN": "Required columns are missing.",
    "IND_INVALID_OUTPUT_COLUMN": "Output column naming is malformed or invalid.",
    "IND_OUTPUT_COLUMN_CONFLICT": "Output column names conflict with input columns.",
    "IND_INVALID_OUTPUT_MODE": "Output modes are mutually exclusive or invalid.",
    "IND_INPUT_MUTATION_DETECTED": "Indicator calculations modified input data in place.",
    "IND_DUPLICATE_TIMESTAMP": "Duplicate timestamps found in symbol dataset.",
    "IND_NON_MONOTONIC_TIME": "Timestamps are not strictly ascending.",
    "IND_AMBIGUOUS_TIMESTAMP": "Naive local time transitions made timestamps ambiguous.",
    "IND_INVALID_TIMEZONE": "Naive local timezone calculations rejected.",
    "IND_INVALID_OHLC": "Prices violate physical boundaries.",
    "IND_INSUFFICIENT_DATA": "Input row count is lower than indicator warmup requirements.",
    "IND_LOOKAHEAD_RISK": "Strategy attempted to consume data before it closed.",
    "IND_UNKNOWN_ADJUSTMENT_STATUS": "Adjustment status of input prices is unknown.",
    "IND_STATE_INCOMPATIBLE": "State serialization does not match current specifications.",
    "IND_STATE_CORRUPTED": "State payload cannot be parsed.",
    "IND_RESOURCE_LIMIT_EXCEEDED": "Calculations exceeded memory budget or time limit.",
    "IND_INTRA_BAR_ADJUSTMENT_UNSUPPORTED": "Intra-bar adjustments are unsupported.",
    "IND_SYMBOL_MAPPING_REQUIRED": "Symbol mapping contract is required but missing.",
    "IND_STUB_QUOTE_REJECTED": "Bid/ask values represent stub quotes and are rejected.",
    "IND_INVERTED_MARKET": "Ask is less than bid.",
    "IND_SPREAD_THRESHOLD_EXCEEDED": "Bid/ask spread exceeds threshold.",
    "IND_FORMULA_VERSION_MISMATCH": "Calculation used incompatible formula versions.",
    "IND_DEPRECATED": "Deprecated indicator requested under strict deprecation phase.",
    "IND_UNSUPPORTED_OUT_OF_CORE": "Out-of-core calculations are unsupported.",
    "IND_ACCELERATION_BACKEND_UNAVAILABLE": "Acceleration backend is unavailable.",
    "IND_TIMEOUT": "Indicator calculation timed out.",
    "IND_CANCELLED": "Indicator calculation was cancelled.",
    "IND_PARTIAL_RESULT": "Partial result returned in strict modes.",
    "IND_UNSUPPORTED_INCREMENTAL_MODE": "Incremental calculation mode not supported.",
    "IND_CUSTOM_INDICATOR_REJECTED": "Conformance or side-effect checks rejected indicator.",
    "IND_ACCESS_DENIED": "Actor lacks basic access to indicator services.",
    "IND_PROPRIETARY_UNAUTHORIZED": "Access control blocked proprietary indicator.",
    "IND_SLO_VIOLATION": "SLO monitoring policy triggered synchronous rejection.",
    # Custom Strategy Messages
    "STRATEGY_INVALID_CONFIG": "Strategy configuration failed schema validation.",
    "STRATEGY_NOT_FOUND": "Unrecognized strategy ID requested.",
    "STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE": "No matching version fits the constraint.",
    "STRATEGY_DEPRECATED": "Strategy is deprecated and cannot be run.",
    "STRATEGY_UNAPPROVED_MODULE": "Module resolution pointed to an unapproved file path.",
    "STRATEGY_SCHEMA_VALIDATION_FAILED": "Config JSON schema failed validation.",
    "STRATEGY_UNSUPPORTED_TIMING_POLICY": "Timing policy is unsupported.",
    "STRATEGY_LOOKAHEAD_DETECTED": "Lookahead risk or future data access detected.",
    "SIM_ARBITRARY_CODE_REJECTED": "Arbitrary user Python code execution rejected.",
    "STRATEGY_INTERNAL_ERROR": "Internal strategy computations failed.",
    "STRATEGY_LIFECYCLE_NOT_APPROVED": "Strategy environment exceeds lifecycle approval state.",
    "STRATEGY_ENVIRONMENT_NOT_PERMITTED": "Target environment not declared in registry.",
    "STRATEGY_ARTIFACT_HASH_MISMATCH": "Package artifact hash does not match registry.",
    "STRATEGY_DEPENDENCY_HASH_MISMATCH": "Lockfile hash mismatch detected.",
    "INDICATOR_MODULE_ERROR": "Underlying indicator module call failed.",
    "STRATEGY_CHECKPOINT_INVALID": "Checkpoint data shape is invalid.",
    "STRATEGY_CHECKPOINT_INCOMPATIBLE": "Restored checkpoint settings mismatch.",
    "STRATEGY_DATA_NOT_READY": "Input data is missing or not ready.",
    "STRATEGY_INDICATOR_NOT_READY": "Required indicators are warmup incomplete.",
    "STRATEGY_MISSING_REQUIRED_DATA": "Data query yielded missing fields.",
    "STRATEGY_STALE_DATA": "Data arrival exceeded latency threshold.",
    "STRATEGY_DUPLICATE_INTENT": "Idempotency or sequence keys collided.",
    "STRATEGY_RESOURCE_LIMIT_EXCEEDED": "CPU time or memory allocations exceeded limit.",
    "STRATEGY_TIMEOUT": "Strategy hook timing exceeded budget limit.",
    "STRATEGY_VALIDATION_ARTIFACT_REQUIRED": "Promotion failed due to missing evidence.",
    "STRATEGY_RISK_PROFILE_REQUIRED": "Strategy registry has no declared risk profile.",
    "STRATEGY_CIRCUIT_BREAKER_TRIGGERED": "Circuit breaker stopped intent generation.",
    "STRATEGY_POSITION_LIMIT_EXCEEDED": "Intent exceeded local position sizing caps.",
    "STRATEGY_VOLUME_PARTICIPATION_EXCEEDED": "Volume size exceeded visible participation limit.",
    "STRATEGY_DATA_QUALITY_GATE_FAILED": "Timezone normalization or gaps rejected tick inputs.",
    "STRATEGY_PERFORMANCE_DEGRADED": "Analytics flagged degraded returns.",
    "STRATEGY_DRIFT_DETECTED": "Model inputs drifted statistical limits.",
    "STRATEGY_REGULATORY_LIMIT_BREACHED": "Local validation hit regulatory caps.",
    "STRATEGY_MARKET_ACCESS_REVOKED": "Broker reported login or venue suspension.",
    "STRATEGY_HARD_KILLED": "Emergency hard kill signal received.",
    # Custom Risk Messages
    "INVALID_PORTFOLIO_STATE": "Portfolio state validation failed.",
    "INVALID_RISK_CONFIG": "Risk configuration validation failed.",
    "MISSING_EVIDENCE": "Required evidence is missing.",
    "STALE_EVIDENCE": "Required evidence is stale.",
    "LIMIT_FAILED": "Risk limit check failed.",
    "POLICY_BLOCKED": "Action is blocked by risk policy.",
    "APPROVAL_REQUIRED": "Action requires an approval token.",
    "APPROVAL_TOKEN_INVALID": "Approval token is invalid.",
    "APPROVAL_TOKEN_EXPIRED": "Approval token is expired.",
    "APPROVAL_TOKEN_REVOKED": "Approval token has been revoked.",
    "APPROVAL_TOKEN_CONSUMED": "Approval token has already been consumed.",
    "CONFIG_VERSION_MISMATCH": "Stored config version or hash mismatch.",
    "CONFIG_COMPATIBILITY_NOT_APPROVED": "Config hash compatibility was not approved.",
    "PARAMETRIC_VAR_GAUSSIAN_WARNING": "Parametric VaR calculation used Gaussian assumption.",
    "PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED": "Pre-trade request blocked due to potential double spend.",
    "PAYLOAD_TOO_LARGE": "Payload exceeds maximum allowed size or nesting depth.",
    "MISSING_STOP_LOSS": "Required stop loss is missing.",
    "INSUFFICIENT_VOLATILITY_EVIDENCE": "Insufficient ATR or volatility evidence.",
    "INSUFFICIENT_K_EVIDENCE": "Insufficient trade samples for Kelly sizing.",
    "LIVE_STATE_STALE": "Live portfolio state freshness checks failed.",
    "IN_FLIGHT_TOLERANCE_EXCEEDED": "In-flight order reconciliation tolerance exceeded.",
    "CALCULATION_FAILED": "A specific risk calculation failed.",
    "SNAPSHOT_BUILD_FAILED": "Building portfolio risk snapshot failed.",
    "REPORT_GENERATION_FAILED": "Risk report generation failed.",
    "STORAGE_ERROR": "Risk audit storage or token state persistence failed.",
    # Custom Simulation Messages
    "SIM_ACCOUNT_INVARIANT_BROKEN": "Account invariant broken.",
    "SIM_CALIBRATION_REQUIRED": "Calibration required.",
    "SIM_CANARY_DIVERGENCE": "Canary divergence.",
    "SIM_CHECKPOINT_INCOMPATIBLE": "Checkpoint incompatible.",
    "SIM_COMMISSION_CALCULATION_FAILED": "Commission calculation failed.",
    "SIM_CONCENTRATION_LIMIT_EXCEEDED": "Concentration limit exceeded.",
    "SIM_CORRELATION_LIMIT_EXCEEDED": "Correlation limit exceeded.",
    "SIM_DATA_DUPLICATE_TIMESTAMP": "Data duplicate timestamp.",
    "SIM_DATA_EMPTY": "Data empty.",
    "SIM_DATA_INVALID_OHLC": "Data invalid ohlc.",
    "SIM_DATA_MISSING_COLUMN": "Data missing column.",
    "SIM_DATA_NEGATIVE_SPREAD": "Data negative spread.",
    "SIM_DATA_NON_MONOTONIC_TIME": "Data non monotonic time.",
    "SIM_DATA_PARTIAL": "Data partial.",
    "SIM_DATA_PRICE_OUTLIER": "Data price outlier.",
    "SIM_DATA_QUALITY_FAILED": "Data quality failed.",
    "SIM_DATA_STALE": "Data stale.",
    "SIM_ENVIRONMENT_DRIFT_WARNING": "Environment drift warning.",
    "SIM_EVENT_PRIORITY_CONFLICT": "Event priority conflict.",
    "SIM_FEATURE_LOOKAHEAD_DETECTED": "Feature lookahead detected.",
    "SIM_FREEZE_LEVEL_VIOLATION": "Freeze level violation.",
    "SIM_FX_CROSS_RATE_REJECTED": "Fx cross rate rejected.",
    "SIM_FX_RATE_STALE": "Fx rate stale.",
    "SIM_GAP_HANDLING_REJECTED": "Gap handling rejected.",
    "SIM_INSUFFICIENT_MARGIN": "Insufficient margin.",
    "SIM_INTERNAL_ERROR": "Internal error.",
    "SIM_INVALID_CONFIG": "Invalid config.",
    "SIM_INVALID_DATE_RANGE": "Invalid date range.",
    "SIM_INVALID_PRICE": "Invalid price.",
    "SIM_INVALID_STOPS_LEVEL": "Invalid stops level.",
    "SIM_INVALID_VOLUME": "Invalid volume.",
    "SIM_IOC_REMAINDER_CANCELLED": "Ioc remainder cancelled.",
    "SIM_KILL_SWITCH_TRIGGERED": "Kill switch triggered.",
    "SIM_LIMIT_QUEUE_NOT_FILLED": "Limit queue not filled.",
    "SIM_LIQUIDITY_UNAVAILABLE": "Liquidity unavailable.",
    "SIM_LOOKAHEAD_DETECTED": "Lookahead detected.",
    "SIM_MARKET_CLOSED": "Market closed.",
    "SIM_MARKET_HALT_ACTIVE": "Market halt active.",
    "SIM_MISSING_SYMBOL": "Missing symbol.",
    "SIM_MODEL_GOVERNANCE_EXPIRED": "Model governance expired.",
    "SIM_MONTE_CARLO_FAILED": "Monte carlo failed.",
    "SIM_OPTIMIZATION_FAILED": "Optimization failed.",
    "SIM_OPTIONAL_SERVICE_DEGRADED": "Optional service degraded.",
    "SIM_ORDER_NOT_FOUND": "Order not found.",
    "SIM_PARTIAL_FILL_REMAINDER": "Partial fill remainder.",
    "SIM_PENDING_ORDER_EXPIRED": "Pending order expired.",
    "SIM_PERFORMANCE_GATE_FAILED": "Performance gate failed.",
    "SIM_PERSISTENCE_FAILED": "Persistence failed.",
    "SIM_POISON_WORK_UNIT_QUARANTINED": "Poison work unit quarantined.",
    "SIM_PORTFOLIO_RISK_REJECTED": "Portfolio risk rejected.",
    "SIM_POSITION_NOT_FOUND": "Position not found.",
    "SIM_PROMOTION_EVIDENCE_MISSING": "Promotion evidence missing.",
    "SIM_QUEUE_LIMIT_EXCEEDED": "Queue limit exceeded.",
    "SIM_RESEARCH_PROTOCOL_MISSING": "Research protocol missing.",
    "SIM_RESOURCE_QUOTA_EXCEEDED": "Resource quota exceeded.",
    "SIM_RUN_ID_CONFLICT": "Run id conflict.",
    "SIM_SIZING_FAILED": "Sizing failed.",
    "SIM_SIZING_INVALID_ATR": "Sizing invalid atr.",
    "SIM_SIZING_INVALID_KELLY_INPUTS": "Sizing invalid kelly inputs.",
    "SIM_SIZING_REQUIRES_STOP_LOSS": "Sizing requires stop loss.",
    "SIM_SLIPPAGE_EXCEEDED": "Slippage exceeded.",
    "SIM_SPREAD_MISSING": "Spread missing.",
    "SIM_SWAP_CALCULATION_FAILED": "Swap calculation failed.",
    "SIM_SYNTHETIC_TICK_GENERATION_FAILED": "Synthetic tick generation failed.",
    "SIM_UNSUPPORTED_COMMISSION_MODEL": "Unsupported commission model.",
    "SIM_UNSUPPORTED_FILL_POLICY": "Unsupported fill policy.",
    "SIM_UNSUPPORTED_LIQUIDITY_MODEL": "Unsupported liquidity model.",
    "SIM_UNSUPPORTED_SLIPPAGE_MODEL": "Unsupported slippage model.",
    "SIM_UNSUPPORTED_SPREAD_MODEL": "Unsupported spread model.",
    "SIM_UNSUPPORTED_SWAP_MODEL": "Unsupported swap model.",
    "SIM_UNSUPPORTED_TICK_MODEL": "Unsupported tick model.",
    "SIM_VENDOR_DATA_POLICY_VIOLATION": "Vendor data policy violation.",
    "SIM_VOLUME_ABOVE_MAX": "Volume above max.",
    "SIM_VOLUME_BELOW_MIN": "Volume below min.",
    "SIM_VOLUME_STEP_MISMATCH": "Volume step mismatch.",
    "SIM_WORKER_LOST_REQUEUED": "Worker lost requeued.",
    # Custom Live Runtime Messages
    "LIVE_DISABLED": "Live trading is disabled. Enable live mode in configuration.",
    "LIVE_GATE_FAILED": "A mandatory live gate failed; the action is blocked.",
    "LIVE_POLICY_UNDEFINED": "No live action policy entry exists for the requested action.",
    "LIVE_APPROVAL_REQUIRED": "Explicit approval context is required for this live action.",
    "LIVE_KILL_SWITCH_ACTIVE": "Active kill switch blocks all live trading requests.",
    "LIVE_STALE_CONTEXT": "Live context is stale and cannot be used for broker mutation.",
    "LIVE_RECONCILIATION_REQUIRED": "Broker reconciliation must complete before live mutation.",
    "LIVE_UNKNOWN_OUTCOME": "The broker outcome is unknown; reconciliation required.",
    "LIVE_IDEMPOTENCY_CONFLICT": "A duplicate idempotency key was detected for a different request.",
    "LIVE_SESSION_INACTIVE": "No active live session; start a session before trading.",
    "LIVE_BROKER_READINESS_FAILED": "Broker readiness check failed; live mutation is blocked.",
    "LIVE_AUDIT_WRITE_FAILED": "Audit pre-event write failed; broker mutation is blocked.",
    "LIVE_COST_BUDGET_EXCEEDED": "Live cost budget exceeded; broker mutation is blocked.",
    "WORKFLOW_TIMEOUT": "Live workflow exceeded configured timeout limit.",
    "RETRY_AFTER_RECONCILIATION": "Retry is not safe until broker reconciliation resolves the outcome.",
}


class ErrorPayload(TypedDict):
    """Structured error payload used by standard error envelopes."""

    code: str
    details: str


class Error(Exception):
    """Base deterministic utility error with a stable error code.

    Use this for support helpers that need to raise typed HaruQuant exceptions
    while remaining safely mappable at official tool boundaries.

    Args:
        message: Human-readable error details.
        code: Optional approved deterministic error code.

    Raises:
        ValidationError: If an explicit code is not approved.
    """

    code = "UNKNOWN_ERROR"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        """Initialize the error with deterministic message and code."""
        super().__init__(message)
        if code is not None:
            self.code = normalize_error_code(code)


class ValidationError(Error):
    """Input, payload, or output validation failure."""

    code = "VALIDATION_FAILED"


class ConfigurationError(Error):
    """Invalid or missing runtime configuration."""

    code = "SERVICE_UNAVAILABLE"


class SecurityError(Error):
    """Permission, authorization, or redaction failure."""

    code = "PERMISSION_DENIED"


class DataError(Error):
    """Data lookup, shape, or availability failure."""

    code = "DATA_NOT_FOUND"


class ExternalServiceError(Error):
    """External service, network, broker, or timeout failure."""

    code = "SERVICE_UNAVAILABLE"


class TradingError(ExternalServiceError):
    """Base error for deterministic trading execution failures."""

    code = "BROKER_UNAVAILABLE"


class TradingTimeoutError(TradingError):
    """Raised when broker execution exceeds the configured timeout."""

    code = "TIMEOUT"


class UnknownOutcomeError(TradingError):
    """Raised when broker execution outcome cannot be determined safely."""

    code = "CIRCUIT_OPEN"


TRADING_RETCODE_ERROR_MAP: dict[int, str] = {
    10004: "TIMEOUT",  # TRADE_RETCODE_REQUOTE
    10006: "BROKER_UNAVAILABLE",  # TRADE_RETCODE_REJECT
    10014: "VALIDATION_FAILED",  # TRADE_RETCODE_INVALID_VOLUME
    10015: "VALIDATION_FAILED",  # TRADE_RETCODE_INVALID_PRICE
    10016: "VALIDATION_FAILED",  # TRADE_RETCODE_INVALID_STOPS
    10017: "CIRCUIT_OPEN",  # TRADE_RETCODE_TRADE_DISABLED / freeze-like block
    10019: "VALIDATION_FAILED",  # TRADE_RETCODE_NO_MONEY
    10031: "DATA_NOT_FOUND",  # order not found in simulator compatibility layer
    10032: "DATA_NOT_FOUND",  # position not found in simulator compatibility layer
}

TRANSIENT_TRADING_RETCODES = frozenset({10004, 10005, 10006, 10012, 10020, 10021})


def classify_broker_error(raw_error: Exception | object) -> dict[str, object]:
    """Classify broker errors into deterministic internal error metadata.

    Args:
        raw_error: Exception or broker response object with an optional
            ``retcode`` attribute.

    Returns:
        A mapping containing ``code``, ``classification``, ``retcode``, and
        redacted ``details``.
    """
    retcode = getattr(raw_error, "retcode", None)
    if isinstance(raw_error, Mapping):
        retcode = raw_error.get("retcode", retcode)
    try:
        normalized_retcode = int(retcode) if retcode is not None else None
    except (TypeError, ValueError):
        normalized_retcode = None

    code = "UNKNOWN_ERROR"
    if normalized_retcode is not None:
        if normalized_retcode in TRADING_RETCODE_ERROR_MAP:
            code = TRADING_RETCODE_ERROR_MAP[normalized_retcode]
    elif isinstance(raw_error, BaseException):
        code = code_for_exception(raw_error)

    classification = (
        "transient"
        if normalized_retcode in TRANSIENT_TRADING_RETCODES
        or code in {"TIMEOUT", "NETWORK_ERROR", "BROKER_UNAVAILABLE"}
        else "permanent"
    )
    return {
        "code": normalize_error_code(code),
        "classification": classification,
        "retcode": normalized_retcode,
        "details": redact_text(str(raw_error)),
    }


def trading_retry_delay(
    attempt: int,
    *,
    base_seconds: float = 0.25,
    max_seconds: float = 5.0,
    jitter_ratio: float = 0.2,
) -> float:
    """Compute exponential backoff with randomized jitter for idempotent retries.

    Args:
        attempt: Zero-based retry attempt number.
        base_seconds: Initial delay before exponential growth.
        max_seconds: Maximum returned delay.
        jitter_ratio: Fractional jitter applied to the capped delay.

    Returns:
        Delay in seconds.

    Raises:
        ValidationError: If retry parameters are invalid.
    """
    if attempt < 0:
        raise ValidationError("attempt must be non-negative.")
    if base_seconds <= 0.0 or max_seconds <= 0.0:
        raise ValidationError("retry delays must be positive.")
    if jitter_ratio < 0.0:
        raise ValidationError("jitter_ratio must be non-negative.")

    delay_val = base_seconds * (2**attempt)
    delay = float(max_seconds) if delay_val > max_seconds else float(delay_val)
    jitter = float(delay * jitter_ratio * random())
    total_delay = delay + jitter
    return float(max_seconds) if total_delay > max_seconds else float(total_delay)


# --- Indicators Domain Errors ---
class IndicatorError(ValidationError):
    """Base error type for all indicator calculations and registry operations.

    Ensures that custom IND_ error codes are retained on the exception object.
    """

    code = "VALIDATION_FAILED"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        """Initialize with message and optional custom code."""
        super().__init__(message)
        self.code = code if code is not None else self.__class__.code


class IndicatorConfigError(IndicatorError):
    """Raised when configuration combination checks fail."""

    code = "IND_INVALID_CONFIG"


class IndicatorParameterError(IndicatorError):
    """Raised when formula parameter checks fail (e.g. period <= 0)."""

    code = "IND_INVALID_PARAMETER"


class UnsupportedIndicatorError(IndicatorError):
    """Raised when an unrecognized indicator ID is requested."""

    code = "IND_UNSUPPORTED_INDICATOR"


class UnsupportedTimeframeError(IndicatorError):
    """Raised when timeframe is invalid or missing."""

    code = "IND_UNSUPPORTED_TIMEFRAME"


class UnsupportedDtypeError(IndicatorError):
    """Raised when inputs contain unsupported float or integer precision."""

    code = "IND_UNSUPPORTED_DTYPE"


class InvalidInputSchemaError(IndicatorError):
    """Raised when DataFrame structure or column types fail validation."""

    code = "IND_INVALID_INPUT_SCHEMA"


class MissingRequiredColumnError(IndicatorError):
    """Raised when required columns (e.g. 'close') are missing."""

    code = "IND_MISSING_REQUIRED_COLUMN"


class InvalidOutputColumnError(IndicatorError):
    """Raised when output column naming is malformed or invalid."""

    code = "IND_INVALID_OUTPUT_COLUMN"


class OutputColumnConflictError(IndicatorError):
    """Raised when output column names conflict with input columns."""

    code = "IND_OUTPUT_COLUMN_CONFLICT"


class InvalidOutputModeError(IndicatorError):
    """Raised when output modes are mutually exclusive or invalid."""

    code = "IND_INVALID_OUTPUT_MODE"


class InputMutationError(IndicatorError):
    """Raised when indicator calculations modify input data in place."""

    code = "IND_INPUT_MUTATION_DETECTED"


class DuplicateTimestampError(IndicatorError):
    """Raised when duplicate timestamps are found in a single symbol dataset."""

    code = "IND_DUPLICATE_TIMESTAMP"


class NonMonotonicTimeError(IndicatorError):
    """Raised when timestamps are not strictly ascending."""

    code = "IND_NON_MONOTONIC_TIME"


class AmbiguousTimestampError(IndicatorError):
    """Raised when naive local time transitions make timestamps ambiguous."""

    code = "IND_AMBIGUOUS_TIMESTAMP"


class InvalidTimezoneError(IndicatorError):
    """Raised when naive local timezone calculations are rejected."""

    code = "IND_INVALID_TIMEZONE"


class InvalidOHLCError(IndicatorError):
    """Raised when prices violate physical boundaries (e.g. low > high)."""

    code = "IND_INVALID_OHLC"


class InsufficientDataError(IndicatorError):
    """Raised when input row count is lower than indicator warmup requirements."""

    code = "IND_INSUFFICIENT_DATA"


class LookaheadRiskError(IndicatorError):
    """Raised when strategy attempts to consume data before it is closed/available."""

    code = "IND_LOOKAHEAD_RISK"


class UnknownAdjustmentStatusError(IndicatorError):
    """Raised when adjustment status of input prices is unknown."""

    code = "IND_UNKNOWN_ADJUSTMENT_STATUS"


class StateIncompatibleError(IndicatorError):
    """Raised when state serialization does not match current specifications."""

    code = "IND_STATE_INCOMPATIBLE"


class StateCorruptedError(IndicatorError):
    """Raised when state payload cannot be parsed."""

    code = "IND_STATE_CORRUPTED"


class ResourceLimitExceededError(IndicatorError):
    """Raised when calculations exceed memory budget or time limit."""

    code = "IND_RESOURCE_LIMIT_EXCEEDED"


class UnsupportedIntraBarAdjustmentError(IndicatorError):
    """Raised when intra-bar corporate-action adjustments are unsupported."""

    code = "IND_INTRA_BAR_ADJUSTMENT_UNSUPPORTED"


class SymbolMappingRequiredError(IndicatorError):
    """Raised when symbol mapping contract is required but missing."""

    code = "IND_SYMBOL_MAPPING_REQUIRED"


class StubQuoteRejectedError(IndicatorError):
    """Raised when bid/ask values represent stub quotes and are rejected."""

    code = "IND_STUB_QUOTE_REJECTED"


class InvertedMarketError(IndicatorError):
    """Raised when ask is less than bid."""

    code = "IND_INVERTED_MARKET"


class SpreadThresholdExceededError(IndicatorError):
    """Raised when bid/ask spread exceeds the configured threshold."""

    code = "IND_SPREAD_THRESHOLD_EXCEEDED"


class FormulaVersionMismatchError(IndicatorError):
    """Raised when calculation uses incompatible formula versions."""

    code = "IND_FORMULA_VERSION_MISMATCH"


class DeprecatedIndicatorError(IndicatorError):
    """Raised when a deprecated indicator is requested under strict deprecation phase."""

    code = "IND_DEPRECATED"


class UnsupportedOutOfCoreError(IndicatorError):
    """Raised when indicator requires full context and out-of-core is unsupported."""

    code = "IND_UNSUPPORTED_OUT_OF_CORE"


class AccelerationBackendUnavailableError(IndicatorError):
    """Raised when requested acceleration backend is not available."""

    code = "IND_ACCELERATION_BACKEND_UNAVAILABLE"


class IndicatorTimeoutError(IndicatorError):
    """Raised when calculation times out."""

    code = "IND_TIMEOUT"


class CalculationCancelledError(IndicatorError):
    """Raised when calculation is cancelled before completion."""

    code = "IND_CANCELLED"


class PartialResultError(IndicatorError):
    """Raised when only a partial result is returned in strict modes."""

    code = "IND_PARTIAL_RESULT"


class UnsupportedIncrementalModeError(IndicatorError):
    """Raised when incremental calculation mode is not supported by the indicator."""

    code = "IND_UNSUPPORTED_INCREMENTAL_MODE"


class CustomIndicatorRejectedError(IndicatorError):
    """Raised when conformance or side-effect checks reject custom indicators."""

    code = "IND_CUSTOM_INDICATOR_REJECTED"


class AccessDeniedError(IndicatorError):
    """Raised when actor/workflow lacks basic access to indicator services."""

    code = "IND_ACCESS_DENIED"


class ProprietaryUnauthorizedError(IndicatorError):
    """Raised when access control blocks proprietary/licensed indicators."""

    code = "IND_PROPRIETARY_UNAUTHORIZED"


class SLOViolationError(IndicatorError):
    """Raised when SLO monitoring policy triggers synchronous rejection."""

    code = "IND_SLO_VIOLATION"


# --- Strategies Domain Errors ---


class StrategyError(ValidationError):
    """Base error type for all strategy calculations and registry operations.

    Ensures that custom STRATEGY_ error codes are retained on the exception object.
    """

    code = "VALIDATION_FAILED"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        """Initialize with message and optional custom code."""
        super().__init__(message)
        self.code = code if code is not None else self.__class__.code


class StrategyConfigError(StrategyError):
    """Raised when strategy configuration fails schema validation."""

    code = "STRATEGY_INVALID_CONFIG"


class StrategyNotFoundError(StrategyError):
    """Raised when an unrecognized strategy ID is requested."""

    code = "STRATEGY_NOT_FOUND"


class StrategyVersionConstraintUnsatisfiableError(StrategyError):
    """Raised when no matching version fits the constraint."""

    code = "STRATEGY_VERSION_CONSTRAINT_UNSATISFIABLE"


class StrategyDeprecatedError(StrategyError):
    """Raised when strategy is deprecated and cannot be run."""

    code = "STRATEGY_DEPRECATED"


class StrategyUnapprovedModuleError(StrategyError):
    """Raised when module resolution points to an unapproved file path."""

    code = "STRATEGY_UNAPPROVED_MODULE"


class StrategySchemaValidationFailedError(StrategyError):
    """Raised when config JSON schema fails validation."""

    code = "STRATEGY_SCHEMA_VALIDATION_FAILED"


class StrategyUnsupportedTimingPolicyError(StrategyError):
    """Raised when timing policy is unsupported."""

    code = "STRATEGY_UNSUPPORTED_TIMING_POLICY"


class StrategyLookaheadDetectedError(StrategyError):
    """Raised when lookahead risk or future data access is detected."""

    code = "STRATEGY_LOOKAHEAD_DETECTED"


class SimArbitraryCodeRejectedError(StrategyError):
    """Raised when arbitrary user Python code execution is rejected."""

    code = "SIM_ARBITRARY_CODE_REJECTED"


class StrategyInternalError(StrategyError):
    """Raised when internal strategy computations fail."""

    code = "STRATEGY_INTERNAL_ERROR"


class StrategyLifecycleNotApprovedError(StrategyError):
    """Raised when strategy environment exceeds lifecycle approval state."""

    code = "STRATEGY_LIFECYCLE_NOT_APPROVED"


class StrategyEnvironmentNotPermittedError(StrategyError):
    """Raised when the target environment is not declared in registry."""

    code = "STRATEGY_ENVIRONMENT_NOT_PERMITTED"


class StrategyArtifactHashMismatchError(StrategyError):
    """Raised when package artifact hash does not match registry entry."""

    code = "STRATEGY_ARTIFACT_HASH_MISMATCH"


class StrategyDependencyHashMismatchError(StrategyError):
    """Raised when lockfile hash mismatch is detected."""

    code = "STRATEGY_DEPENDENCY_HASH_MISMATCH"


class IndicatorModuleError(StrategyError):
    """Raised when an underlying indicator module call fails."""

    code = "INDICATOR_MODULE_ERROR"


class StrategyCheckpointInvalidError(StrategyError):
    """Raised when checkpoint data shape is invalid."""

    code = "STRATEGY_CHECKPOINT_INVALID"


class StrategyCheckpointIncompatibleError(StrategyError):
    """Raised when restored checkpoint has mismatching settings or version."""

    code = "STRATEGY_CHECKPOINT_INCOMPATIBLE"


class StrategyDataNotReadyError(StrategyError):
    """Raised when input data is missing or not ready."""

    code = "STRATEGY_DATA_NOT_READY"


class StrategyIndicatorNotReadyError(StrategyError):
    """Raised when required indicators are warm-up incomplete."""

    code = "STRATEGY_INDICATOR_NOT_READY"


class StrategyMissingRequiredDataError(StrategyError):
    """Raised when data query yields missing fields."""

    code = "STRATEGY_MISSING_REQUIRED_DATA"


class StrategyStaleDataError(StrategyError):
    """Raised when data arrival exceeds latency threshold."""

    code = "STRATEGY_STALE_DATA"


class StrategyDuplicateIntentError(StrategyError):
    """Raised when idempotency or sequence keys collide."""

    code = "STRATEGY_DUPLICATE_INTENT"


class StrategyResourceLimitExceededError(StrategyError):
    """Raised when CPU time or memory allocations exceed limit."""

    code = "STRATEGY_RESOURCE_LIMIT_EXCEEDED"


class StrategyTimeoutError(StrategyError):
    """Raised when strategy hook timing exceeds budget limit."""

    code = "STRATEGY_TIMEOUT"


class StrategyValidationArtifactRequiredError(StrategyError):
    """Raised when promotion fails due to missing evidence artifact."""

    code = "STRATEGY_VALIDATION_ARTIFACT_REQUIRED"


class StrategyRiskProfileRequiredError(StrategyError):
    """Raised when strategy registry has no declared risk profile."""

    code = "STRATEGY_RISK_PROFILE_REQUIRED"


class StrategyCircuitBreakerTriggeredError(StrategyError):
    """Raised when circuit breaker stops intent generation."""

    code = "STRATEGY_CIRCUIT_BREAKER_TRIGGERED"


class StrategyPositionLimitExceededError(StrategyError):
    """Raised when intent exceeds local position sizing caps."""

    code = "STRATEGY_POSITION_LIMIT_EXCEEDED"


class StrategyVolumeParticipationExceededError(StrategyError):
    """Raised when volume size exceeds visible participation limit."""

    code = "STRATEGY_VOLUME_PARTICIPATION_EXCEEDED"


class StrategyDataQualityGateFailedError(StrategyError):
    """Raised when timezone normalization or gaps reject tick inputs."""

    code = "STRATEGY_DATA_QUALITY_GATE_FAILED"


class StrategyPerformanceDegradedError(StrategyError):
    """Raised when analytics flag degraded returns."""

    code = "STRATEGY_PERFORMANCE_DEGRADED"


class StrategyDriftDetectedError(StrategyError):
    """Raised when model inputs drift statistical limits."""

    code = "STRATEGY_DRIFT_DETECTED"


class StrategyRegulatoryLimitBreachedError(StrategyError):
    """Raised when local validation hits regulatory caps."""

    code = "STRATEGY_REGULATORY_LIMIT_BREACHED"


class StrategyMarketAccessRevokedError(StrategyError):
    """Raised when broker reports login or venue suspension."""

    code = "STRATEGY_MARKET_ACCESS_REVOKED"


class StrategyHardKilledError(StrategyError):
    """Raised when external orchestration sends emergency hard kill signal."""

    code = "STRATEGY_HARD_KILLED"


# --- Risk Domain Errors ---


class RiskError(ValidationError):
    """Base error type for all risk calculations and registry operations.

    Ensures that custom risk error codes are retained on the exception object.
    """

    code = "VALIDATION_FAILED"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        """Initialize with message and optional custom code."""
        super().__init__(message)
        self.code = code if code is not None else self.__class__.code


class InvalidPortfolioStateError(RiskError):
    """Raised when portfolio state has invalid structure or parameters."""

    code = "INVALID_PORTFOLIO_STATE"


class InvalidRiskConfigError(RiskError):
    """Raised when risk configuration is missing or invalid."""

    code = "INVALID_RISK_CONFIG"


class MissingEvidenceError(RiskError):
    """Raised when required evidence is missing."""

    code = "MISSING_EVIDENCE"


class StaleEvidenceError(RiskError):
    """Raised when required evidence is stale."""

    code = "STALE_EVIDENCE"


class LimitFailedError(RiskError):
    """Raised when risk limit check fails."""

    code = "LIMIT_FAILED"


class PolicyBlockedError(RiskError):
    """Raised when trade/allocation is blocked by deterministic policy."""

    code = "POLICY_BLOCKED"


class ApprovalRequiredError(RiskError):
    """Raised when action requires approval token."""

    code = "APPROVAL_REQUIRED"


class ApprovalTokenInvalidError(RiskError):
    """Raised when approval token is invalid."""

    code = "APPROVAL_TOKEN_INVALID"


class ApprovalTokenExpiredError(RiskError):
    """Raised when approval token has expired."""

    code = "APPROVAL_TOKEN_EXPIRED"


class ApprovalTokenRevokedError(RiskError):
    """Raised when approval token was revoked."""

    code = "APPROVAL_TOKEN_REVOKED"


class ApprovalTokenConsumedError(RiskError):
    """Raised when approval token was already consumed."""

    code = "APPROVAL_TOKEN_CONSUMED"


class ConfigVersionMismatchError(RiskError):
    """Raised when config version or hash mismatch occurs."""

    code = "CONFIG_VERSION_MISMATCH"


class ConfigCompatibilityNotApprovedError(RiskError):
    """Raised when config compatibility is not approved."""

    code = "CONFIG_COMPATIBILITY_NOT_APPROVED"


class ParametricVarGaussianWarningError(RiskError):
    """Warning/error when Gaussian assumptions are used for parametric VaR."""

    code = "PARAMETRIC_VAR_GAUSSIAN_WARNING"


class PendingApprovalDoubleSpendBlockedError(RiskError):
    """Raised when concurrent proposals risk double spending."""

    code = "PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED"


class PayloadTooLargeError(RiskError):
    """Raised when request payload is too large or nested too deeply."""

    code = "PAYLOAD_TOO_LARGE"


class MissingStopLossError(RiskError):
    """Raised when stop loss is missing for stop-dependent sizing."""

    code = "MISSING_STOP_LOSS"


class InsufficientVolatilityEvidenceError(RiskError):
    """Raised when volatility evidence is insufficient for calculation."""

    code = "INSUFFICIENT_VOLATILITY_EVIDENCE"


class InsufficientKEvidenceError(RiskError):
    """Raised when Kelly trade sample evidence is insufficient (< 30)."""

    code = "INSUFFICIENT_K_EVIDENCE"


class LiveStateStaleError(RiskError):
    """Raised when live state is stale."""

    code = "LIVE_STATE_STALE"


class InFlightToleranceExceededError(RiskError):
    """Raised when in-flight order tolerance buffer is exceeded."""

    code = "IN_FLIGHT_TOLERANCE_EXCEEDED"


class CalculationFailedError(RiskError):
    """Raised when a specific risk calculation fails."""

    code = "CALCULATION_FAILED"


class SnapshotBuildFailedError(RiskError):
    """Raised when snapshot building fails."""

    code = "SNAPSHOT_BUILD_FAILED"


class ReportGenerationFailedError(RiskError):
    """Raised when report generation fails."""

    code = "REPORT_GENERATION_FAILED"


class StorageError(RiskError):
    """Raised when risk storage or audit persistence operations fail."""

    code = "STORAGE_ERROR"


# --- Simulation Domain Errors ---


class SimulationError(ValidationError):
    """Base error type for all simulation and backtesting operations.

    Ensures that custom SIM_ error codes are retained on the exception object.
    """

    code = "VALIDATION_FAILED"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        """Initialize with message and optional custom code."""
        super().__init__(message)
        self.code = code if code is not None else self.__class__.code


class SimLookaheadDetectedError(SimulationError):
    """Raised when strategy attempts to access future data."""

    code = "SIM_LOOKAHEAD_DETECTED"


class SimPersistenceFailedError(SimulationError):
    """Raised when journal persistence operations fail."""

    code = "SIM_PERSISTENCE_FAILED"


def map_exception_to_strategy_error(exc: Exception) -> StrategyError:
    """Map any lower-level exception to a StrategyError code at boundaries.

    Ensures lookahead, indicator, and data errors map deterministically.
    """
    if isinstance(exc, StrategyError):
        return exc

    exc_name = exc.__class__.__name__
    msg = str(exc)

    # Check for lookahead
    if (
        exc_name == "LookaheadRiskError"
        or "LookaheadRisk" in exc_name
        or getattr(exc, "code", "") == "IND_LOOKAHEAD_RISK"
    ):
        return StrategyLookaheadDetectedError(msg)

    # Check for indicator failures
    if (
        exc_name.startswith("Indicator")
        or "Indicator" in exc_name
        or getattr(exc, "code", "").startswith("IND_")
    ):
        return IndicatorModuleError(f"Underlying indicator execution failed: {msg}")

    # Check for data service issues
    if "Data" in exc_name or getattr(exc, "code", "").startswith("DATA_"):
        return StrategyDataNotReadyError(f"Underlying data service failed: {msg}")

    # Fallback to internal error
    return StrategyInternalError(f"Internal calculation failed: {msg}")


# --- Error Routing Logic ---

RouteStatus = Literal["routed", "suppressed", "failed"]


@dataclass(frozen=True, slots=True)
class ErrorRouteResult:
    """Error routing result."""

    status: RouteStatus
    message: str
    route_key: str
    event_id: str | None


@dataclass
class ErrorRouter:
    """Bounded deduplicating error router."""

    bus: InMemoryEventBus
    dedupe_window_seconds: float = 60.0
    _last_seen: dict[str, float] = field(default_factory=dict)

    def route_error(
        self,
        *,
        error: BaseException | ErrorPayload,
        source: str,
        request_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ErrorRouteResult:
        """Route an error event unless it is suppressed by deduplication."""
        from app.utils.event_bus import build_event_envelope

        payload = (
            error if isinstance(error, dict) else exception_to_error_payload(error)
        )
        route_key = f"{source}:{payload['code']}:{redact_text(payload['details'])}"
        now = time.monotonic()
        previous = self._last_seen.get(route_key)
        if previous is not None and now - previous < self.dedupe_window_seconds:
            return ErrorRouteResult(
                "suppressed", "duplicate error suppressed", route_key, None
            )
        self._last_seen[route_key] = now
        event = build_event_envelope(
            event_type="utility.error",
            source=source,
            severity="error",
            request_id=request_id,
            payload={
                "code": payload["code"],
                "details": redact_text(payload["details"]),
            },
            metadata=redact_mapping(metadata or {}),
            idempotency_key=route_key,
        )
        result = self.bus.publish(event)
        if result.status in {"delivered", "duplicate"}:
            return ErrorRouteResult(
                "routed", "error routed", route_key, event["event_id"]
            )
        return ErrorRouteResult("failed", result.message, route_key, event["event_id"])


def route_error(
    error: BaseException | ErrorPayload,
    *,
    source: str,
    bus: InMemoryEventBus | None = None,
    request_id: str | None = None,
) -> ErrorRouteResult:
    """Route an error through a caller-supplied or temporary in-memory bus."""
    from app.utils.event_bus import InMemoryEventBus

    router = ErrorRouter(bus=bus or InMemoryEventBus())
    return router.route_error(error=error, source=source, request_id=request_id)


# --- Helper methods ---


def _validate_code_text(code: object, field_name: str = "code") -> str:
    """Return an uppercase code string or raise a typed validation error."""
    if not isinstance(code, str) or not code.strip():
        message = f"{field_name} must be a non-empty string."
        raise ValidationError(message)
    return code.strip().upper()


def normalize_error_code(
    code: str | None,
    *,
    default: str = "UNKNOWN_ERROR",
) -> str:
    """Return an approved deterministic error code.

    Use this at tool boundaries and response builders before emitting errors.
    Unknown codes resolve to ``default`` when approved, otherwise
    ``UNKNOWN_ERROR``.

    Args:
        code: Candidate error code.
        default: Approved fallback code.

    Returns:
        Approved deterministic error code.

    Side effects:
        Logs unknown-code normalization for diagnostics.
    """
    fallback = default.strip().upper() if isinstance(default, str) else "UNKNOWN_ERROR"
    if fallback not in APPROVED_ERROR_CODES:
        fallback = "UNKNOWN_ERROR"
    if not isinstance(code, str) or not code.strip():
        return fallback
    normalized = code.strip().upper()
    if normalized in APPROVED_ERROR_CODES:
        return normalized
    logger.warning(
        "unknown error code normalized",
        extra={
            "event_name": "error_code_normalized",
            "error_code": normalized,
        },
    )
    return fallback


def raise_for_invalid_code(code: str) -> None:
    """Raise when ``code`` is not in the approved error-code registry.

    Use this in tests or strict validation paths where unknown codes should be
    rejected instead of normalized.

    Args:
        code: Candidate error code.

    Raises:
        ValidationError: If the code is empty or not approved.

    Side effects:
        None.
    """
    normalized = _validate_code_text(code)
    if normalized not in APPROVED_ERROR_CODES:
        message = f"error code is not approved: {normalized}"
        raise ValidationError(message)


def error_name(code: str) -> str:
    """Return a deterministic human-readable name for an error code.

    Args:
        code: Error code to convert.

    Returns:
        Title-cased display name. Unknown codes are normalized safely first.

    Raises:
        ValidationError: If ``code`` is empty.

    Side effects:
        None.
    """
    normalized = normalize_error_code(_validate_code_text(code))
    return normalized.replace("_", " ").title()


def message_for(code: str, default: str | None = None) -> str:
    """Return the deterministic default message for an error code.

    Args:
        code: Error code to look up.
        default: Optional caller-provided fallback message for unknown codes.

    Returns:
        Known default message, provided fallback, or the ``UNKNOWN_ERROR``
        message for unknown codes.

    Raises:
        ValidationError: If ``code`` is empty.

    Side effects:
        None.
    """
    candidate = _validate_code_text(code)
    if candidate in ERROR_MESSAGES:
        return ERROR_MESSAGES[candidate]
    if default is not None:
        return default
    return ERROR_MESSAGES["UNKNOWN_ERROR"]


def code_for_exception(
    exception: BaseException,
    *,
    default: str = "TOOL_EXECUTION_FAILED",
) -> str:
    """Return a safe deterministic code for an exception.

    Args:
        exception: Exception to inspect. Compatible future domain errors may
            expose a string ``code`` attribute.
        default: Approved fallback for unknown non-HaruQuant exceptions.

    Returns:
        Approved deterministic error code.

    Side effects:
        None.
    """
    raw_code = getattr(exception, "code", None)
    if isinstance(raw_code, str):
        return normalize_error_code(raw_code, default=default)
    return normalize_error_code(default)


def details_for_exception(exception: BaseException) -> str:
    """Return safe human-readable details for an exception.

    Args:
        exception: Exception to describe.

    Returns:
        String details containing exception type and message. The raw exception
        object is never returned.

    Side effects:
        None.
    """
    return f"{exception.__class__.__name__}: {exception}"


def exception_to_error_payload(
    exception: BaseException,
    *,
    default_code: str = "TOOL_EXECUTION_FAILED",
) -> ErrorPayload:
    """Map an exception to a standard error payload.

    Args:
        exception: Exception to map.
        default_code: Approved fallback code for unknown exceptions.

    Returns:
        Mapping with deterministic ``code`` and string ``details``.

    Side effects:
        None.
    """
    return {
        "code": code_for_exception(exception, default=default_code),
        "details": details_for_exception(exception),
    }


def validate_error_payload(payload: Mapping[str, object]) -> ErrorPayload:
    """Validate and normalize a mapping into an error payload.

    Args:
        payload: Candidate payload containing ``code`` and ``details``.

    Returns:
        Normalized error payload.

    Raises:
        ValidationError: If required fields are missing or malformed.

    Side effects:
        None.
    """
    code = payload.get("code")
    details = payload.get("details")
    if set(payload) != {"code", "details"}:
        raise ValidationError("error must contain exactly code and details.")
    if not isinstance(details, str) or not details:
        raise ValidationError("error.details must be a non-empty string.")
    return {"code": normalize_error_code(_validate_code_text(code)), "details": details}
