# ruff: noqa: E501
"""Deterministic error definitions for the indicator service.

Inherits from the utility layer Error base class to ensure compatibility with
global diagnostic interfaces.
"""

from app.utils.errors import ValidationError


class IndicatorError(ValidationError):
    """Base error type for all indicator calculations and registry operations.

    Ensures that custom IND_ error codes are retained on the exception object.
    """

    code = "VALIDATION_FAILED"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        """Initialize with message and optional custom code."""
        super().__init__(message)
        # Assign directly to bypass normalize_error_code restrictions for IND_ codes
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
