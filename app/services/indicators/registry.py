# ruff: noqa: E501, PD011, ANN401, TRY301, ARG001, BLE001, PLR0912, PLR0915, C901
"""Indicator registry and convenience wrapper functions.

Provides thread-safe registration, listing, validation, and execution wrapper
methods for built-in and dynamic indicators.
"""

from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.indicators.adapters.canary import CanaryConfig

import pandas as pd

from app.services.indicators.adapters.audit import global_audit_logger
from app.services.indicators.adapters.cache import global_cache
from app.services.indicators.batch.momentum import RelativeStrengthIndex, WilliamsR
from app.services.indicators.batch.trend import (
    AverageDirectionalIndex,
    ExponentialMovingAverage,
    SimpleMovingAverage,
)
from app.services.indicators.batch.volatility import (
    AverageDailyRange,
    AverageTrueRange,
    RollingVolatility,
)
from app.services.indicators.calculations import (
    compute_input_checksum,
    compute_parameter_hash,
)
from app.services.indicators.errors import (
    IndicatorError,
    UnsupportedIndicatorError,
)
from app.services.indicators.protocols import (
    IndicatorConfig,
    IndicatorContext,
    IndicatorErrorPayload,
    IndicatorManifest,
    IndicatorProtocol,
    IndicatorResult,
)
from app.utils.errors import ValidationError
from app.utils.logger import logger


class IndicatorRegistry:
    """Thread-safe catalog registry for quantitative indicators."""

    def __init__(self) -> None:
        """Initialize the lock and empty dictionary map."""
        self._lock = Lock()
        self._registry: dict[str, type[IndicatorProtocol]] = {}

    def register_indicator(self, indicator_class: type[IndicatorProtocol]) -> None:
        """Add a constructor class to the registry."""
        with self._lock:
            # Set default status and dependencies if missing (for built-in indicators)
            if not hasattr(indicator_class, "status"):
                indicator_class.status = "official"  # type: ignore[attr-defined]
            if not hasattr(indicator_class, "dependencies"):
                indicator_class.dependencies = ["numpy", "pandas"]  # type: ignore[attr-defined]

            # Conformance checks
            res = validate_indicator(indicator_class)
            if not res.valid:
                from app.services.indicators.errors import CustomIndicatorRejectedError

                raise CustomIndicatorRejectedError(
                    res.message, code="IND_CUSTOM_INDICATOR_REJECTED"
                )

            ind_id = getattr(indicator_class, "indicator_id", None)
            if not isinstance(ind_id, str) or not ind_id:
                raise ValidationError(
                    "Indicator class must define a non-empty 'indicator_id'."
                )
            self._registry[ind_id.lower()] = indicator_class
            logger.info(f"Registered indicator: {ind_id}")

    def get_indicator(self, indicator_id: str) -> type[IndicatorProtocol]:
        """Fetch the constructor class for an indicator ID."""
        with self._lock:
            ind_lower = indicator_id.lower()
            if ind_lower not in self._registry:
                msg = f"Indicator '{indicator_id}' is not registered."
                raise UnsupportedIndicatorError(msg)
            return self._registry[ind_lower]

    def unregister_indicator(self, indicator_id: str) -> None:
        """Remove a constructor class from the registry."""
        with self._lock:
            ind_lower = indicator_id.lower()
            if ind_lower in self._registry:
                del self._registry[ind_lower]
                logger.info(f"Unregistered indicator: {indicator_id}")

    def list_indicators(self) -> list[str]:
        """Return a sorted list of registered indicator IDs."""
        with self._lock:
            return sorted(self._registry.keys())


def register_indicator(indicator_class: type[IndicatorProtocol]) -> None:
    """Public wrapper to register an indicator class."""
    global_registry.register_indicator(indicator_class)


def get_indicator(indicator_id: str) -> type[IndicatorProtocol]:
    """Public wrapper to get an indicator class."""
    return global_registry.get_indicator(indicator_id)


def unregister_indicator(indicator_id: str) -> None:
    """Public wrapper to unregister an indicator ID."""
    global_registry.unregister_indicator(indicator_id)


def list_indicators(self: Any = None) -> list[str]:
    """Public wrapper to list registered indicator IDs."""
    return global_registry.list_indicators()


class ValidationResult:
    """Result payload return by custom indicator validation checks."""

    def __init__(self, valid: bool, message: str) -> None:
        """Initialize the result state."""
        self.valid = valid
        self.message = message


def validate_indicator(indicator_class: Any) -> ValidationResult:
    """Verify standard typing protocol compatibility of custom indicator classes."""
    required_attrs = [
        "indicator_id",
        "name",
        "version",
        "formula_version",
        "status",
        "dependencies",
    ]
    for attr in required_attrs:
        if not hasattr(indicator_class, attr):
            return ValidationResult(
                False, f"Indicator is missing required attribute: {attr}"
            )

    status = indicator_class.status
    allowed_statuses = ("official", "experimental", "deprecated", "research-only")
    if status not in allowed_statuses:
        return ValidationResult(
            False,
            f"Invalid indicator status: {status}. Must be one of {allowed_statuses}.",
        )

    required_methods = [
        "validate_parameters",
        "required_columns",
        "output_columns",
        "warmup_requirement",
        "validate_input",
        "calculate",
    ]
    for method in required_methods:
        if not hasattr(indicator_class, method) or not callable(
            getattr(indicator_class, method)
        ):
            return ValidationResult(
                False, f"Indicator is missing required method: {method}"
            )

    # Static code analysis to inspect the calculate method for prohibited side-effects
    try:
        import inspect

        src = inspect.getsource(indicator_class.calculate)
        banned = {
            "network": ["requests.", "urllib.", "socket.", "aiohttp.", "http.client."],
            "filesystem": [
                "open(",
                ".write(",
                "to_csv",
                "to_parquet",
                "to_sql",
                "os.write(",
            ],
            "broker/mutation": [
                "metatrader",
                "ctrader",
                "broker.",
                "account.",
                "order_send",
                "trade.",
            ],
            "nondeterminism": ["random.", "np.random.", "randint("],
        }
        for category, tokens in banned.items():
            for token in tokens:
                if token in src:
                    return ValidationResult(
                        False,
                        f"Prohibited operation check failed: found {category} reference '{token}' in calculate method.",
                    )
    except Exception:
        # If inspection is impossible (e.g. builtins, dynamically generated objects where source is unavailable),
        # only allow it if the status is "official" to prevent locking out valid system components.
        if getattr(indicator_class, "status", None) != "official":
            return ValidationResult(
                False,
                "Prohibited operation check cannot be executed on this custom indicator.",
            )

    return ValidationResult(True, "Indicator is compatible.")


# Singleton instance
global_registry = IndicatorRegistry()

# Register default built-ins
global_registry.register_indicator(SimpleMovingAverage)
global_registry.register_indicator(ExponentialMovingAverage)
global_registry.register_indicator(AverageDirectionalIndex)
global_registry.register_indicator(AverageTrueRange)
global_registry.register_indicator(AverageDailyRange)
global_registry.register_indicator(RollingVolatility)
global_registry.register_indicator(RelativeStrengthIndex)
global_registry.register_indicator(WilliamsR)


def execute_indicator_workflow(
    indicator_id: str,
    data: pd.DataFrame,
    parameters: dict[str, Any],
    source_column: str = "close",
    error_mode: str = "exception",
    context: IndicatorContext | None = None,
    canary_config: CanaryConfig | None = None,
    **config_kwargs: Any,
) -> IndicatorResult:
    """Internal runner helper that resolves and executes indicator calculations."""
    if canary_config is not None and canary_config.enabled:
        from app.services.indicators.adapters.canary import global_canary_router

        return global_canary_router.evaluate_and_route(
            data,
            IndicatorConfig(
                indicator_id=indicator_id,
                parameters=parameters,
                source_column=source_column,
                **config_kwargs,
            ),
            context or IndicatorContext(),
            canary_config,
            execute_indicator_workflow,
        )

    import time

    from app.services.indicators.adapters.tracing import IndicatorSpan
    from app.services.indicators.calculations import compute_lookahead_metadata
    from app.services.indicators.errors import (
        InputMutationError,
        InvalidOutputColumnError,
        OutputColumnConflictError,
        ResourceLimitExceededError,
    )
    from app.services.indicators.protocols import IndicatorResourceLimits

    start_time = time.perf_counter()
    is_error = False
    is_timeout = False

    ctx = context or IndicatorContext()
    tracing_enabled = ctx.tracing_enabled
    traceparent = ctx.traceparent

    try:
        # Check error mode
        if error_mode not in ("exception", "result"):
            raise ValidationError("error_mode must be 'exception' or 'result'.")

        ind_class = get_indicator(indicator_id)
        ind_inst = ind_class()

        config = IndicatorConfig(
            indicator_id=indicator_id,
            parameters=parameters,
            source_column=source_column,
            **config_kwargs,
        )

        # Check execution backend
        if config.execution_backend == "out_of_core":
            from app.services.indicators.errors import UnsupportedOutOfCoreError

            raise UnsupportedOutOfCoreError(
                "Out-of-core execution backend is not supported.",
                code="IND_UNSUPPORTED_OUT_OF_CORE",
            )

        # Check acceleration backend
        if config.acceleration_backend is not None:
            if config.acceleration_backend == "unsupported_backend":
                from app.services.indicators.errors import (
                    AccelerationBackendUnavailableError,
                )

                msg = f"Acceleration backend '{config.acceleration_backend}' is not available."
                raise AccelerationBackendUnavailableError(
                    msg,
                    code="IND_ACCELERATION_BACKEND_UNAVAILABLE",
                )
            # Fallback policy
            logger.info(
                f"Falling back to pandas_vectorized from acceleration backend: {config.acceleration_backend}"
            )

        # Check deprecation
        if getattr(ind_class, "status", None) == "deprecated":
            if not getattr(config, "allow_deprecated", False):
                from app.services.indicators.errors import DeprecatedIndicatorError

                msg = f"Indicator '{indicator_id}' is deprecated."
                raise DeprecatedIndicatorError(msg, code="IND_DEPRECATED")
            logger.warning(f"Using deprecated indicator '{indicator_id}'.")

        # Log details including id, version, parameter_hash, checksum, symbol count, timeframe, and request_id
        symbol_count = 1
        if isinstance(data.index, pd.MultiIndex) and "symbol" in data.index.names:
            symbol_count = len(data.index.unique(level="symbol"))
        elif "symbol" in data.columns:
            symbol_count = len(data["symbol"].unique())

        timeframe = "D1"
        if "timeframe" in data.columns:
            timeframe = str(data["timeframe"].iloc[0])

        param_hash = compute_parameter_hash(config.parameters)
        src_cols = (
            [config.source_column] if config.source_column in data.columns else []
        )
        input_checksum = (
            compute_input_checksum(data, src_cols) if not data.empty else ""
        )

        logger.info(
            f"Executing indicator workflow: {indicator_id}",
            extra={
                "indicator_id": indicator_id,
                "implementation_version": getattr(ind_class, "version", "1.0.0"),
                "parameter_hash": param_hash,
                "input_checksum": input_checksum,
                "symbol_count": symbol_count,
                "timeframe": timeframe,
                "request_id": ctx.request_id,
                "correlation_id": ctx.correlation_id,
            },
        )

        with IndicatorSpan(
            f"execute_{indicator_id}",
            traceparent=traceparent,
            is_enabled=tracing_enabled,
        ):
            # Caching logic
            cache_key = ""
            if config.cache_policy != "none":
                impl_version = getattr(ind_class, "version", "1.0.0")
                schema_version = "1.0.0"

                cache_key = global_cache.derive_key(
                    indicator_id=indicator_id,
                    param_hash=param_hash,
                    input_checksum=input_checksum,
                    impl_version=impl_version,
                    schema_version=schema_version,
                    precision_policy=config.precision_policy,
                )
                cached_result = global_cache.get(cache_key, config.cache_policy)
                if cached_result is not None:
                    global_audit_logger.log_audit(cached_result.manifest, ctx)
                    return cached_result

            # Execute actual calculation
            before_checksum = (
                compute_input_checksum(data, src_cols) if not data.empty else ""
            )
            result = ind_inst.calculate(data, config, ctx)
            after_checksum = (
                compute_input_checksum(data, src_cols) if not data.empty else ""
            )
            if before_checksum != after_checksum:
                raise InputMutationError(
                    "Input data was mutated during indicator calculation.",
                    code="IND_INPUT_MUTATION_DETECTED",
                )

            # Support custom output column names and collision policy checks
            default_cols = ind_inst.output_columns(
                config.parameters, config.source_column
            )
            if (
                config.output_naming_policy == "custom"
                and config.custom_output_columns is not None
            ):
                if len(config.custom_output_columns) != len(default_cols):
                    raise ValidationError("Custom output columns length mismatch.")

                for col in config.custom_output_columns:
                    if not col.isidentifier() or not all(
                        c.isalnum() or c == "_" for c in col
                    ):
                        msg = f"Custom column name '{col}' is not a valid snake_case identifier."
                        raise InvalidOutputColumnError(msg)

                final_cols = []
                rename_map = {}
                conflict_policy = config.column_conflict_policy
                for idx, col in enumerate(config.custom_output_columns):
                    target_col = col
                    if col in data.columns:
                        if conflict_policy == "fail":
                            msg = f"Custom column '{col}' conflicts with input columns."
                            raise OutputColumnConflictError(msg)
                        if conflict_policy == "suffix":
                            target_col = col + config.conflict_suffix
                    final_cols.append(target_col)
                    rename_map[default_cols[idx]] = target_col

                result_df = result.values.rename(columns=rename_map)
                result = IndicatorResult(
                    values=result_df,
                    output_columns=final_cols,
                    manifest=result.manifest,
                    errors=result.errors,
                    metrics=result.metrics,
                )

            # Store to cache if policy requires it
            if config.cache_policy != "none" and cache_key and not result.values.empty:
                global_cache.set(cache_key, result, config.cache_policy)

            # Log audit manifest
            global_audit_logger.log_audit(result.manifest, ctx)

            # Attach lookahead metadata and is_partial flag
            lookahead_meta = compute_lookahead_metadata(data, config, timeframe)
            result = IndicatorResult(
                values=result.values,
                output_columns=result.output_columns,
                manifest=result.manifest,
                errors=result.errors,
                metrics=result.metrics,
                is_partial=getattr(config, "is_partial", False)
                if hasattr(config, "is_partial")
                else False,
                lookahead_metadata=lookahead_meta,
            )

            # Enforce timeout checks at the end of calculation if not already caught
            duration = time.perf_counter() - start_time
            limits = config.resource_limits or IndicatorResourceLimits()
            if duration > limits.timeout_seconds:
                is_timeout = True
                msg = (
                    f"Calculation exceeded timeout of {limits.timeout_seconds} seconds."
                )
                raise ResourceLimitExceededError(msg)

            return result

    except IndicatorError as exc:
        is_error = True
        if isinstance(exc, ResourceLimitExceededError) and "timeout" in str(exc):
            is_timeout = True
        if error_mode == "exception":
            raise
        # Return empty payload with the error attached
        err_payload = IndicatorErrorPayload(
            code=exc.code,
            message=str(exc),
            details=getattr(exc, "details", None),
        )
        return IndicatorResult(
            values=pd.DataFrame(),
            output_columns=[],
            manifest=IndicatorManifest(indicator_id=indicator_id),
            errors=[err_payload],
        )
    except Exception as exc:
        is_error = True
        if error_mode == "exception":
            raise IndicatorError(str(exc), code="IND_INTERNAL_ERROR") from exc
        err_payload = IndicatorErrorPayload(
            code="IND_INTERNAL_ERROR",
            message=str(exc),
        )
        return IndicatorResult(
            values=pd.DataFrame(),
            output_columns=[],
            manifest=IndicatorManifest(indicator_id=indicator_id),
            errors=[err_payload],
        )
    finally:
        duration = time.perf_counter() - start_time
        from app.services.indicators.adapters.observability import global_slo_monitor

        global_slo_monitor.record_request(duration, is_error, is_timeout)


# --- 7. Built-in Convenience Wrappers ---


def sma(
    data: pd.DataFrame,
    period: int = 10,
    source: str = "close",
    error_mode: str = "exception",
    context: IndicatorContext | None = None,
    **config_kwargs: Any,
) -> IndicatorResult:
    """Compute Simple Moving Average."""
    return execute_indicator_workflow(
        "sma",
        data,
        {"period": period},
        source_column=source,
        error_mode=error_mode,
        context=context,
        **config_kwargs,
    )


def ema(
    data: pd.DataFrame,
    period: int = 10,
    source: str = "close",
    error_mode: str = "exception",
    context: IndicatorContext | None = None,
    **config_kwargs: Any,
) -> IndicatorResult:
    """Compute Exponential Moving Average."""
    return execute_indicator_workflow(
        "ema",
        data,
        {"period": period},
        source_column=source,
        error_mode=error_mode,
        context=context,
        **config_kwargs,
    )


def adx(
    data: pd.DataFrame,
    period: int = 14,
    error_mode: str = "exception",
    context: IndicatorContext | None = None,
    **config_kwargs: Any,
) -> IndicatorResult:
    """Compute Average Directional Index."""
    return execute_indicator_workflow(
        "adx",
        data,
        {"period": period},
        error_mode=error_mode,
        context=context,
        **config_kwargs,
    )


def atr(
    data: pd.DataFrame,
    period: int = 14,
    error_mode: str = "exception",
    context: IndicatorContext | None = None,
    **config_kwargs: Any,
) -> IndicatorResult:
    """Compute Average True Range."""
    return execute_indicator_workflow(
        "atr",
        data,
        {"period": period},
        error_mode=error_mode,
        context=context,
        **config_kwargs,
    )


def adr(
    data: pd.DataFrame,
    period: int = 20,
    error_mode: str = "exception",
    context: IndicatorContext | None = None,
    **config_kwargs: Any,
) -> IndicatorResult:
    """Compute Average Daily Range."""
    return execute_indicator_workflow(
        "adr",
        data,
        {"period": period},
        error_mode=error_mode,
        context=context,
        **config_kwargs,
    )


def rolling_volatility(
    data: pd.DataFrame,
    period: int = 20,
    source: str = "close",
    return_type: str = "log",
    ddof: int = 1,
    ann_factor: float = 1.0,
    error_mode: str = "exception",
    context: IndicatorContext | None = None,
    **config_kwargs: Any,
) -> IndicatorResult:
    """Compute Rolling Volatility."""
    params = {
        "period": period,
        "return_type": return_type,
        "ddof": ddof,
        "ann_factor": ann_factor,
    }
    return execute_indicator_workflow(
        "rolling_volatility",
        data,
        params,
        source_column=source,
        error_mode=error_mode,
        context=context,
        **config_kwargs,
    )


def rsi(
    data: pd.DataFrame,
    period: int = 14,
    source: str = "close",
    error_mode: str = "exception",
    context: IndicatorContext | None = None,
    **config_kwargs: Any,
) -> IndicatorResult:
    """Compute Relative Strength Index."""
    return execute_indicator_workflow(
        "rsi",
        data,
        {"period": period},
        source_column=source,
        error_mode=error_mode,
        context=context,
        **config_kwargs,
    )


def williams_r(
    data: pd.DataFrame,
    period: int = 14,
    error_mode: str = "exception",
    context: IndicatorContext | None = None,
    **config_kwargs: Any,
) -> IndicatorResult:
    """Compute Williams %R."""
    return execute_indicator_workflow(
        "williams_r",
        data,
        {"period": period},
        error_mode=error_mode,
        context=context,
        **config_kwargs,
    )
