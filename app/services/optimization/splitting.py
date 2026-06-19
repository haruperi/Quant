"""Optimization walk-forward and chronological time-series splitting.

Provides rolling, anchored, and expanding time-series split generators,
with support for purging overlapping trades and embargo windows.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.services.optimization.models import SplitterResult, WalkForwardWindow


class WalkForwardSplit:
    """Configures and runs walk-forward split generation.

    Args:
        start_date: Start date boundary.
        end_date: End date boundary.
        folds: Number of time-series folds.
        train_fraction: Training allocation fraction (0-1).
        fold_mode: Split mode ('rolling', 'anchored', 'expanding').
        purging_bars: Overlap purge window in bars.
        embargo_bars: Embargo window in bars.
    """

    def __init__(
        self,
        start_date: datetime | str,
        end_date: datetime | str,
        folds: int = 5,
        train_fraction: float = 0.7,
        fold_mode: str = "rolling",
        purging_bars: int = 0,
        embargo_bars: int = 0,
    ) -> None:
        """Initialize split configuration."""
        self.start_date = (
            datetime.fromisoformat(start_date)
            if isinstance(start_date, str)
            else start_date
        )
        self.end_date = (
            datetime.fromisoformat(end_date) if isinstance(end_date, str) else end_date
        )
        self.folds = folds
        self.train_fraction = train_fraction
        self.fold_mode = fold_mode.strip().lower()
        self.purging_bars = purging_bars
        self.embargo_bars = embargo_bars

    def split(self) -> SplitterResult:
        """Generate time-series split windows.

        Returns:
            SplitterResult: Generated train/test windows.
        """
        if self.fold_mode in {"expanding", "anchored"}:
            folds_list = expanding_window_split(
                self.start_date,
                self.end_date,
                self.folds,
                self.train_fraction,
                self.purging_bars,
                self.embargo_bars,
            )
        else:
            folds_list = rolling_window_split(
                self.start_date,
                self.end_date,
                self.folds,
                self.train_fraction,
                self.purging_bars,
                self.embargo_bars,
            )
        return SplitterResult(folds=folds_list)


def chronological_split(
    start: datetime | str,
    end: datetime | str,
    train_fraction: float = 0.7,
) -> tuple[WalkForwardWindow, ...]:
    """Create a single train-test split window.

    Args:
        start: Start date.
        end: End date.
        train_fraction: Fraction allocated to training.

    Returns:
        tuple[WalkForwardWindow, ...]: Tuple containing the single split window.
    """
    dt_start = datetime.fromisoformat(start) if isinstance(start, str) else start
    dt_end = datetime.fromisoformat(end) if isinstance(end, str) else end
    total_sec = (dt_end - dt_start).total_seconds()
    train_end = dt_start + timedelta(seconds=total_sec * train_fraction)

    return (
        WalkForwardWindow(
            train_start=dt_start.isoformat(),
            train_end=train_end.isoformat(),
            test_start=train_end.isoformat(),
            test_end=dt_end.isoformat(),
        ),
    )


def rolling_window_split(
    start: datetime,
    end: datetime,
    folds: int = 5,
    train_fraction: float = 0.7,
    purging_bars: int = 0,
    embargo_bars: int = 0,
) -> list[WalkForwardWindow]:
    """Create deterministic rolling time-series train/test windows.

    Args:
        start: Start date boundary.
        end: End date boundary.
        folds: Folds count.
        train_fraction: Sizing fraction.
        purging_bars: purges overlap in bars.
        embargo_bars: embargo period in bars.

    Returns:
        list[WalkForwardWindow]: List of splits.
    """
    total_seconds = (end - start).total_seconds()
    step_seconds = total_seconds / (folds + 1)
    windows = []
    for i in range(folds):
        fold_start = start + timedelta(seconds=i * step_seconds)
        fold_end = start + timedelta(seconds=(i + 2) * step_seconds)

        train_duration = (fold_end - fold_start).total_seconds() * train_fraction
        train_end = fold_start + timedelta(seconds=train_duration)

        # Apply embargo and purging bounds
        # purging shifts train_end backward to avoid overlap leakage
        purged_train_end = train_end - timedelta(minutes=purging_bars)
        if purged_train_end <= fold_start:
            purged_train_end = train_end

        # embargo shifts test_start forward to avoid correlation leakage
        test_start = train_end + timedelta(minutes=embargo_bars)
        test_end = fold_end

        if test_start >= test_end:
            test_start = train_end

        windows.append(
            WalkForwardWindow(
                train_start=fold_start.isoformat(),
                train_end=purged_train_end.isoformat(),
                test_start=test_start.isoformat(),
                test_end=test_end.isoformat(),
            )
        )
    return windows


def expanding_window_split(
    start: datetime,
    end: datetime,
    folds: int = 5,
    train_fraction: float = 0.7,
    purging_bars: int = 0,
    embargo_bars: int = 0,
) -> list[WalkForwardWindow]:
    """Create deterministic expanding time-series train/test windows.

    Args:
        start: Start date.
        end: End date.
        folds: Folds count.
        train_fraction: Training split fraction.
        purging_bars: Purge bars.
        embargo_bars: Embargo bars.

    Returns:
        list[WalkForwardWindow]: List of splits.
    """
    total_seconds = (end - start).total_seconds()
    step_seconds = total_seconds / (folds + 1)
    windows = []
    for i in range(folds):
        fold_start = start
        fold_end = start + timedelta(seconds=(i + 2) * step_seconds)

        train_duration = (fold_end - fold_start).total_seconds() * train_fraction
        train_end = fold_start + timedelta(seconds=train_duration)

        # Apply purging and embargo
        purged_train_end = train_end - timedelta(minutes=purging_bars)
        if purged_train_end <= fold_start:
            purged_train_end = train_end

        test_start = train_end + timedelta(minutes=embargo_bars)
        test_end = fold_end

        if test_start >= test_end:
            test_start = train_end

        windows.append(
            WalkForwardWindow(
                train_start=fold_start.isoformat(),
                train_end=purged_train_end.isoformat(),
                test_start=test_start.isoformat(),
                test_end=test_end.isoformat(),
            )
        )
    return windows


def splitter_from_rolling(
    start: str,
    end: str,
    folds: int = 5,
    train_fraction: float = 0.7,
    purging_bars: int = 0,
    embargo_bars: int = 0,
) -> SplitterResult:
    """Create deterministic rolling time-series train/test windows.

    Args:
        start: ISO start date.
        end: ISO end date.
        folds: Number of folds.
        train_fraction: Training fraction allocation.
        purging_bars: Bars count for purging.
        embargo_bars: Bars count for embargo.

    Returns:
        SplitterResult: Generated windows envelope.
    """
    dt_start = datetime.fromisoformat(start)
    dt_end = datetime.fromisoformat(end)
    folds_list = rolling_window_split(
        dt_start, dt_end, folds, train_fraction, purging_bars, embargo_bars
    )
    return SplitterResult(folds=folds_list)


def splitter_from_expanding(
    start: str,
    end: str,
    folds: int = 5,
    train_fraction: float = 0.7,
    purging_bars: int = 0,
    embargo_bars: int = 0,
) -> SplitterResult:
    """Create expanding time-series train/test windows.

    Args:
        start: ISO start.
        end: ISO end.
        folds: Number of folds.
        train_fraction: Training fraction allocation.
        purging_bars: Bars count for purging.
        embargo_bars: Bars count for embargo.

    Returns:
        SplitterResult: Generated expanding windows.
    """
    dt_start = datetime.fromisoformat(start)
    dt_end = datetime.fromisoformat(end)
    folds_list = expanding_window_split(
        dt_start, dt_end, folds, train_fraction, purging_bars, embargo_bars
    )
    return SplitterResult(folds=folds_list)


def splitter_rolling_split(
    data: Any,  # noqa: ANN401
    train_fraction: float = 0.7,
) -> tuple[Any, Any]:
    """Split tabular data into rolling train/test or train/validation/test slices.

    Args:
        data: Tabular list or pandas DataFrame.
        train_fraction: Sizing fraction.

    Returns:
        tuple[Any, Any]: Train and test slices.
    """
    if hasattr(data, "iloc"):
        split_idx = int(len(data) * train_fraction)
        return data.iloc[:split_idx], data.iloc[split_idx:]
    split_idx = int(len(data) * train_fraction)
    return data[:split_idx], data[split_idx:]
