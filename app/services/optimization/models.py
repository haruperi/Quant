"""Optimization Service data models and schemas.

This module defines all parameter-space, request, response, and scenario simulation
models used by the Optimization Service. All primary models inherit from Contract
to ensure deterministic serialization and trace propagation.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.contracts.base import Contract


class ParameterRange(BaseModel):
    """Models a single parameter optimization range.

    Args:
        name: The parameter name.
        type: The parameter type ('int', 'float', 'categorical', 'bool').
        min_value: The minimum numeric value.
        max_value: The maximum numeric value.
        step: Optional step size for search space discretization.
        options: List of allowed values for categorical parameters.
        conditional_on: Optional name of the parameter this depends on.
        conditional_values: List of values of the trigger parameter
            for this parameter to be active.
    """

    name: str = Field(..., description="Unique parameter identifier.")
    type: Literal["int", "float", "categorical", "bool"] = Field(
        ..., description="Parameter type classification."
    )
    min_value: float | None = Field(
        default=None, description="Minimum numeric boundary."
    )
    max_value: float | None = Field(
        default=None, description="Maximum numeric boundary."
    )
    step: float | None = Field(default=None, description="Optional search step size.")
    options: list[Any] | None = Field(
        default=None, description="Allowed choices for categorical type."
    )
    conditional_on: str | None = Field(
        default=None, description="Parent parameter name for conditional execution."
    )
    conditional_values: list[Any] | None = Field(
        default=None, description="Trigger parent values to activate this parameter."
    )

    @model_validator(mode="after")
    def validate_range_boundaries(self) -> ParameterRange:
        """Validate numeric range boundaries and option lists."""
        if self.type in ("int", "float"):
            if self.min_value is None or self.max_value is None:
                raise ValueError(
                    "min_value and max_value are required for numeric types."
                )
            if self.min_value > self.max_value:
                raise ValueError("min_value cannot be greater than max_value.")
        elif self.type == "categorical":
            if not self.options:
                raise ValueError(
                    "options must be provided and non-empty for categorical types."
                )
        return self


class ParameterSpace(BaseModel):
    """Defines the complete search space including constraints.

    Args:
        parameters: List of parameter range boundaries.
        constraints: Optional Python expressions validating parameter relationships.
    """

    parameters: list[ParameterRange] = Field(
        ..., description="List of search parameter definitions."
    )
    constraints: list[str] = Field(
        default_factory=list,
        description=(
            "Logical constraint expressions evaluated before candidate execution."
        ),
    )


class ParameterCandidate(BaseModel):
    """Represents a single evaluated or proposed parameter set.

    Args:
        parameters: Dictionary mapping parameter names to actual values.
        candidate_hash: Unique SHA-256 hash identifying
            the candidate parameter combination.
    """

    parameters: dict[str, Any] = Field(..., description="Parameter values mapping.")
    candidate_hash: str = Field(..., description="SHA-256 identifier.")


class OptimizationResult(BaseModel):
    """Represent one candidate optimization result.

    Args:
        parameters: The candidate parameters evaluated.
        score: The primary objective optimization score.
        metrics: Detailed metrics mapping (e.g. sharpe, drawdown, trade_count).
        metadata: Tracing or runner metadata.
    """

    parameters: dict[str, Any] = Field(..., description="Parameters evaluated.")
    score: float = Field(..., description="Objective optimization score.")
    metrics: dict[str, Any] = Field(
        ..., description="Detailed performance metric outputs."
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Runner-specific metadata."
    )


class OptimizationSummary(BaseModel):
    """Summary of the complete optimization run.

    Args:
        best_candidate: The highest-scoring parameter candidate.
        best_score: The highest score achieved in the sweep.
        objective: The name of the objective function used.
        runtime_ms: Total duration in milliseconds.
        total_candidates: Total count of candidate trials evaluated.
        candidates: Chronological or ranked list of all evaluated candidate results.
    """

    best_candidate: ParameterCandidate = Field(
        ..., description="Highest-scoring candidate."
    )
    best_score: float = Field(..., description="Highest score achieved.")
    objective: str = Field(..., description="Optimization objective name.")
    runtime_ms: float = Field(..., description="Execution time in milliseconds.")
    total_candidates: int = Field(..., description="Total trials count.")
    candidates: list[OptimizationResult] = Field(
        default_factory=list, description="List of all evaluated candidates."
    )

    def top_n(self, n: int = 10) -> list[OptimizationResult]:
        """Return the top N candidates sorted by score descending.

        Args:
            n: Number of candidates to return.

        Returns:
            List of the top N candidate results.
        """
        sorted_cands = sorted(self.candidates, key=lambda c: c.score, reverse=True)
        return sorted_cands[:n]

    def to_dataframe(self) -> Any:  # noqa: ANN401
        """Convert candidates to a pandas DataFrame.

        Returns:
            A pandas DataFrame mapping parameter values and metrics.
        """
        import pandas as pd

        records = []
        for cand in self.candidates:
            record = {
                "score": cand.score,
                **{f"param_{k}": v for k, v in cand.parameters.items()},
                **cand.metrics,
            }
            records.append(record)
        return pd.DataFrame(records)


class UnsupervisedConfigRequest(BaseModel):
    """Configuration request options for unsupervised classification/clustering.

    Args:
        method: Method name (e.g. 'kmeans', 'pca').
        n_clusters: Optional cluster count parameter.
        features: Target features list for the unsupervised model.
    """

    method: str = Field(default="kmeans", description="Unsupervised learning method.")
    n_clusters: int | None = Field(
        default=None, description="Number of target clusters."
    )
    features: list[str] = Field(
        default_factory=list, description="Target features subset."
    )


class UnsupervisedRunSummary(BaseModel):
    """Summary of unsupervised model runs attached to optimization.

    Args:
        method: The unsupervised method evaluated.
        cluster_labels: Mapping of candidate hashes to their assigned cluster IDs.
        silhouette_score: Optional model performance score.
        metadata: Run metadata.
    """

    method: str = Field(..., description="Method name.")
    cluster_labels: dict[str, int] = Field(
        ..., description="Candidate cluster assignments."
    )
    silhouette_score: float | None = Field(
        default=None, description="Cluster quality score."
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata.")


class UnsupervisedAnalysisRequest(BaseModel):
    """Request for running unsupervised clustering on optimization run results.

    Args:
        run_id: Optimization run ID.
        config: Configuration parameters.
    """

    run_id: str = Field(..., description="Associated optimization run identifier.")
    config: UnsupervisedConfigRequest = Field(
        ..., description="Model configuration parameters."
    )


class OptimizationRequest(Contract):
    """Request package for running parameter optimization sweeps.

    Args:
        strategy_ref: Strategy registration reference.
        symbols: Target symbols list.
        timeframe: Execution bar timeframe.
        start: Start Date ISO string.
        end: End Date ISO string.
        parameter_space: Define parameter boundaries.
        search_method: sweep algorithm ('grid', 'random', 'bayesian', 'genetic').
        objective: Main optimization objective (e.g. 'sharpe').
        initial_balance: Starting cash deposit balance.
        max_workers: Maximum execution concurrency.
        dry_run: Dry run execution flag.
    """

    strategy_ref: str = Field(..., description="Target strategy register name.")
    symbols: list[str] = Field(..., description="Target symbols list.")
    timeframe: str = Field(..., description="Resolution timeframe.")
    start: str = Field(..., description="ISO 8601 start date.")
    end: str = Field(..., description="ISO 8601 end date.")
    parameter_space: ParameterSpace = Field(..., description="Parameter boundaries.")
    search_method: Literal["grid", "random", "bayesian", "genetic"] = Field(
        default="grid", description="Sweep algorithm selection."
    )
    objective: str = Field(default="sharpe", description="Target objective metric.")
    initial_balance: float = Field(
        default=10000.0, description="Starting account balance."
    )
    max_workers: int = Field(default=1, description="Worker execution count.")
    dry_run: bool = Field(
        default=True, description="Lightweight dry-run execution flag."
    )


class OptimizationResultItem(BaseModel):
    """Single item returned inside public optimization response payloads.

    Args:
        candidate_hash: Unique identifier.
        parameters: Candidate parameters evaluated.
        score: Computed objective score.
        metrics: Detailed metrics.
    """

    candidate_hash: str = Field(..., description="Candidate unique hash.")
    parameters: dict[str, Any] = Field(..., description="Parameters.")
    score: float = Field(..., description="Objective score.")
    metrics: dict[str, Any] = Field(..., description="Computed backtest metrics.")


class OptimizationResponse(Contract):
    """Official envelope returned by optimization public sweep methods.

    Args:
        run_id: Target optimization run ID.
        status: Sweep status.
        message: Human-readable message.
        best_candidate: Best candidate details.
        top_candidates: List of top N results.
        metadata: Tracing and execution performance metadata.
    """

    run_id: str = Field(..., description="Unique run identifier.")
    status: Literal[
        "ready_for_risk_review",
        "validation_needed",
        "research_only",
        "rejected",
        "failed",
        "cancelled",
    ] = Field(..., description="Standard workflow status outcome.")
    message: str = Field(..., description="Execution status description.")
    best_candidate: OptimizationResultItem | None = Field(
        default=None, description="Top-performing candidate."
    )
    top_candidates: list[OptimizationResultItem] = Field(
        default_factory=list, description="Top-N results."
    )


class OptimizationRunDetails(Contract):
    """Audit details representing a single saved optimization run record."""

    run_id: str = Field(..., description="Unique run ID.")
    strategy_ref: str = Field(..., description="Strategy name.")
    parameter_space_hash: str = Field(..., description="Parameter space hash.")
    objective: str = Field(..., description="Target objective.")
    status: str = Field(..., description="Run status.")
    total_candidates: int = Field(..., description="Evaluated candidate count.")
    candidates: list[OptimizationResult] = Field(
        default_factory=list, description="Evaluated candidates."
    )


class SweepResult(BaseModel):
    """Sweep result mapping data structure."""

    run_id: str = Field(..., description="Optimization run ID.")
    summary: OptimizationSummary = Field(..., description="Execution summary metrics.")


class PositionSizingRequest(Contract):
    """Request for running position sizing simulations."""

    win_rate: float = Field(..., description="Expected win rate percentage.")
    reward_risk_ratio: float = Field(..., description="Reward-to-risk ratio.")
    risk_per_trade: float = Field(
        default=0.01, description="Fraction of balance risked per trade."
    )
    trade_count: int = Field(default=100, description="Simulated trade count.")
    simulation_count: int = Field(
        default=1000, description="Monte Carlo simulation count."
    )
    initial_balance: float = Field(
        default=10000.0, description="Starting cash deposit."
    )


class PositionSizingResult(BaseModel):
    """Results of a position sizing simulation run."""

    method: str = Field(
        ..., description="Simulation sizing method (e.g. 'linear', 'compounding')."
    )
    equity_curves: list[list[float]] = Field(
        ..., description="Simulated equity curve paths."
    )
    final_balances: list[float] = Field(..., description="Terminal account balances.")
    max_drawdowns: list[float] = Field(
        ..., description="Drawdowns experienced across paths."
    )


class WalkForwardWindow(BaseModel):
    """Represents a single train-test split window.

    Args:
        train_start: ISO 8601 start date of training set.
        train_end: ISO 8601 end date of training set.
        test_start: ISO 8601 start date of testing set.
        test_end: ISO 8601 end date of testing set.
    """

    train_start: str = Field(..., description="Train start date.")
    train_end: str = Field(..., description="Train end date.")
    test_start: str = Field(..., description="Test start date.")
    test_end: str = Field(..., description="Test end date.")


class WalkForwardRequest(Contract):
    """Request for executing Walk-Forward Analysis (WFA)."""

    strategy_ref: str = Field(..., description="Target strategy.")
    symbols: list[str] = Field(..., description="Symbols array.")
    timeframe: str = Field(..., description="Resolution timeframe.")
    start: str = Field(..., description="Start date ISO string.")
    end: str = Field(..., description="End date ISO string.")
    parameter_space: ParameterSpace = Field(..., description="Parameter boundaries.")
    objective: str = Field(default="sharpe", description="Optimization objective.")
    initial_balance: float = Field(default=10000.0, description="Initial balance.")
    fold_mode: Literal["rolling", "anchored", "expanding"] = Field(
        default="rolling", description="Walk forward window split mode."
    )
    train_fraction: float = Field(
        default=0.7, description="Fraction of window allocated to training."
    )
    folds: int = Field(default=5, description="Number of walk-forward folds.")
    purging_bars: int = Field(default=0, description="Overlap purging window in bars.")
    embargo_bars: int = Field(
        default=0, description="Embargo bars applied after training."
    )
    dry_run: bool = Field(default=True, description="Dry run flag.")


class WalkForwardResponse(Contract):
    """Walk-forward analysis results envelope."""

    run_id: str = Field(..., description="Run identifier.")
    walk_forward_score: float = Field(
        ..., description="Combined Walk-Forward test score."
    )
    oos_retention_score: float = Field(
        ..., description="Ratio of test performance to train performance."
    )
    parameter_drift_score: float = Field(
        ..., description="Parameter variance/drift across folds."
    )
    walk_forward_efficiency: float = Field(
        ..., description="Walk-Forward Efficiency (WFE)."
    )
    status: str = Field(
        ..., description="Walk forward status (e.g. 'ready_for_risk_review')."
    )
    evidence: dict[str, Any] = Field(
        ..., description="Detailed fold outcomes and validation data."
    )


class MonteCarloResult(BaseModel):
    """Result of a Monte Carlo simulation run.

    Provides ruin probability and drawdown percentile calculations.
    """

    equity_curves: list[list[float]] = Field(..., description="Equity paths.")
    drawdowns: list[list[float]] = Field(..., description="Drawdown paths.")
    final_equity: list[float] = Field(..., description="Terminal equity distribution.")
    max_drawdowns: list[float] = Field(..., description="Max drawdown distributions.")
    ruin_probability: float = Field(
        ..., description="Probability of balance breaching ruin threshold."
    )
    daily_loss_breach_probability: float = Field(
        ..., description="Daily drawdown breach probability."
    )
    total_loss_breach_probability: float = Field(
        ..., description="Total drawdown breach probability."
    )
    profit_target_probability: float = Field(
        ..., description="Probability of reaching target balance."
    )
    losing_streak_distribution: list[int] = Field(
        ..., description="Losing streak counts distribution."
    )


class MonteCarloRequest(Contract):
    """Request for running trade-level Monte Carlo simulations."""

    trades: list[dict[str, Any]] = Field(
        ..., description="Chronological trade outcomes mapping."
    )
    simulation_method: Literal["shuffle_trades", "resample_trades", "skip_trades"] = (
        Field(default="shuffle_trades", description="Resampling strategy.")
    )
    simulation_count: int = Field(default=1000, description="Paths count.")
    initial_balance: float = Field(default=10000.0, description="Starting balance.")
    ruin_threshold: float = Field(
        default=0.5, description="Drawdown ruin fraction threshold (0-1)."
    )
    target_balance: float = Field(
        default=12000.0, description="Target balance parameter."
    )


class ParametricMonteCarloRequest(Contract):
    """Request for running parametric Monte Carlo simulations."""

    win_rate: float = Field(..., description="Win rate ratio (0-1).")
    reward_risk_ratio: float = Field(..., description="Reward-to-risk ratio.")
    risk_per_trade: float = Field(default=0.01, description="Sizing percentage.")
    trade_count: int = Field(default=100, description="Trade count per path.")
    simulation_count: int = Field(default=1000, description="Paths count.")
    initial_balance: float = Field(default=10000.0, description="Starting balance.")


class MonteCarloResponse(Contract):
    """Monte Carlo analysis envelope response."""

    run_id: str = Field(..., description="Run identifier.")
    ruin_probability: float = Field(..., description="Estimated probability of ruin.")
    drawdown_p95: float = Field(..., description="95th percentile max drawdown.")
    drawdown_p99: float = Field(..., description="99th percentile max drawdown.")
    mean_final_balance: float = Field(
        ..., description="Mean final balance across paths."
    )
    results: MonteCarloResult = Field(
        ..., description="Detailed Monte Carlo statistics."
    )


class ConsecutiveLosingRequest(Contract):
    """Request to simulate consecutive losing streaks."""

    win_rate: float = Field(..., description="Win rate ratio (0-1).")
    trade_count: int = Field(..., description="Total trades count.")
    simulation_count: int = Field(default=1000, description="Simulation paths.")


class ConsecutiveLosingScenario(BaseModel):
    """Represents a simulated losing streak scenario."""

    max_streak: int = Field(
        ..., description="Maximum consecutive losing trades encountered."
    )
    probability: float = Field(..., description="Observed probability of occurrence.")


class ConsecutiveLosingResponse(Contract):
    """Response containing simulated consecutive losing streak details."""

    run_id: str = Field(..., description="Run identifier.")
    mean_max_streak: float = Field(
        ..., description="Mean of maximum streak across runs."
    )
    max_streak_p95: int = Field(..., description="95th percentile max losing streak.")
    scenarios: list[ConsecutiveLosingScenario] = Field(
        ..., description="Streak distributions."
    )


class ProfitTargetRequest(Contract):
    """Request to estimate profit target achievement likelihoods."""

    win_rate: float = Field(..., description="Win rate ratio.")
    reward_risk_ratio: float = Field(..., description="Reward-to-risk.")
    risk_per_trade: float = Field(..., description="Sizing ratio.")
    trade_count: int = Field(..., description="Trades limit.")
    simulation_count: int = Field(..., description="Paths.")
    initial_balance: float = Field(..., description="Starting balance.")
    target_balance: float = Field(..., description="Target balance.")


class ProfitTargetResult(BaseModel):
    """Individual scenario results for profit target simulations."""

    target_balance: float = Field(..., description="Simulated target balance.")
    reached_probability: float = Field(
        ..., description="Estimated probability of reaching target."
    )
    mean_trades_to_reach: float | None = Field(
        default=None, description="Average trade steps to reach target balance."
    )


class ProfitTargetResponse(Contract):
    """Response containing profit target probability estimates."""

    run_id: str = Field(..., description="Run ID.")
    probability: float = Field(..., description="Probability of reaching target.")
    mean_trades: float | None = Field(
        default=None, description="Mean trade count required."
    )
    results: list[ProfitTargetResult] = Field(
        default_factory=list, description="Detail scenarios."
    )


class MultiEntryRequest(Contract):
    """Request to simulate multi-entry strategy parameters."""

    entries: int = Field(default=3, description="Scale-in entry levels count.")
    entry_distance_pct: float = Field(
        default=0.01, description="Distance between entry grids."
    )
    volume_multipliers: list[float] = Field(
        default_factory=lambda: [1.0, 1.5, 2.0],
        description="Scale multipliers per entry.",
    )
    win_rate: float = Field(..., description="Base win rate.")
    reward_risk_ratio: float = Field(..., description="Reward-to-risk.")
    initial_balance: float = Field(default=10000.0, description="Start balance.")
    trade_count: int = Field(default=100, description="Trade count.")
    simulation_count: int = Field(default=1000, description="Paths.")


class MultiEntryScenarioResult(BaseModel):
    """Results of a multi-entry grid simulation scenario."""

    average_cost_pct: float = Field(
        ..., description="Normalized average cost entry index."
    )
    final_balance_mean: float = Field(..., description="Mean terminal balance.")
    drawdown_mean: float = Field(..., description="Mean drawdown experienced.")


class MultiEntryResponse(Contract):
    """Response details for multi-entry grids analysis."""

    run_id: str = Field(..., description="Run ID.")
    optimal_entries: int = Field(..., description="Recommended entries count.")
    scenarios: list[MultiEntryScenarioResult] = Field(
        ..., description="Detail entry scenarios."
    )


class RobustnessRequest(Contract):
    """Request for running robustness checks against evaluated strategies."""

    strategy_ref: str = Field(..., description="Strategy name.")
    parameters: dict[str, Any] = Field(..., description="Strategy parameters.")
    symbols: list[str] = Field(..., description="Symbols list.")
    timeframe: str = Field(..., description="Timeframe.")
    start: str = Field(..., description="Start date ISO string.")
    end: str = Field(..., description="End date ISO string.")
    initial_balance: float = Field(default=10000.0, description="Starting balance.")


class RobustnessStats(BaseModel):
    """Robustness metric statistics summary."""

    pass_rate: float = Field(..., description="Robustness test suite checks pass rate.")
    robustness_score: float = Field(
        ..., description="Calculated robustness rating percentage."
    )
    warnings: list[str] = Field(
        default_factory=list, description="Validation warnings flagged."
    )


class RobustnessResponse(Contract):
    """Response packaging robustness assessment details."""

    run_id: str = Field(..., description="Run ID.")
    stats: RobustnessStats = Field(..., description="Calculated statistics.")
    checks: dict[str, Any] = Field(
        ..., description="Checked status outputs per subtest."
    )


class SplitterResult(BaseModel):
    """Data model holding train/test split index windows."""

    folds: list[WalkForwardWindow] = Field(..., description="Split windows list.")


class ParametricSimulationResult(BaseModel):
    """Parametric path simulation stats."""

    equity_paths: list[list[float]] = Field(..., description="Equity paths.")
    drawdowns: list[list[float]] = Field(..., description="Drawdowns.")
    final_equity: list[float] = Field(..., description="Terminal equity.")


class ConsecutiveLosingScenarioResult(BaseModel):
    """Model holding details of a consecutive loss simulation run."""

    max_losing_streak: int = Field(..., description="Max losing streak.")
    win_rate: float = Field(..., description="Simulated win rate.")


class ProfitTargetScenarioResult(BaseModel):
    """Model holding details of a profit target simulation run."""

    target_balance: float = Field(..., description="Target balance.")
    reached: bool = Field(..., description="True if target was hit.")
    trades_needed: int = Field(..., description="Trades required to hit target.")


class PortfolioOptimizerResult(BaseModel):
    """Portfolio manager allocation weight outputs."""

    weights: dict[str, float] = Field(
        ..., description="Optimization weights by asset symbol."
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata.")
