# ruff: noqa: E501, ANN401
"""Data leakage checks and chronological splitting for Research Edge Lab.

This module provides tools to detect forward-looking bias (lookahead bias) and
enforce chronological splits.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from app.utils.errors import ValidationError
from app.utils.security import redact_mapping


class LeakageReport(BaseModel):
    """Defines suspected columns, severity, evidence, recommendations, and metadata."""

    suspected_columns: list[str] = Field(default_factory=list)
    severity: str = "clean"  # "clean", "warning", "critical"
    evidence: list[str] = Field(default_factory=list)
    recommendation: str = ""
    allowed_forward_columns: list[str] = Field(default_factory=list)
    target_column: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# Alias LeakageCheckResult to LeakageReport
LeakageCheckResult = LeakageReport


def validate_no_lookahead_features(
    df: pd.DataFrame,
    allowed_forward_columns: list[str] | None = None,
    target_column: str | None = None,
) -> LeakageReport:
    """Inspect DataFrame columns for lookahead bias without mutating the input frame.

    Args:
        df: The feature DataFrame to inspect.
        allowed_forward_columns: List of columns containing future targets that are allowed.
        target_column: The main target column name.

    Returns:
        LeakageReport: Report summarizing suspected lookahead columns.
    """
    if allowed_forward_columns is None:
        allowed_forward_columns = []

    suspected = []
    evidence = []
    recommendation = "Remove lookahead columns or label them correctly."

    # Look for forward-looking indicators in column names
    lookahead_keywords = {"forward", "future", "lookahead", "lead", "research_"}

    for col in df.columns:
        col_str = str(col)
        # Skip allowed columns
        if col_str in allowed_forward_columns:
            continue

        # Check if the column name contains lookahead keywords
        if any(kw in col_str.lower() for kw in lookahead_keywords):
            suspected.append(col_str)
            evidence.append(
                f"Column '{col_str}' name contains lookahead-associated keywords."
            )

    severity = "clean"
    if suspected:
        severity = "critical"
        recommendation = f"Drop suspected columns {suspected} before model training."

    return LeakageReport(
        suspected_columns=suspected,
        severity=severity,
        evidence=evidence,
        recommendation=recommendation,
        allowed_forward_columns=allowed_forward_columns,
        target_column=target_column,
        metadata={"total_columns": len(df.columns)},
    )


def validate_no_lookahead(
    df: pd.DataFrame,
    allowed_forward_columns: list[str] | None = None,
    target_column: str | None = None,
) -> LeakageReport:
    """Wrapper for validate_no_lookahead_features."""
    return validate_no_lookahead_features(
        df,
        allowed_forward_columns=allowed_forward_columns,
        target_column=target_column,
    )


def detect_feature_leakage(
    df: pd.DataFrame,
    allowed_forward_columns: list[str] | None = None,
    target_column: str | None = None,
) -> LeakageReport:
    """Wrapper for validate_no_lookahead_features."""
    return validate_no_lookahead_features(
        df,
        allowed_forward_columns=allowed_forward_columns,
        target_column=target_column,
    )


def mask_forward_columns(df: pd.DataFrame, report: LeakageReport) -> pd.DataFrame:
    """Return a copy of the DataFrame with suspected lookahead columns dropped.

    Args:
        df: Input DataFrame.
        report: The leakage report containing suspected columns.

    Returns:
        pd.DataFrame: A copy of the DataFrame without lookahead columns.
    """
    df = df.copy()
    to_drop = [c for c in report.suspected_columns if c in df.columns]
    return df.drop(columns=to_drop)


class TimeSplitResult:
    """Represents deterministic chronological train, validation, and test partitions."""

    def __init__(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame,
        test_df: pd.DataFrame,
    ) -> None:
        """Initialize the chronological time split result."""
        self.train_df = train_df
        self.val_df = val_df
        self.test_df = test_df
        self.train_records = len(train_df)
        self.val_records = len(val_df)
        self.test_records = len(test_df)

    def to_dict(self) -> dict[str, int]:
        """Return counts of splits."""
        return {
            "train_records": self.train_records,
            "val_records": self.val_records,
            "test_records": self.test_records,
        }


def enforce_time_split(
    df: pd.DataFrame,
    train_pct: float = 0.6,
    val_pct: float = 0.2,
    test_pct: float = 0.2,
) -> TimeSplitResult:
    """Enforce chronological train, validation, and test splits without overlap.

    Args:
        df: Market data DataFrame.
        train_pct: Fraction of data to use for training.
        val_pct: Fraction of data to use for validation.
        test_pct: Fraction of data to use for testing.

    Returns:
        TimeSplitResult: Object containing the chronological splits.
    """
    if not np.isclose(train_pct + val_pct + test_pct, 1.0):
        raise ValidationError(
            "Split percentages must sum to 1.0.",
            code="INVALID_INPUT",
        )

    # Sort index to ensure chronological splits
    df = df.sort_index()
    n = len(df)
    train_end = int(n * train_pct)
    val_end = train_end + int(n * val_pct)

    train_df = df.iloc[:train_end]
    val_df = df.iloc[train_end:val_end]
    test_df = df.iloc[val_end:]

    return TimeSplitResult(train_df, val_df, test_df)


def mask_research_artifact(artifact: dict[str, Any]) -> dict[str, Any]:
    """Remove or redact sensitive fields from research artifacts before persistence or sharing."""
    # Recursively redact credentials, keys, or passwords
    return redact_mapping(artifact)


def dump_masked_research_json(artifact: dict[str, Any]) -> str:
    """Serialize a masked research artifact to JSON."""
    masked = mask_research_artifact(artifact)

    class CustomEncoder(json.JSONEncoder):
        def default(self, o: Any) -> Any:
            if hasattr(o, "isoformat"):
                return o.isoformat()
            if hasattr(o, "to_dict"):
                return o.to_dict()
            return super().default(o)

    return json.dumps(masked, cls=CustomEncoder, indent=2)
