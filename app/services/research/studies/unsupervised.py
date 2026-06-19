# ruff: noqa: E501, PLR2004, EM102
"""Unsupervised learning and dimensionality reduction service for Research Edge Lab.

Provides PCA, K-Means clustering, and outperformance analysis for market regime detection.
"""

from __future__ import annotations

import datetime
from typing import Any

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from app.utils.errors import ValidationError


class UnsupervisedResearchRequest(BaseModel):
    """Represents one unsupervised research request."""

    feature_columns: list[str]
    n_components: int = 2
    n_clusters: int = 3
    seed: int = 42


class UnsupervisedResearchResult(BaseModel):
    """Represents a complete unsupervised research result."""

    pca_explained_variance: list[float]
    cluster_centers: list[list[float]]
    silhouette_score: float = 0.0
    seed: int
    metadata: dict[str, Any] = Field(default_factory=dict)


def run_pca(df: pd.DataFrame, n_components: int = 2) -> dict[str, Any]:
    """Run PCA on numeric feature columns and return component scores and loadings."""
    # Standardize data
    numeric_df = df.select_dtypes(include=[np.number]).dropna()
    if len(numeric_df) < n_components or numeric_df.empty:
        raise ValidationError(
            "Insufficient data for PCA calculation.",
            code="INVALID_INPUT",
        )

    try:
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        raise ValidationError(
            "scikit-learn is required for PCA calculations.",
            code="SERVICE_UNAVAILABLE",
        ) from exc

    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(numeric_df)

    pca = PCA(n_components=n_components, random_state=42)
    pca.fit(scaled_data)

    loadings = pca.components_
    explained_variance = pca.explained_variance_ratio_

    return {
        "explained_variance": [float(x) for x in explained_variance],
        "loadings": [[float(val) for val in row] for row in loadings],
        "columns": list(numeric_df.columns),
    }


def cluster_feature_space(
    df: pd.DataFrame,
    n_clusters: int = 3,
    seed: int = 42,
) -> dict[str, Any]:
    """Cluster numeric feature rows using K-Means."""
    numeric_df = df.select_dtypes(include=[np.number]).dropna()
    if len(numeric_df) < n_clusters or numeric_df.empty:
        raise ValidationError(
            "Insufficient data for clustering.",
            code="INVALID_INPUT",
        )

    try:
        from sklearn.cluster import KMeans
        from sklearn.preprocessing import StandardScaler
    except ImportError as exc:
        raise ValidationError(
            "scikit-learn is required for K-Means clustering.",
            code="SERVICE_UNAVAILABLE",
        ) from exc

    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(numeric_df)

    kmeans = KMeans(n_clusters=n_clusters, random_state=seed, n_init=10)
    kmeans.fit(scaled_data)

    labels = kmeans.labels_
    centers = kmeans.cluster_centers_

    return {
        "labels": labels.tolist(),
        "cluster_centers": [[float(val) for val in row] for row in centers],
        "scaler_mean": scaler.mean_.tolist(),
        "scaler_scale": scaler.scale_.tolist(),
        "seed": seed,
        "columns": list(numeric_df.columns),
    }


def attach_cluster_labels(
    df: pd.DataFrame, labels: np.ndarray | list[int]
) -> pd.DataFrame:
    """Attach cluster labels to a feature frame without mutating the input."""
    df = df.copy()
    df["cluster"] = labels
    return df


def identify_pca_risk_factors(
    pca_results: dict[str, Any],
    columns: list[str],
) -> list[dict[str, Any]]:
    """Extract the largest PCA loadings as interpretable risk factors."""
    loadings = pca_results.get("loadings", [])
    factors = []
    for idx, component_loading in enumerate(loadings):
        # Find absolute max loading index
        max_idx = int(np.argmax(np.abs(component_loading)))
        factors.append(
            {
                "component": idx,
                "primary_column": columns[max_idx],
                "loading_value": float(component_loading[max_idx]),
            }
        )
    return factors


def compute_forward_returns(close: pd.Series, horizon: int = 5) -> pd.Series:
    """Compute horizon-aligned forward returns from a price column."""
    if horizon <= 0:
        raise ValidationError("Horizon must be positive.", code="INVALID_INPUT")
    return np.log(close.shift(-horizon) / close)


def analyze_cluster_outperformance(
    df: pd.DataFrame,
    labels: list[int] | np.ndarray,
    forward_returns_col: str = "research_forward_returns",
) -> dict[int, dict[str, Any]]:
    """Score clusters by future returns and assign semantic regime names."""
    df = df.copy()
    df["cluster"] = labels
    if forward_returns_col not in df.columns:
        raise ValidationError(
            f"Forward returns column '{forward_returns_col}' not found in DataFrame.",
            code="INVALID_INPUT",
        )

    cluster_stats = {}
    for cluster_id, group in df.groupby("cluster"):
        fwd_ret = group[forward_returns_col].dropna()
        mean_ret = float(fwd_ret.mean()) if not fwd_ret.empty else 0.0
        # Assign semantic regime
        if mean_ret > 0.0002:
            regime = "High Growth"
        elif mean_ret < -0.0002:
            regime = "Contraction"
        else:
            regime = "Sideways Stable"

        cluster_stats[int(cluster_id)] = {
            "mean_forward_return": mean_ret,
            "sample_size": len(fwd_ret),
            "regime_name": regime,
        }

    return cluster_stats


def adapt_signals_by_cluster(
    cluster_performance: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    """Produce advisory signal-adaptation recommendations identifying clusters where forward-return evidence is weak.

    This does not mutate strategy runtime state, block live entries, or authorize execution changes.
    """
    recommendations = {}
    for cid, stats in cluster_performance.items():
        mean_ret = stats["mean_forward_return"]
        if mean_ret < -0.0001:
            recommendations[str(cid)] = {
                "action": "reduce_exposure_advisory",
                "reason": f"Weak or negative historical forward return ({mean_ret:.5f}) in cluster.",
            }
        else:
            recommendations[str(cid)] = {
                "action": "maintain_exposure_advisory",
                "reason": "Stable return profile.",
            }

    return {
        "recommendations": recommendations,
        "status": "advisory_only",
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
    }


def build_unsupervised_insight_report(
    symbol: str,
    timeframe: str,
    pca_results: dict[str, Any],
    cluster_results: dict[str, Any],
) -> dict[str, Any]:
    """Build a complete unsupervised insight report for trading workflows."""
    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "pca_variance": pca_results.get("explained_variance", []),
        "cluster_centers": cluster_results.get("cluster_centers", []),
        "created_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "disclaimer": "Advisory unsupervised insight report.",
    }
