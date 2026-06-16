# ruff: noqa: E501, C901, PLR0912, PLR0915, ANN401
"""Type declarations and interfaces for the indicators service.

This module defines standard protocols, configs, contexts, results, and manifest
structures that unify all built-in and custom indicator calculations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

import pandas as pd


@dataclass(frozen=True)
class IndicatorResourceLimits:
    """Resource constraints for indicator request execution.

    Attributes:
        max_rows: Maximum input rows allowed.
        max_symbols: Maximum unique symbols allowed in multi-index data.
        max_columns: Maximum input columns allowed.
        memory_budget_bytes: Estimated memory size limit in bytes.
        chunk_size: Processing chunk row size.
        timeout_seconds: Execution timeout limit in seconds.
    """

    max_rows: int = 10_000_000
    max_symbols: int = 1_000
    max_columns: int = 256
    memory_budget_bytes: int = 4_294_967_296  # 4 GB
    chunk_size: int = 1_000_000
    timeout_seconds: float = 60.0


@dataclass(frozen=True)
class IndicatorConfig:
    """Configuration schema for configuring an indicator run.

    Attributes:
        indicator_id: The unique identifier of the target indicator (e.g. 'sma').
        parameters: Dictionary of formula-specific hyper-parameters.
        source_column: The target price/series column (defaults to 'close').
        output_naming_policy: Policy for naming output columns ('default', 'custom').
        output_mode: Dictates returned df type ('values_only', 'join').
        column_conflict_policy: Behavior on column collision ('fail', 'overwrite', 'suffix').
        precision_policy: Precision specification ('float64', 'decimal').
        cache_policy: Caching mode ('none', 'best_effort', 'strict').
        calendar_policy: Session-aware calendar identifier.
        availability_policy: Logic for calculating available_at.
        execution_backend: Runtime engine ('in_memory', 'out_of_core').
        resource_limits: Optional override constraints.
        custom_output_columns: Optional list of output names for 'custom' policy.
        conflict_suffix: Custom suffix used when column_conflict_policy is 'suffix'.
    """

    indicator_id: str
    parameters: dict[str, Any] = field(default_factory=dict)
    source_column: str = "close"
    output_naming_policy: str = "default"
    output_mode: str = "values_only"
    column_conflict_policy: str = "fail"
    precision_policy: str = "float64"
    cache_policy: str = "none"
    calendar_policy: str = "continuous"
    availability_policy: str = "standard"
    execution_backend: str = "in_memory"
    resource_limits: IndicatorResourceLimits | None = None
    custom_output_columns: list[str] | None = None
    conflict_suffix: str = "_indicator"
    acceleration_backend: str | None = None
    is_partial: bool = False
    price_adjustment_status: str = "raw"
    price_source: str = "trade"
    venue: str | None = None
    exchange: str | None = None
    data_vendor: str | None = None
    symbol_mapping_contract: dict[str, str] | None = None
    spread_rejection_threshold: float | None = 0.5
    allow_unknown_adjustment: bool = False
    allow_stub_quotes: bool = False
    allow_deprecated: bool = False


@dataclass(frozen=True)
class IndicatorContext:
    """Operational execution context for tracing and monitoring.

    Attributes:
        request_id: Unique identifier tracing back to the client request.
        correlation_id: Flow identifier for cross-module diagnostics.
        actor: Identity (human or agent) initiating the calculation.
        workflow: Context name (e.g., 'backtest', 'live', 'research').
        environment: Execution tier ('research', 'paper', 'live').
        tracing_enabled: If True, enables tracing spans.
        traceparent: Optional W3C traceparent string header context.
        tracestate: Optional trace state propagation context.
    """

    request_id: str | None = None
    correlation_id: str | None = None
    actor: str | None = None
    workflow: str | None = None
    environment: str | None = None
    tracing_enabled: bool = False
    traceparent: str | None = None
    tracestate: str | None = None


@dataclass(frozen=True)
class IndicatorErrorPayload:
    """Structured, safe error diagnostics for indicators."""

    code: str
    message: str
    details: str | None = None


@dataclass(frozen=True)
class IndicatorManifest:
    """Audit-trail descriptor for reproducibility and version pinning.

    Attributes:
        manifest_version: Version of this manifest format.
        indicator_id: The ID of the computed indicator.
        indicator_version: Version code of the indicator code.
        formula_version: The mathematical version code of the formula.
        output_schema_version: Schema version of output payload.
        parameter_hash: Hex hash of normalized config parameters.
        input_checksum: Checksum of input prices/timestamps.
        output_checksum: Checksum of computed results.
        data_provenance: Provenance details (price source, venue, vendors).
        output_contract: Configuration of resulting columns.
        execution_backend: Metadata of calculation run (CPU, RAM, library).
        timing: Time duration logs.
        output_shape: Row count, symbol count, dtype mapping.
        environment: Host Python version, libraries, OS.
    """

    manifest_version: str = "1.0.0"
    indicator_id: str = ""
    indicator_version: str = ""
    formula_version: str = ""
    output_schema_version: str = "1.0.0"
    parameter_hash: str = ""
    input_checksum: str = ""
    output_checksum: str = ""
    data_provenance: dict[str, Any] = field(default_factory=dict)
    output_contract: dict[str, Any] = field(default_factory=dict)
    execution_backend: dict[str, Any] = field(default_factory=dict)
    timing: dict[str, Any] = field(default_factory=dict)
    output_shape: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    rollout: dict[str, Any] = field(default_factory=dict)
    access_control: dict[str, Any] = field(default_factory=dict)
    quality_flag_policy: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IndicatorResult:
    """Wrapper holding output values, metadata, and calculation audit logs.

    Attributes:
        values: Aligned DataFrame containing 'timestamp', 'symbol', indicators,
            'available_at', and 'quality'.
        output_columns: Explicit list of generated column names.
        manifest: Standalone descriptor object.
        errors: List of structured errors encountered (if non-blocking).
        metrics: Latency and row size metrics.
        is_partial: Whether this result is a partial calculation output chunk.
        lookahead_metadata: Execution metadata flags for downstream lookahead checks.
    """

    values: pd.DataFrame
    output_columns: list[str]
    manifest: IndicatorManifest
    errors: list[IndicatorErrorPayload] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    is_partial: bool = False
    lookahead_metadata: dict[str, Any] = field(default_factory=dict)

    def join_to(self, input_data: pd.DataFrame, mode: str = "copy") -> pd.DataFrame:
        """Align and append generated indicator columns back to source dataset.

        Args:
            input_data: The source OHLCV DataFrame to join.
            mode: Mode of operation (currently only 'copy' is supported).

        Returns:
            A copy of the input dataframe with the new indicator columns appended.
        """
        pd_module = pd
        if not isinstance(input_data, pd_module.DataFrame):
            from app.utils.errors import ValidationError

            raise ValidationError(
                "input_data must be a pandas DataFrame.", code="INVALID_INPUT"
            )

        if mode != "copy":
            from app.utils.errors import ValidationError

            raise ValidationError(
                "Only 'copy' mode is supported.", code="INVALID_INPUT"
            )

        # Determine index type
        df_copy = input_data.copy()
        original_index = df_copy.index

        # Prepare df_copy for merging by ensuring it has "symbol" and "timestamp" columns
        added_symbol = False
        added_timestamp = False

        if "symbol" not in df_copy.columns and "symbol" in original_index.names:
            df_copy["symbol"] = original_index.get_level_values("symbol")
            added_symbol = True

        if "timestamp" not in df_copy.columns:
            if "timestamp" in original_index.names:
                df_copy["timestamp"] = original_index.get_level_values("timestamp")
                added_timestamp = True
            elif isinstance(original_index, pd_module.DatetimeIndex):
                df_copy["timestamp"] = original_index
                added_timestamp = True

        # Assign a simple RangeIndex to completely avoid index level vs column label ambiguity
        df_copy.index = pd_module.RangeIndex(len(df_copy))

        # Join on index or keys (symbol, timestamp)
        # Create helper matching key combinations
        has_symbol_col = "symbol" in df_copy.columns and "symbol" in self.values.columns
        has_timestamp_col = (
            "timestamp" in df_copy.columns and "timestamp" in self.values.columns
        )

        # Determine column conflict policy
        contract = self.manifest.output_contract if self.manifest else {}
        conflict_policy = contract.get("column_conflict_policy", "fail")
        conflict_suffix = contract.get("conflict_suffix", "_indicator")

        # Ensure index matching if columns not available
        if not (has_symbol_col or has_timestamp_col):
            # Positional index alignment if indexes match exactly
            for col in self.output_columns:
                target_col = col
                if col in df_copy.columns:
                    if conflict_policy == "fail":
                        from app.services.indicators.errors import (
                            OutputColumnConflictError,
                        )

                        msg = f"Column collision: {col} already exists in source."
                        raise OutputColumnConflictError(msg)
                    if conflict_policy == "overwrite":
                        df_copy = df_copy.drop(columns=[col])
                    elif conflict_policy == "suffix":
                        target_col = col + conflict_suffix
                df_copy[target_col] = self.values[col]
            return df_copy

        # Merge based on timestamp/symbol columns
        merge_keys = []
        if has_symbol_col:
            merge_keys.append("symbol")
        if has_timestamp_col:
            merge_keys.append("timestamp")

        # Resolve output columns to keep and merge keys
        columns_to_merge = []
        renamed_columns: dict[str, str] = {}

        for col in self.output_columns:
            target_col = col
            if col in df_copy.columns:
                if conflict_policy == "fail":
                    from app.services.indicators.errors import OutputColumnConflictError

                    msg = f"Column collision: {col} already exists in source."
                    raise OutputColumnConflictError(msg)
                if conflict_policy == "overwrite":
                    df_copy = df_copy.drop(columns=[col])
                elif conflict_policy == "suffix":
                    target_col = col + conflict_suffix
                    renamed_columns[col] = target_col
            columns_to_merge.append(target_col)

        # Subset values to avoid duplicating other columns
        cols_to_extract = list(self.output_columns)
        if (
            "available_at" in self.values.columns
            and "available_at" not in df_copy.columns
        ):
            cols_to_extract.append("available_at")
        if "quality" in self.values.columns and "quality" not in df_copy.columns:
            cols_to_extract.append("quality")

        subset_values = self.values[merge_keys + cols_to_extract].copy()
        if renamed_columns:
            subset_values = subset_values.rename(columns=renamed_columns)

        subset_values.index = pd_module.RangeIndex(len(subset_values))

        result = pd_module.merge(df_copy, subset_values, on=merge_keys, how="left")
        # Ensure row ordering and index are preserved
        result.index = original_index

        # Clean up temporary columns that were added
        if added_symbol:
            result = result.drop(columns=["symbol"])
        if added_timestamp:
            result = result.drop(columns=["timestamp"])

        return result

    @property
    def values_only(self) -> pd.DataFrame:
        """Return indicator columns and alignment columns without price values."""
        key_cols = []
        if "timestamp" in self.values.columns:
            key_cols.append("timestamp")
        if "symbol" in self.values.columns:
            key_cols.append("symbol")
        meta_cols = []
        if "available_at" in self.values.columns:
            meta_cols.append("available_at")
        if "quality" in self.values.columns:
            meta_cols.append("quality")
        return self.values[key_cols + self.output_columns + meta_cols]

    def _repr_html_(self) -> str:
        """HTML representation for Jupyter notebooks."""
        manifest = self.manifest
        # Safely compute summary stats for numeric output columns only
        numeric_cols = [
            col
            for col in self.output_columns
            if col in self.values.columns
            and pd.api.types.is_numeric_dtype(self.values[col])
        ]
        if numeric_cols:
            summary_df = self.values[numeric_cols].describe()
            html_summary = summary_df.to_html()
        else:
            html_summary = "<p>No numeric indicator values computed.</p>"

        # Safe NaN checks for indicator output columns
        valid_cols = [col for col in self.output_columns if col in self.values.columns]
        if valid_cols:
            warmup_rows = self.values[self.values[valid_cols].isna().any(axis=1)]
            warmup_count = len(warmup_rows)
        else:
            warmup_count = 0
        avail_count = len(self.values) - warmup_count

        return f"""
        <div style="border: 1px solid #ccc; padding: 15px; border-radius: 5px; font-family: sans-serif; max-width: 600px;">
            <h3 style="margin-top: 0; color: #1f77b4;">Indicator Result: {manifest.indicator_id.upper()} (v{manifest.indicator_version})</h3>
            <p><b>Parameter Hash:</b> {manifest.parameter_hash or "N/A"}</p>
            <p><b>Execution Time:</b> {manifest.timing.get("wall_clock_duration_ms", 0.0):.2f} ms</p>
            <p><b>Data Coverage:</b> {len(self.values)} total rows ({warmup_count} warmup/null, {avail_count} computed)</p>
            <h4 style="color: #2ca02c; margin-bottom: 5px;">Summary Statistics</h4>
            {html_summary}
        </div>
        """

    def _repr_pretty_(self, p: Any, cycle: bool) -> None:
        """Pretty text representation for notebook/console output."""
        if cycle:
            p.text("IndicatorResult(...)")
            return
        manifest = self.manifest
        numeric_cols = [
            col
            for col in self.output_columns
            if col in self.values.columns
            and pd.api.types.is_numeric_dtype(self.values[col])
        ]
        summary_str = ""
        if numeric_cols:
            summary_str = f"\nSummary Stats:\n{self.values[numeric_cols].describe()}"

        valid_cols = [col for col in self.output_columns if col in self.values.columns]
        warmup_count = (
            self.values[valid_cols].isna().any(axis=1).sum() if valid_cols else 0
        )
        p.text(
            f"IndicatorResult: {manifest.indicator_id.upper()} (v{manifest.indicator_version})\n"
            f"Parameter Hash: {manifest.parameter_hash or 'N/A'}\n"
            f"Execution Time: {manifest.timing.get('wall_clock_duration_ms', 0.0):.2f} ms\n"
            f"Total rows: {len(self.values)} (Warmup: {warmup_count}){summary_str}"
        )


@dataclass(frozen=True)
class WarmupRequirement:
    """Contextual descriptor outlining required historical bars for warmup.

    Attributes:
        symbol: Target ticker symbol.
        timeframe: Required interval timeframe.
        lookback_bars: Number of rows needed before first valid value.
    """

    symbol: str
    timeframe: str
    lookback_bars: int


@dataclass(frozen=True)
class IndicatorState:
    """State snapshot descriptor for incremental indicators.

    Attributes:
        indicator_id: ID of the state owner.
        last_processed_timestamp: Epoch timestamp or datetime string.
        last_processed_symbol: Ticker symbol.
        accumulators: Intermediate rolling state calculations.
        warmup_completed: True if warmup phase has elapsed.
        state_schema_version: Format classification code.
    """

    indicator_id: str
    last_processed_timestamp: str | datetime | None = None
    last_processed_symbol: str | None = None
    accumulators: dict[str, Any] = field(default_factory=dict)
    warmup_completed: bool = False
    state_schema_version: str = "1.0.0"
    implementation_version: str = ""
    parameter_hash: str = ""
    input_checksum: str = ""


@runtime_checkable
class IndicatorProtocol(Protocol):
    """Typing protocol representing the structural contract for all indicators."""

    @property
    def indicator_id(self) -> str:
        """Unique key mapping this indicator definition."""
        ...

    @property
    def name(self) -> str:
        """Display name of the indicator formula."""
        ...

    @property
    def version(self) -> str:
        """Version indicator for formula behavior mapping."""
        ...

    @property
    def formula_version(self) -> str:
        """Mathematical formula specification version mapping."""
        ...

    def validate_parameters(self, parameters: dict[str, Any]) -> None:
        """Validate input parameters before calculation runs.

        Raises:
            ValidationError: If configuration boundaries are crossed.
        """
        ...

    def required_columns(self, parameters: dict[str, Any]) -> list[str]:
        """Return the column keys needed from target dataset (e.g. ['close'])."""
        ...

    def output_columns(
        self,
        parameters: dict[str, Any],
        source: str | None = None,
        naming_policy: str | None = None,
    ) -> list[str]:
        """Determine resulting output column names."""
        ...

    def warmup_requirement(
        self,
        parameters: dict[str, Any],
        timeframe: str,
        calendar: str | None = None,
    ) -> WarmupRequirement:
        """Define row lookback boundaries for initial value calculation."""
        ...

    def validate_input(
        self,
        data: pd.DataFrame,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> None:
        """Verify inputs match schema expectations and timestamp rules.

        Raises:
            ValidationError: If input quality is insufficient.
        """
        ...

    def calculate(
        self,
        data: pd.DataFrame,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> IndicatorResult:
        """Execute calculations and return standardized aligned results."""
        ...

    def update(
        self,
        bar: dict[str, Any],
        state: IndicatorState,
        config: IndicatorConfig,
        context: IndicatorContext | None = None,
    ) -> tuple[IndicatorResult, IndicatorState]:
        """Incremental accumulator update for late-arriving and streaming bars."""
        ...

    def serialize_state(self, state: IndicatorState) -> str:
        """Serialize state object to string schema."""
        ...

    def deserialize_state(self, payload: str) -> IndicatorState:
        """Restore state object from string schema."""
        ...
