"""Official AI tools implementation for the Market Data Service.

All functions are wrapped in standard success/error envelopes, validate inputs,
and delegate to the core business logic layer.
"""

import functools
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Literal

from app.services.data import (
    aggregate_ticks_to_bars as _aggregate_ticks_to_bars,
)
from app.services.data import (
    align_multitimeframe_data as _align_multitimeframe_data,
)
from app.services.data import (
    clear_data_cache as _clear_data_cache,
)
from app.services.data import (
    create_data_update_job as _create_data_update_job,
)
from app.services.data import (
    generate_synthetic_bars as _generate_synthetic_bars,
)
from app.services.data import (
    generate_synthetic_ticks as _generate_synthetic_ticks,
)
from app.services.data import (
    get_data as _get_data,
)
from app.services.data import (
    get_data_availability as _get_data_availability,
)
from app.services.data import (
    get_data_update_job_status as _get_data_update_job_status,
)
from app.services.data import (
    get_feed_status as _get_feed_status,
)
from app.services.data import (
    get_market_hours as _get_market_hours,
)
from app.services.data import (
    get_symbol_metadata as _get_symbol_metadata,
)
from app.services.data import (
    get_trading_sessions as _get_trading_sessions,
)
from app.services.data import (
    label_market_data as _label_market_data,
)
from app.services.data import (
    list_symbols as _list_symbols,
)
from app.services.data import (
    load_local_dataset as _load_local_dataset,
)
from app.services.data import (
    resample_ohlcv as _resample_ohlcv,
)
from app.services.data import (
    run_data_update_job_once as _run_data_update_job_once,
)
from app.services.data import (
    save_market_data as _save_market_data,
)
from app.services.data import (
    start_data_update_job as _start_data_update_job,
)
from app.services.data import (
    stop_data_update_job as _stop_data_update_job,
)
from app.services.data.validation import validate_timeframe
from app.utils.errors import ValidationError, exception_to_error_payload
from app.utils.logger import logger
from app.utils.normalization import normalize_timestamp
from app.utils.standard import build_metadata, error_response, success_response

_SUCCESS_MSG_TEMPLATES: dict[str, Callable[[Any], str]] = {
    "get_market_data": (
        lambda d: f"Successfully retrieved {len(d)} market data records."
    ),
    "get_tick_data": (lambda d: f"Successfully retrieved {len(d)} tick records."),
    "get_spread_data": (lambda d: f"Successfully retrieved {len(d)} spread records."),
    "get_historical_volume": (lambda _: "Historical volume records retrieved."),
    "resample_ohlcv": (lambda _: "Resampling completed."),
    "align_multitimeframe_data": (lambda _: "Multi-timeframe alignment completed."),
    "aggregate_ticks_to_bars": (
        lambda d: f"Successfully aggregated ticks to {len(d)} bars."
    ),
    "generate_synthetic_ticks": (lambda d: f"Generated {len(d)} synthetic ticks."),
    "generate_synthetic_bars": (lambda d: f"Generated {len(d)} synthetic bars."),
    "label_market_data": (lambda _: "Data labeling completed."),
    "load_local_dataset": (
        lambda d: f"Successfully loaded {len(d)} local dataset records."
    ),
    "save_market_data": lambda d: (
        f"Successfully saved "
        f"{d.get('record_count', 0) if isinstance(d, dict) else len(d)} "
        f"records."
    ),
    "clear_data_cache": lambda d: (
        f"Successfully cleared cache: "
        f"{d.get('cleared_count', 0) if isinstance(d, dict) else 0} "
        f"entries removed."
    ),
    "get_data_availability": (lambda _: "Data availability check completed."),
    "get_symbol_metadata": (lambda _: "Successfully retrieved symbol metadata."),
    "list_symbols": (lambda d: f"Successfully listed {len(d)} symbols."),
    "get_market_hours": (lambda _: "Market hours retrieved successfully."),
    "get_trading_sessions": (lambda _: "Trading sessions retrieved successfully."),
    "create_data_update_job": (
        lambda d: f"Successfully created data update job: {d.get('name')}."
    ),
    "get_data_update_job_status": lambda d: (
        f"Successfully retrieved status for {len(d)} data update jobs."
        if isinstance(d, list)
        else f"Successfully retrieved status for job: {d.get('name')}."
    ),
    "run_data_update_job_once": (
        lambda d: f"Successfully executed run-once for job: {d.get('name')}."
    ),
    "start_data_update_job": (
        lambda d: f"Successfully started data update job: {d.get('job_id')}."
    ),
    "stop_data_update_job": (
        lambda d: f"Successfully stopped data update job: {d.get('job_id')}."
    ),
    "get_feed_status": lambda d: (
        f"Successfully retrieved status for {len(d)} feeds."
        if isinstance(d, list)
        else f"Successfully retrieved status for feed: {d.get('feed_id')}."
    ),
}

_ERROR_MSG_TEMPLATES: dict[str, str] = {
    "get_market_data": "Failed to fetch market data.",
    "get_tick_data": "Failed to fetch tick data.",
    "get_spread_data": "Failed to fetch spread data.",
    "get_historical_volume": "Failed to fetch historical volume data.",
    "resample_ohlcv": "Resampling failed.",
    "align_multitimeframe_data": "Alignment failed.",
    "aggregate_ticks_to_bars": "Failed to aggregate ticks to bars.",
    "generate_synthetic_ticks": "Synthetic tick generation failed.",
    "generate_synthetic_bars": "Synthetic bar generation failed.",
    "label_market_data": "Labeling failed.",
    "load_local_dataset": "Failed to load local dataset.",
    "save_market_data": "Failed to save market data.",
    "clear_data_cache": "Failed to clear data cache.",
    "get_data_availability": "Failed to fetch data availability.",
    "get_symbol_metadata": "Failed to retrieve symbol metadata.",
    "list_symbols": "Failed to list symbols.",
    "get_market_hours": "Failed to fetch market hours.",
    "get_trading_sessions": "Failed to fetch trading sessions.",
    "create_data_update_job": "Failed to create data update job.",
    "get_data_update_job_status": "Failed to get job status.",
    "run_data_update_job_once": "Failed to run data update job.",
    "start_data_update_job": "Failed to start data update job.",
    "stop_data_update_job": "Failed to stop data update job.",
    "get_feed_status": "Failed to get feed status.",
}


def data_tool(
    name: str,
    version: str = "1.0.0",
    category: str = "data",
    risk_level: Literal["low", "medium", "high", "critical"] = "low",
    *,
    reads: bool = False,
    writes: bool = False,
    updates: bool = False,
    deletes: bool = False,
    trades: bool = False,
    requires_network: bool = False,
) -> Callable[..., Callable[..., dict[str, Any]]]:
    """Decorator to standardize tool responses into standard envelopes."""

    def decorator(func: Callable[..., Any]) -> Callable[..., dict[str, Any]]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> dict[str, Any]:  # noqa: ANN401
            request_id = kwargs.get("request_id")
            t_start = datetime.now(UTC).timestamp()
            try:
                data = func(*args, **kwargs)
                meta = build_metadata(
                    tool_name=name,
                    tool_version=version,
                    tool_category=category,
                    tool_risk_level=risk_level,
                    request_id=request_id,
                    reads=reads,
                    writes=writes,
                    updates=updates,
                    deletes=deletes,
                    trades=trades,
                    requires_network=requires_network,
                    start_time=t_start,
                )

                # Determine success message
                msg = _SUCCESS_MSG_TEMPLATES.get(
                    name, lambda _: f"Successfully executed tool {name}."
                )(data)

                return success_response(  # type: ignore[return-value]
                    message=msg,
                    data=data,
                    metadata=meta,
                )
            except Exception as e:  # noqa: BLE001
                logger.error(
                    f"Tool {name} error: {e}",
                    extra={"request_id": request_id},
                )
                meta = build_metadata(
                    tool_name=name,
                    tool_version=version,
                    tool_category=category,
                    tool_risk_level=risk_level,
                    request_id=request_id,
                    reads=reads,
                    writes=writes,
                    updates=updates,
                    deletes=deletes,
                    trades=trades,
                    requires_network=requires_network,
                    start_time=t_start,
                )

                err_msg = _ERROR_MSG_TEMPLATES.get(name, f"Failed to execute {name}.")

                payload = exception_to_error_payload(
                    e, default_code="TOOL_EXECUTION_FAILED"
                )
                return error_response(  # type: ignore[return-value]
                    message=err_msg,
                    code=payload["code"],
                    details=payload["details"],
                    metadata=meta,
                )

        return wrapper

    return decorator


# --- 1. Historical & Retrieval Tools ---


@data_tool(name="get_market_data", risk_level="low", reads=True)
def get_market_data(
    symbol: str,
    timeframe: str,
    start_time: str,
    end_time: str,
    source: str = "csv",
    limit: int | None = None,
    stale_data_behavior: str = "refresh_and_return",
    workflow_context: str = "research",
    fallback_sources: list[str] | None = None,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve normalized historical OHLCV bar records."""
    return _get_data(
        symbol=symbol,
        start_time=start_time,
        end_time=end_time,
        data_kind="ohlcv",
        timeframe=timeframe,
        source=source,
        limit=limit,
        stale_data_behavior=stale_data_behavior,
        workflow_context=workflow_context,
        fallback_sources=fallback_sources,
        request_id=request_id,
    )


@data_tool(name="get_tick_data", risk_level="low", reads=True)
def get_tick_data(
    symbol: str,
    start_time: str,
    end_time: str,
    source: str = "csv",
    limit: int | None = None,
    stale_data_behavior: str = "refresh_and_return",
    workflow_context: str = "research",
    fallback_sources: list[str] | None = None,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve normalized historical tick records."""
    return _get_data(
        symbol=symbol,
        start_time=start_time,
        end_time=end_time,
        data_kind="ticks",
        source=source,
        limit=limit,
        stale_data_behavior=stale_data_behavior,
        workflow_context=workflow_context,
        fallback_sources=fallback_sources,
        request_id=request_id,
    )


@data_tool(name="get_spread_data", risk_level="low", reads=True)
def get_spread_data(
    symbol: str,
    start_time: str,
    end_time: str,
    source: str = "csv",
    limit: int | None = None,
    stale_data_behavior: str = "refresh_and_return",
    workflow_context: str = "research",
    fallback_sources: list[str] | None = None,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Retrieve normalized historical spread records."""
    return _get_data(
        symbol=symbol,
        start_time=start_time,
        end_time=end_time,
        data_kind="spreads",
        source=source,
        limit=limit,
        stale_data_behavior=stale_data_behavior,
        workflow_context=workflow_context,
        fallback_sources=fallback_sources,
        request_id=request_id,
    )


@data_tool(name="get_historical_volume", risk_level="low", reads=True)
def get_historical_volume(
    symbol: str,
    timeframe: str,
    start_time: str,
    end_time: str,
    source: str = "csv",
    limit: int | None = None,
    stale_data_behavior: str = "refresh_and_return",
    workflow_context: str = "research",
    fallback_sources: list[str] | None = None,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Return volume-specific historical records or summaries."""
    return _get_data(
        symbol=symbol,
        start_time=start_time,
        end_time=end_time,
        data_kind="volume",
        timeframe=timeframe,
        source=source,
        limit=limit,
        stale_data_behavior=stale_data_behavior,
        workflow_context=workflow_context,
        fallback_sources=fallback_sources,
        request_id=request_id,
    )


# --- 2. Transformation & Generation Tools ---


@data_tool(name="resample_ohlcv", risk_level="low", reads=True)
def resample_ohlcv(
    records: list[dict[str, Any]],
    source_timeframe: str,
    target_timeframe: str,
    *,
    spread_policy: str = "average",
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Resample normalized OHLCV records into higher timeframes."""
    validate_timeframe(source_timeframe)
    validate_timeframe(target_timeframe)
    return _resample_ohlcv(
        records=records,
        target_timeframe=target_timeframe,
        spread_policy=spread_policy,
        request_id=request_id,
    )


@data_tool(name="align_multitimeframe_data", risk_level="low", reads=True)
def align_multitimeframe_data(
    records_map: dict[str, list[dict[str, Any]]],
    base_timeframe: str,
    *,
    allow_lookahead: bool = False,
    alignment_method: str = "last_known_closed_bar",
    request_id: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Align multiple timeframes without lookahead by default."""
    validate_timeframe(base_timeframe)
    if base_timeframe not in records_map:
        err_msg = f"Base timeframe {base_timeframe} missing from records_map."
        raise ValidationError(err_msg)
    target_timestamps = [r["timestamp"] for r in records_map[base_timeframe]]
    return _align_multitimeframe_data(
        datasets=records_map,
        target_timestamps=target_timestamps,
        allow_lookahead=allow_lookahead,
        alignment_method=alignment_method,
        request_id=request_id,
    )


@data_tool(name="generate_synthetic_ticks", risk_level="low", reads=True)
def generate_synthetic_ticks(
    symbol: str,
    start_time: str,
    num_ticks: int = 100,
    start_price: float = 1.0,
    average_spread: float = 0.0002,
    volatility: float = 0.001,
    seed: int | None = None,
    *,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Generate deterministic synthetic tick data when a seed is supplied."""
    return _generate_synthetic_ticks(
        symbol=symbol,
        start_time=start_time,
        num_ticks=num_ticks,
        start_price=start_price,
        average_spread=average_spread,
        volatility=volatility,
        seed=seed,
        request_id=request_id,
    )


@data_tool(name="generate_synthetic_bars", risk_level="low", reads=True)
def generate_synthetic_bars(
    symbol: str,
    timeframe: str,
    start_time: str,
    num_bars: int = 100,
    start_price: float = 1.0,
    drift: float = 0.0001,
    volatility: float = 0.01,
    seed: int | None = None,
    *,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Generate deterministic synthetic bar data when a seed is supplied."""
    return _generate_synthetic_bars(
        symbol=symbol,
        timeframe=timeframe,
        start_time=start_time,
        num_bars=num_bars,
        start_price=start_price,
        drift=drift,
        volatility=volatility,
        seed=seed,
        request_id=request_id,
    )


@data_tool(name="aggregate_ticks_to_bars", risk_level="low", reads=True)
def aggregate_ticks_to_bars(
    ticks: list[dict[str, Any]],
    timeframe: str,
    *,
    repair: bool = False,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Aggregate tick records into OHLCV bars."""
    return _aggregate_ticks_to_bars(
        ticks=ticks,
        timeframe=timeframe,
        repair=repair,
        request_id=request_id,
    )


@data_tool(name="label_market_data", risk_level="low", reads=True)
def label_market_data(
    records: list[dict[str, Any]],
    method: str = "fixed_horizon",
    *,
    horizon: int = 5,
    threshold: float = 0.001,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Generate deterministic historical labels without claiming predictive value."""
    if method != "fixed_horizon":
        err_msg = f"Unsupported labeling method: {method}"
        raise ValidationError(err_msg)
    return _label_market_data(
        records=records,
        horizon=horizon,
        threshold=threshold,
        request_id=request_id,
    )


# --- 3. Storage & Caching Tools ---


@data_tool(name="load_local_dataset", risk_level="low", reads=True)
def load_local_dataset(
    path_str: str,
    *,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Load CSV/Parquet local datasets into normalized records."""
    return _load_local_dataset(path_str=path_str, request_id=request_id)


@data_tool(name="save_market_data", risk_level="medium", writes=True)
def save_market_data(
    records: list[dict[str, Any]],
    path_str: str,
    format_str: str = "parquet",
    *,
    overwrite: bool = False,
    include_metadata: bool = True,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Save validated normalized records to approved CSV/Parquet storage paths."""
    return _save_market_data(
        records=records,
        path_str=path_str,
        format_str=format_str,
        overwrite=overwrite,
        include_metadata=include_metadata,
        request_id=request_id,
    )


@data_tool(name="clear_data_cache", risk_level="medium", writes=True, deletes=True)
def clear_data_cache(
    namespace: str,
    source_filter: str | None = None,
    symbol_filter: str | None = None,
    *,
    dry_run: bool = True,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Inspect or clear cached data namespaces safely."""
    return _clear_data_cache(
        namespace=namespace,
        source_filter=source_filter,
        symbol_filter=symbol_filter,
        dry_run=dry_run,
        request_id=request_id,
    )


# --- 4. Metadata & Discovery Tools ---


@data_tool(name="get_data_availability", risk_level="low", reads=True)
def get_data_availability(
    symbol: str,
    timeframe: str,
    source: str = "csv",
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Inspect committed ranges, gaps, and record counts."""
    return _get_data_availability(
        symbol=symbol,
        timeframe=timeframe,
        source=source,
        request_id=request_id,
    )


@data_tool(name="get_symbol_metadata", risk_level="low", reads=True)
def get_symbol_metadata(
    symbol: str,
    source: str = "csv",
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Retrieve normalized symbol and asset metadata."""
    return _get_symbol_metadata(symbol=symbol, source=source, request_id=request_id)


@data_tool(name="list_symbols", risk_level="low", reads=True)
def list_symbols(
    source: str = "csv",
    *,
    request_id: str | None = None,
) -> list[str]:
    """List symbols discovered from the source."""
    return _list_symbols(source=source, request_id=request_id)


@data_tool(name="get_market_hours", risk_level="low", reads=True)
def get_market_hours(
    symbol: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Return timezone-aware market hours (Phase 1)."""
    return _get_market_hours(symbol=symbol, request_id=request_id)


@data_tool(name="get_trading_sessions", risk_level="low", reads=True)
def get_trading_sessions(
    start_time: str,
    end_time: str,
    *,
    request_id: str | None = None,
) -> list[dict[str, Any]]:
    """Return normalized session windows and labels."""
    t_s = normalize_timestamp(start_time)
    t_e = normalize_timestamp(end_time)
    return _get_trading_sessions(start_time=t_s, end_time=t_e, request_id=request_id)


# --- 5. Scheduler & Job Tools ---


@data_tool(name="create_data_update_job", risk_level="medium", writes=True)
def create_data_update_job(
    name: str,
    source: str,
    symbols: list[str],
    timeframes: list[str],
    data_kind: str,
    storage_format: str,
    storage_path: str,
    start_time: str | None = None,
    end_time: str | None = None,
    schedule: str | None = None,
    enabled: bool = True,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Create a persisted data update job definition in the database."""
    return _create_data_update_job(
        name=name,
        source=source,
        symbols=symbols,
        timeframes=timeframes,
        data_kind=data_kind,
        storage_format=storage_format,
        storage_path=storage_path,
        start_time=start_time,
        end_time=end_time,
        schedule=schedule,
        enabled=enabled,
        request_id=request_id,
    )


@data_tool(name="start_data_update_job", risk_level="medium", updates=True)
def start_data_update_job(
    name: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Start recurring background execution for a valid existing job or schedule."""
    return _start_data_update_job(name=name, request_id=request_id)


@data_tool(name="stop_data_update_job", risk_level="medium", updates=True)
def stop_data_update_job(
    name: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Stop or disable scheduled background execution for a job."""
    return _stop_data_update_job(name=name, request_id=request_id)


@data_tool(name="run_data_update_job_once", risk_level="medium", updates=True)
def run_data_update_job_once(
    name: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Execute one immediate update run of a job without scheduling it."""
    return _run_data_update_job_once(name=name, request_id=request_id)


@data_tool(name="get_data_update_job_status", risk_level="low", reads=True)
def get_data_update_job_status(
    name: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any] | list[dict[str, Any]]:
    """Inspect status metrics of a job definition."""
    return _get_data_update_job_status(name=name, request_id=request_id)


@data_tool(name="get_feed_status", risk_level="low", reads=True)
def get_feed_status(
    feed_id: str | None = None,
    source: str | None = None,
    symbol: str | None = None,
    data_kind: str | None = None,
    *,
    request_id: str | None = None,
) -> dict[str, Any] | list[dict[str, Any]]:
    """Inspect real-time feed health, heartbeat timeouts, and circuit breaker states."""
    return _get_feed_status(
        feed_id=feed_id,
        source=source,
        symbol=symbol,
        data_kind=data_kind,
        request_id=request_id,
    )
