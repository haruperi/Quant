"""Unit tests for dataframe utility helpers."""

from __future__ import annotations

import math
from collections.abc import Iterator
from datetime import UTC, datetime

import pytest
from tools.utils import (
    align_dataframe_datetime,
    bar_to_record,
    chunked,
    compare_dataframes,
    compare_ohlc,
    compare_ohlcv,
    dataframe_columns,
    dataframe_tools,
    iter_dataframe_records,
    parameter_combinations,
    serialize_dataframe_records,
)
from tools.utils.errors import ConfigurationError, ValidationError


class FakeSeries(list[object]):
    """Tiny list-backed series for dataframe tests."""


class FakeTimestamp:
    """Placeholder timestamp type for ``isinstance`` checks."""


class FakeIndex(list[object]):
    """Tiny index with pandas-like equality."""

    @property
    def empty(self) -> bool:
        """Return whether index is empty."""
        return len(self) == 0

    def equals(self, other: object) -> bool:
        """Return whether indexes are equal."""
        return isinstance(other, FakeIndex) and list(self) == list(other)


class FakeRow:
    """Tiny row wrapper."""

    def __init__(self, row: dict[str, object]) -> None:
        self.row = row

    def to_dict(self) -> dict[str, object]:
        """Return row mapping."""
        return dict(self.row)

    def __getitem__(self, column: str) -> object:
        """Return one column value."""
        return self.row[column]


class FakeAt:
    """Tiny ``.at`` indexer."""

    def __init__(self, frame: FakeDataFrame) -> None:
        self.frame = frame

    def __getitem__(self, key: tuple[int, str]) -> object:
        """Return a scalar by row index and column."""
        row_index, column = key
        return self.frame.rows[row_index][column]


class FakeDataFrame:
    """Tiny DataFrame double with only methods used by the helpers."""

    def __init__(self, rows: list[dict[str, object]]) -> None:
        self.rows = [dict(row) for row in rows]
        self.index = FakeIndex(range(len(rows)))
        self.at = FakeAt(self)

    @property
    def empty(self) -> bool:
        """Return whether the frame is empty."""
        return not self.rows

    @property
    def columns(self) -> list[str]:
        """Return column names in insertion order."""
        return list(self.rows[0]) if self.rows else []

    def copy(self, *, deep: bool = True) -> FakeDataFrame:  # noqa: ARG002
        """Return a copied frame."""
        copied = FakeDataFrame(self.rows)
        copied.index = FakeIndex(self.index)
        return copied

    def __getitem__(self, column: str) -> FakeSeries:
        """Return a column as a fake series."""
        return FakeSeries(row[column] for row in self.rows)

    def __setitem__(self, column: str, values: list[object]) -> None:
        """Set a column from a list of values."""
        for row, value in zip(self.rows, values, strict=True):
            row[column] = value

    def __len__(self) -> int:
        """Return row count."""
        return len(self.rows)

    def to_dict(self, *, orient: str) -> list[dict[str, object]]:
        """Return record dictionaries."""
        assert orient == "records"
        return [dict(row) for row in self.rows]

    def iterrows(self) -> Iterator[tuple[int, FakeRow]]:
        """Yield row index and fake row pairs."""
        for index, row in enumerate(self.rows):
            yield index, FakeRow(row)

    def equals(self, other: object) -> bool:
        """Return whether two fake frames contain the same rows."""
        return isinstance(other, FakeDataFrame) and self.rows == other.rows


class FakePandas:
    """Tiny pandas module double."""

    DataFrame = FakeDataFrame
    Timestamp = FakeTimestamp

    @staticmethod
    def isna(value: object) -> bool:
        """Return whether a value is missing."""
        return value is None

    @staticmethod
    def notna(value: object) -> bool:
        """Return whether a value is present."""
        return value is not None

    @staticmethod
    def DatetimeIndex(values: list[object]) -> FakeIndex:  # noqa: N802
        """Return values as a fake datetime index."""
        return FakeIndex(values)

    @staticmethod
    def to_datetime(
        values: list[object],
        *,
        utc: bool,
        errors: str,
    ) -> list[object]:
        """Return values unchanged for tests."""
        assert utc is True
        assert errors == "raise"
        return values


def _patch_pandas() -> None:
    """Patch dataframe helpers to use the fake pandas module."""
    dataframe_tools._pandas = lambda: FakePandas


def test_dataframe_helpers_serialize_without_mutating() -> None:
    """Dataframe helpers return deterministic records and preserve input."""
    _patch_pandas()
    frame = FakeDataFrame(
        [
            {
                "timestamp": "2026-06-11T10:00:00Z",
                "open": 1.0,
                "high": 1.2,
                "low": 0.9,
                "close": 1.1,
                "volume": 10,
            },
        ],
    )
    aligned = align_dataframe_datetime(frame, timestamp_column="timestamp")

    assert frame.rows[0]["timestamp"] == "2026-06-11T10:00:00Z"
    assert dataframe_columns(aligned) == [
        "timestamp",
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]
    timestamp = serialize_dataframe_records(aligned)[0]["timestamp"]
    assert isinstance(timestamp, str)
    assert timestamp.endswith("Z")
    assert next(iter(iter_dataframe_records(aligned)))["close"] == 1.1


def test_dataframe_comparison_and_combinatorics() -> None:
    """Comparison, chunking, and grids are deterministic."""
    _patch_pandas()
    left = FakeDataFrame(
        [{"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 1}],
    )
    right = FakeDataFrame(
        [{"open": 1.0, "high": 2.1, "low": 0.5, "close": 1.5, "volume": 1}],
    )

    assert compare_ohlcv(left, left)["equal"] is True
    assert compare_ohlcv(left, right)["equal"] is False
    assert chunked([1, 2, 3], size=2) == [[1, 2], [3]]
    assert parameter_combinations({"a": [1, 2], "b": ["x"]}) == [
        {"a": 1, "b": "x"},
        {"a": 2, "b": "x"},
    ]
    assert bar_to_record({"open": 1, "close": 2}) == {"close": 2, "open": 1}


def test_dataframe_helpers_reject_invalid_inputs() -> None:
    """Dataframe helpers raise deterministic validation errors."""
    _patch_pandas()
    frame = FakeDataFrame([{"open": 1.0, "high": 2.0}])
    other = FakeDataFrame([{"open": 1.0, "high": 2.0}])
    other.index = FakeIndex([99])

    with pytest.raises(ValidationError, match="DataFrame"):
        dataframe_columns(object())
    with pytest.raises(ValidationError, match="missing required columns"):
        align_dataframe_datetime(frame, timestamp_column="timestamp")
    with pytest.raises(ValidationError, match="greater than zero"):
        chunked([1, 2], size=0)
    with pytest.raises(ValidationError, match="non-empty sequence"):
        parameter_combinations({"fast": []})
    with pytest.raises(ValidationError, match="non-negative"):
        compare_dataframes(frame, frame, tolerance=-0.1)
    with pytest.raises(ValidationError, match="indexes do not align"):
        compare_dataframes(frame, other)
    with pytest.raises(ValidationError, match="bar must be a mapping"):
        bar_to_record(["not", "mapping"])  # type: ignore[arg-type]


def test_dataframe_serialization_handles_index_dates_and_nonfinite_values() -> None:
    """Serialization converts date-like and non-finite values into JSON-safe data."""
    _patch_pandas()
    timestamp = datetime(2026, 6, 11, 10, 0, tzinfo=UTC)
    frame = FakeDataFrame(
        [
            {
                "timestamp": timestamp,
                "nested": {"bad": math.inf},
                "items": [1, math.nan],
                "open": 1.0,
            },
        ],
    )

    records = serialize_dataframe_records(
        frame,
        timestamp_columns=("timestamp",),
        include_index=True,
        index_name="row",
    )
    bar = bar_to_record({"timestamp": timestamp, "value": math.nan})

    assert records == [
        {
            "timestamp": "2026-06-11T10:00:00Z",
            "nested": {"bad": None},
            "items": [1, None],
            "open": 1.0,
            "row": 0,
        },
    ]
    assert bar["timestamp"] == "2026-06-11T10:00:00Z"
    assert bar["value"] is None


def test_dataframe_comparison_tolerance_and_nan_handling() -> None:
    """Comparison supports OHLC subsets, tolerance, and NaN equality."""
    _patch_pandas()
    left = FakeDataFrame(
        [{"open": 1.0, "high": 2.0, "low": 0.5, "close": math.nan, "volume": 1}],
    )
    right = FakeDataFrame(
        [{"open": 1.01, "high": 2.0, "low": 0.5, "close": math.nan, "volume": 1}],
    )

    assert compare_ohlc(left, right, tolerance=0.02)["equal"] is True
    assert compare_ohlc(left, right, tolerance=0.001)["equal"] is False


def test_pandas_import_failure_is_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lazy pandas import failures produce configuration errors."""
    import importlib

    module = importlib.reload(dataframe_tools)
    real_import = module.importlib.import_module

    def fail_for_pandas(name: str) -> object:
        if name == "pandas":
            raise ImportError("missing pandas")
        return real_import(name)

    monkeypatch.setattr(module.importlib, "import_module", fail_for_pandas)

    with pytest.raises(ConfigurationError, match="pandas is required"):
        module._pandas()
