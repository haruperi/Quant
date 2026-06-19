## Phase 9 Optimization Service

### Goal

Implement the Optimization Service requirements under `app/services/optimization/` while preserving the phase module boundaries and governance rules.

Task inventory: 278 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

Required files:

```text

app/utils/__init__.py

app/utils/dataframe_tools.py

app/services/simulation/__init__.py

app/services/simulation/engine.py

```

Required functionality:

- Backtest simulation engine executes individual runs synchronously.
- Dataframe tools generate parameter combination grids.
- SQLite or standard storage repositories persist sweep state data.

### Files to Create

```text

app/services/optimization/

app/__init__.py

app/services/optimization/__init__.py

app/services/optimization/sweeps.py

app/services/optimization/robustness.py

app/services/optimization/splitting.py

app/services/optimization/scoring.py

app/services/optimization/algorithms/__init__.py

app/services/optimization/algorithms/grid.py

app/services/optimization/algorithms/random.py

app/services/optimization/algorithms/bayesian.py

app/services/optimization/algorithms/genetic.py

app/services/optimization/persistence/__init__.py

app/services/optimization/persistence/checkpoint.py

app/services/optimization/persistence/repository.py

app/services/optimization/helpers.py

app/services/optimization/models.py

```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `app/__init__.py`

Functions/classes:

- `strategy_id`
- `Infinity`
- `OPT_JSON_SERIALIZATION_FAILED`

Requirements:

- [X] Optimization workflows shall record reproducibility context including `strategy_id`, parameter-space definition including constraints, objective, data window start/end, engine type, engine version, seed, cost model hash, simulator realism profile hash, module version, parameter-space hash, candidate hashes, and all candidate results required to reproduce ranking and report outputs.
- [X] The module shall validate optimization requests, strategy compatibility, market data quality, parameter spaces, objective definitions, and evidence-package shape before running expensive work or persisting artifacts.
- [X] `parametric_simulation` shall simulate outcomes from win rate, reward/risk ratio, risk per trade, trade count, simulation count, and initial balance.
- [X] `parameter_space_hash` shall be order-invariant, shall sort dictionary keys, shall canonicalize parameter definitions, and shall include constraints after canonical sorting and normalization.
- [X] The module shall perform no broker, database, network, multiprocessing, or heavy dependency initialization at import time.
- [X] Timeout enforcement shall use a monotonic clock source such as `time.monotonic()` or `time.perf_counter()` so NTP adjustments or wall-clock changes cannot cause premature timeout or infinite hangs.
- [X] Public result payloads shall be JSON-safe before envelope return. `NaN`, `Infinity`, and `-Infinity` shall serialize as `null` with a warning; `datetime` values shall serialize as UTC ISO-8601 strings; `Decimal` values shall serialize as normalized strings unless a schema declares a numeric representation; unsupported objects shall fail closed with `OPT_JSON_SERIALIZATION_FAILED`.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.

#### `app/services/optimization/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [X] No file-specific functional requirements defined. Foundation properties apply.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.

#### `app/services/optimization/sweeps.py`

Functions/classes:

- `ParameterSpace`
- `ParameterCandidate`
- `SweepResult`
- `grid_search`
- `random_search`
- `run_parameter_sweep`

Requirements:

- [X] No file-specific functional requirements defined. Foundation properties apply.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.
- [X] Parameter spaces, iteration counts, population sizes, bootstrap counts, simulation counts, and worker counts must be bounded before production use.
- [X] Optimization outputs shall include objective, executable parameters, candidate score, data slice, algorithm name and version, seed, engine type and version, cost model hash, simulator realism profile hash, parameter-space hash, candidate hash, warnings, and caveats.
- [X] Metrics shall include request count, validation failures, runtime failures, resource-cap rejections, execution duration, queue time, candidate count, and cancellation count.
- [X] Repeated deterministic runs with the same inputs shall produce the same candidate ordering, same candidate hashes, same parameter-space hash, and same evidence when backtest execution is deterministic.
- [X] Request-packaging tools shall not trigger candidate execution, persistence writes, external network calls, or background jobs unless explicitly documented and approved.
- [X] The module shall support float, integer, categorical, boolean, fixed, conditional, and constrained parameter spaces.
- [X] Parameter constraints shall be evaluated before candidate execution, and unsafe constraint expressions shall be blocked.
- [X] Final optimization output states shall use the canonical enum `ready_for_risk_review`, `validation_needed`, `research_only`, `rejected`, `failed`, or `cancelled`; all requirements, schemas, tests, examples, and reports shall use these exact values.
- [X] `compare_optimization_runs` shall package candidate optimization run IDs or result payloads for comparison.
- [X] `calculate_parameter_stability` shall calculate standard-deviation-style stability by parameter across selected candidates.
- [X] `detect_overfit_parameters` shall detect overfit risk from the gap between in-sample and out-of-sample scores.
- [X] `rank_parameter_sets` shall rank optimization parameter candidates deterministically from highest score to lowest score.
- [X] `rank_parameter_sets` tie-breaking shall sort tied scores by `trade_count` descending when available, then by `candidate_hash` ascending; missing `trade_count` shall sort after present `trade_count` for the same score.
- [X] Search methods shall return optimization summaries containing candidate results, best parameters, best score, objective, runtime, and total-run metadata.
- [X] `walk_forward` shall optimize parameters on rolling training windows and test them on out-of-sample windows.
- [X] `optimization_walk_forward` shall expose a user-facing wrapper around walk-forward parameter optimization.
- [X] `print_optimization_report` shall print or format a top-candidate optimization report for inspection.
- [X] Walk-forward results shall preserve train window, test window, selected parameters, train score, test score, and degradation context.
- [X] Walk-forward evidence shall include fold results, best parameters per fold, OOS results per fold, fold pass rate, parameter drift score, OOS retention score, walk-forward score, Walk-Forward Efficiency, and walk-forward status.
- [X] `parallel_walk_forward` shall run walk-forward optimization across windows and/or candidates in parallel.
- [X] Pruned candidates shall remain persisted with partial evidence, including prune reason, prune phase, intermediate metric snapshot, backend name, and retryable flag.
- [X] `run_optimization_task` shall coordinate a background parameter optimization run and report progress.
- [X] Candidate cache entries shall be invalidated automatically when strategy hash, data hash, cost model hash, simulator realism profile hash, objective hash, engine type, module version, or parameter-space hash changes.
- [X] `candidate_hash` shall be the source of truth for candidate deduplication and shall deterministically combine strategy hash, data hash, cost model hash, simulator realism profile hash, objective hash, engine type, module version, and canonicalized sorted executable parameter values.
- [X] `candidate_hash` shall exclude inactive conditional parameters and shall use canonical JSON with sorted keys and normalized decimals.

#### `app/services/optimization/robustness.py`

Functions/classes:

- `calculate_robustness_score`
- `RobustnessRequest`
- `RobustnessStats`
- `RobustnessResponse`

Requirements:

- [X] Optimization workflows must warn about overfitting, parameter instability, and robustness weaknesses instead of presenting candidate scores as live readiness.
- [X] Risk Governor handoff packages shall include the full evidence package, final decision, best candidate, top candidates, rejected-candidate summary, production gates, walk-forward evidence, robustness evidence, Monte Carlo evidence, prop-firm compliance evidence, warnings, audit references, and institutional evidence fields.
- [X] `run_spread_stress_test` shall package wider-spread stress-test inputs.
- [X] `run_slippage_stress_test` shall package slippage stress-test inputs.
- [X] `run_commission_stress_test` shall package commission stress-test inputs.
- [X] `run_randomize_trade_order_mc` shall package shuffled-trade-order Monte Carlo inputs.
- [X] `run_resample_trades_mc` shall package resampled-trade Monte Carlo inputs.
- [X] `run_skip_trades_mc` shall package skipped-trade Monte Carlo inputs.
- [X] `run_randomize_parameters_mc` shall package randomized-parameter Monte Carlo inputs.
- [X] `run_randomize_history_mc` shall package randomized-history Monte Carlo inputs.
- [X] `run_combined_monte_carlo` shall package combined Monte Carlo stress inputs.
- [X] `run_cross_market_test` shall package cross-market robustness-test inputs.
- [X] `run_cross_timeframe_test` shall package cross-timeframe robustness-test inputs.
- [X] `run_second_oos_test` shall package second out-of-sample validation inputs.
- [X] `run_third_oos_test` shall package third out-of-sample validation inputs.
- [X] `calculate_robustness_score` shall calculate a deterministic robustness percentage from pass/fail checks.
- [X] `build_robustness_report` shall package robustness report creation inputs.
- [X] `assess_strategy_robustness` shall produce a comprehensive Monte Carlo robustness assessment.
- [X] `robustness_simulation` shall simulate robustness with skipped trades, deterioration, and selected Monte Carlo mode.
- [X] `optimization_monte_carlo` shall expose a user-facing wrapper around Monte Carlo robustness simulation over trade results.
- [X] Candidate scoring shall support return, net profit, Sharpe, Sortino, Calmar, profit factor, expectancy, win rate, drawdown, trade count, exposure, turnover, cost-adjusted return, OOS retention, fold consistency, robustness survival, Monte Carlo p5 outcome, and prop-firm breach probability.
- [X] `RobustnessRequest`, `RobustnessStats`, and `RobustnessResponse` shall model robustness simulation inputs and outputs.
- [X] Evidence packages shall include best candidate, top candidates, rejected candidate summary, optimization summary, walk-forward evidence, parameter stability evidence, robustness evidence, Monte Carlo evidence, prop-firm compliance evidence, production gates, final decision, warnings, audit references, and visualization data.
- [X] Chart-ready data shall support equity curves, drawdown curves, candidate scatter plots, parameter heatmaps, Pareto front, walk-forward fold results, Monte Carlo cone, final equity distribution, drawdown distribution, regime performance, robustness degradation, DSR versus raw Sharpe, topology visualization, capacity ladder, embargo table, and execution-realism stress table.
- [X] The module shall support checkpointing after configured candidate intervals, state transitions, before long robustness or Monte Carlo phases, on cancellation, and on recoverable errors.
- [X] Metrics and reports must not overstate live readiness or hide sample-size, out-of-sample, robustness, or overfit caveats.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.
- [X] `bootstrap_simulation` shall use block bootstrap to preserve short-term temporal structure.
- [X] `compare_simulation_methods` shall run multiple Monte Carlo methods and compare their results.
- [X] `MonteCarloResult` shall hold Monte Carlo simulation outputs and provide summary/statistics behavior.
- [X] Monte Carlo evidence shall include ruin probability, daily-loss breach probability, total-loss breach probability, profit-target probability, equity percentiles, drawdown percentiles, losing-streak distribution, and return distribution.
- [X] `run_monte_carlo_task` shall coordinate a background Monte Carlo simulation run.

#### `app/services/optimization/splitting.py`

Functions/classes:

- `WalkForwardSplit`
- `chronological_split`
- `expanding_window_split`
- `rolling_window_split`

Requirements:

- [X] No file-specific functional requirements defined. Foundation properties apply.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.
- [X] `run_walk_forward_optimization` shall package rolling train/test walk-forward optimization details.
- [X] `run_walk_forward_matrix` shall package a matrix of walk-forward train/test combinations.
- [X] `splitter_from_rolling` shall create deterministic rolling time-series train/test windows.
- [X] `splitter_from_expanding` shall create deterministic expanding time-series train/test windows.
- [X] `splitter_rolling_split` shall split tabular data into rolling train/test or train/validation/test slices.
- [X] `SplitterResult` shall hold split windows and support plotting/inspection behavior.
- [X] Walk-forward validation shall support rolling, anchored, expanding, and custom fold modes.
- [X] Walk-forward and cross-validation splits shall enforce configurable purging and embargo periods between training and validation sets when required.
- [X] Evidence shall include embargo configuration, effective embargo bars, and leakage-prevention status for walk-forward and CPCV runs.
- [X] `analyze_walk_forward_results` shall summarize walk-forward optimization results.
- [X] `run_walk_forward_task` shall coordinate a background walk-forward analysis run and report progress.

#### `app/services/optimization/scoring.py`

Functions/classes:

- `OptimizationScore`
- `ScoringFunction`
- `evaluate_candidate_score`
- `rank_candidates`

Requirements:

- [X] Inactive conditional parameters shall be excluded from executable candidate parameters, candidate hashes, backtest adapter payloads, scoring, and strategy invocation, while remaining available only in metadata or audit records.
- [X] Search methods shall support objective/scoring functions, initial balance, symbol, engine type, max workers, verbosity, progress callbacks, and reproducibility controls where implemented.
- [X] `sharpe_score` shall score results using Sharpe ratio.
- [X] `sortino_score` shall score results using Sortino ratio.
- [X] `calmar_score` shall score results using Calmar ratio.
- [X] `profit_factor_score` shall score results using profit factor.
- [X] `total_return_score` shall score results using total return percentage.
- [X] `custom_score` shall calculate a weighted composite from return, Sharpe, and drawdown components.
- [X] `optimization_get_scoring_func` shall resolve supported objective names to scoring functions.
- [X] Scoring helpers shall handle missing metrics with deterministic fallback behavior.
- [X] Candidate scoring shall support single-objective, weighted multi-objective, constraint-based, and Pareto-ready scoring.
- [X] Pareto selection shall be deterministic and shall record fallback behavior for knee-point selection when used.
- [X] Anti-overfitting gates shall evaluate in-sample versus out-of-sample degradation, walk-forward consistency, parameter neighborhood smoothness, top-candidate clustering, profit concentration, trade count adequacy, cost sensitivity, Monte Carlo survival, regime dependency, Deflated Sharpe Ratio, multiple-testing correction, topology stability, leakage prevention, and capacity degradation.
- [X] Every scored candidate shall include raw Sharpe, deflated Sharpe, multiple-testing method, nominal or effective trial count metadata, Sharpe variance estimate, MTB pass status, and MTB rejection reason.
- [X] `nominal_trial_count` shall be calculated from unique executable candidate hashes after canonical normalization, inactive conditional exclusion, constraint rejection, and cache deduplication.
- [X] If topology-adjusted or effective-trial estimation is enabled, evidence shall include `effective_trial_count`, `trial_count_method`, and any required method metadata.
- [X] Evidence shall include `trial_count_independence_warning` when nominal counts may overstate independence in highly correlated, Bayesian, exploitative, or highly constrained parameter spaces.
- [X] `nominal_trial_count` shall not be presented as a statistically independent trial count unless the configured method explicitly supports that interpretation.
- [X] PBO threshold enforcement shall remain blocked until the designated risk owner approves production, strict-capital, research-only, and exploratory-validation thresholds.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.

#### `app/services/optimization/algorithms/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [X] No file-specific functional requirements defined. Foundation properties apply.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.

#### `app/services/optimization/algorithms/grid.py`

Functions/classes:

- `run_parameter_sweep`

Requirements:

- [X] `run_parameter_sweep` shall package a grid or random parameter search request for downstream optimization execution.
- [X] `run_parameter_sweep` shall require `search_method` with approved values `grid`, `random`, `latin_hypercube`, or `sobol`; distribution-based methods shall include validated distribution definitions instead of grid-only parameter lists.
- [X] `grid_search` shall evaluate an exhaustive parameter grid over a supplied strategy/backtest context.
- [X] `optimization_grid_search` shall expose a user-facing wrapper for exhaustive parameter grid search.
- [X] Grid expansion shall support `100,000+` combinations through strict iterator mode that yields one candidate at a time and never materializes the full Cartesian product in memory.
- [X] Strict iterator mode shall stay within an owner-approved memory budget regardless of grid size; the budget value remains pending owner/architect approval.
- [X] `parallel_grid_search` shall run parameter-grid candidate evaluations across multiple workers.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.

#### `app/services/optimization/algorithms/random.py`

Functions/classes:

- `ManualPairInput`
- `RandomWinRateRequest`
- `RandomWinRatePair`
- `DistributionStats`
- `RandomWinRateResult`
- `RandomWinRateResponse`

Requirements:

- [X] `random_search` shall sample parameter combinations from distributions and evaluate candidates.
- [X] `optimization_random_search` shall expose a user-facing wrapper for randomized parameter search.
- [X] Seeded random search shall support pseudo-random, Sobol sequence, and Latin Hypercube sampling contracts.
- [X] Pseudo-random sampling shall be the always-available deterministic fallback.
- [X] `monte_carlo_analysis` shall run Monte Carlo analysis against a backtest result with selected simulation type and random seed.
- [X] `shuffle_trades_simulation` shall randomize trade order while preserving individual trade outcomes.
- [X] `random_win_rate_simulation` shall simulate trading with random win-rate/reward-risk pairs.
- [X] Monte Carlo and scenario simulations shall support reproducibility controls and must not claim certainty from randomized outputs.
- [X] Monte Carlo random number generation shall derive deterministic seeds from run seed, candidate ID, and phase-specific offsets.
- [X] `parallel_random_search` shall run sampled parameter candidate evaluations across multiple workers.
- [X] `ManualPairInput`, `RandomWinRateRequest`, `RandomWinRatePair`, `DistributionStats`, `RandomWinRateResult`, and `RandomWinRateResponse` shall model random win-rate simulation inputs and outputs.
- [X] Random, Monte Carlo, Bayesian, and genetic workflows must support seed or random-state controls where practical.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.

#### `app/services/optimization/algorithms/bayesian.py`

Functions/classes:

- `bayesian_optimization`
- `optimization_bayesian`
- `BayesianOptimizationResult`

Requirements:

- [X] `bayesian_optimization` shall run Gaussian-process-style Bayesian optimization over a parameter space.
- [X] `optimization_bayesian` shall expose a user-facing wrapper for Bayesian parameter optimization.
- [X] No file-specific non-functional requirements defined.

#### `app/services/optimization/algorithms/genetic.py`

Functions/classes:

- `genetic_algorithm`
- `optimization_genetic`
- `GeneticAlgorithmResult`

Requirements:

- [X] `genetic_algorithm` shall evolve parameter candidates through population, selection, crossover, mutation, and elitism behavior.
- [X] `optimization_genetic` shall expose a user-facing wrapper for genetic algorithm parameter optimization.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.

#### `app/services/optimization/persistence/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [X] No file-specific functional requirements defined. Foundation properties apply.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.

#### `app/services/optimization/persistence/checkpoint.py`

Functions/classes:

- `OPT_ATOMIC_WRITE_FAILED`
- `OPT_CHECKPOINT_CORRUPTED`
- `OPT_INTRADAY_RULE_DATA_UNAVAILABLE`
- `OPT_PROP_FIRM_INTRADAY_EVALUATION_REQUIRED`
- `OPT_TRIAL_COUNT_METHOD_UNSUPPORTED`
- `OPT_PRUNED_BY_HARD_GATE`
- `OPT_PBO_THRESHOLD_FAILED`
- `OPT_NOISY_OBJECTIVE_NOT_ALLOWED`
- `STOCHASTIC_REALISM_CONFLICT`

Requirements:

- [X] The module shall write optimization runs, candidates, candidate results, checkpoints, evidence packages, and audit records only through an approved repository interface.
- [X] Resume logic shall reject corrupted, partial, or schema-invalid checkpoint artifacts rather than silently resuming.
- [X] If the latest checkpoint is corrupted but an earlier valid checkpoint exists, the run may resume from the earlier checkpoint with an audit warning.
- [X] File-backed checkpoint and candidate-result writes shall use atomic rename semantics by writing to a uniquely named temporary file, flushing and fsyncing where supported, then replacing the target artifact.
- [X] Atomic write failure shall produce a structured repository or checkpoint error with artifact type, temporary path reference, target path reference, run ID, and phase.
- [X] Atomic write temporary files shall be created only under approved artifact directories and shall not be treated as valid evidence packages or checkpoints.
- [X] File-backed checkpoint writes shall prevent path traversal through both temporary and final artifact paths.
- [X] The module shall include `OPT_ATOMIC_WRITE_FAILED`, `OPT_CHECKPOINT_CORRUPTED`, `OPT_INTRADAY_RULE_DATA_UNAVAILABLE`, `OPT_PROP_FIRM_INTRADAY_EVALUATION_REQUIRED`, `OPT_TRIAL_COUNT_METHOD_UNSUPPORTED`, `OPT_PRUNED_BY_HARD_GATE`, `OPT_PBO_THRESHOLD_FAILED`, and `OPT_NOISY_OBJECTIVE_NOT_ALLOWED` with subtype `STOCHASTIC_REALISM_CONFLICT` where applicable.
- [X] No file-specific non-functional requirements defined.

#### `app/services/optimization/persistence/repository.py`

Functions/classes:

- `OptimizationRepository`
- `OptimizationRunRecord`
- `save_optimization_run`
- `load_optimization_run`
- `update_optimization_progress`

Requirements:

- [X] Execution-capable workflows shall require an approved execution profile with resource caps, timeout policy, repository policy, and safety gates.
- [X] Repository-backed workflows shall be idempotent for repeated resume, cancel, and progress requests.
- [X] Production implementation shall be blocked until owner-approved limits exist for max candidates, max parameter-space expansion, max runtime, max worker count, max Monte Carlo simulations, objective whitelist, repository backend, artifact root, report schema version, and resource override approver.
- [X] Optional Optuna and scikit-optimize backends shall sit behind a stable optimizer backend interface and shall require dependency approval, version pinning, repository policy approval, and contract tests before production use.
- [X] Future Ray, Dask, or Celery adapters shall remain deferred until repository idempotency, retry behavior, and resource accounting are production-mature.
- [X] The module shall own repository contracts and payload schemas, but shall not own production database provisioning, migrations, credentials, or operations unless explicitly assigned by architecture decision.
- [X] Concrete repository adapters shall be owned by the approved persistence layer unless explicitly assigned to this module by architecture decision.
- [X] Repository implementations shall be passed into execution-capable workflows through Dependency Injection rather than imported or constructed by optimization core code.
- [X] Repository backend support for in-memory fixtures, JSONL fixtures, SQLite, DuckDB/Parquet, PostgreSQL, or managed PostgreSQL-compatible databases shall require deployment-tier approval before production use.
- [X] Proposed engineering baseline: repository writes over network-backed repositories should retry safe transient failures with exponential backoff up to `3` attempts before surfacing a persistent structured error.
- [X] Candidate hash generation shall benchmark at `10,000 candidates/sec` locally for simple parameters, parameter validation shall benchmark at `5,000 candidates/sec` for simple numeric parameters, repository write throughput shall benchmark `1,000` candidate records, and resume scan shall benchmark `10,000` candidate hash checks.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.
- [X] Each execution-capable workflow shall enforce configured timeout, retry, cancellation, and backpressure policies.
- [X] Parallel workflows must avoid race conditions in progress tracking and result aggregation.
- [X] Persist/package tools must distinguish request packaging from actual durable storage.
- [X] Dry-run behavior shall be defined per capability type: packaging tools return a validated request envelope without execution, background jobs, persistence writes, or external calls; lightweight calculation tools still perform the deterministic calculation but skip any logging, persistence, or external side-effect writes.
- [X] Constraint violations shall be persisted or represented in audit-ready evidence and shall not be sent to the backtest adapter for execution.
- [X] `ProgressTracker` shall track progress for parallel optimization work in a thread-safe manner.
- [X] Background task entry points shall return a `task_id` and polling/progress reference, not block the calling thread until optimization completion.

#### `app/services/optimization/helpers.py`

Functions/classes:

- `load_strategy_from_path`
- `normalize_engine_type`
- `run_strategy_backtest`
- `run_strategy_backtest_from_path`
- `EngineOptimizationResult`
- `OptimizationExecutionError`
- `OPT_EXECUTION_FAILED`
- `OPT_STRATEGY_LOAD_FAILED`
- `OPT_ENGINE_CREATION_FAILED`
- `OPT_SYMBOL_SETUP_FAILED`
- `OPT_CANDIDATE_EXECUTION_FAILED`
- `OPT_NOISY_OBJECTIVE_NOT_ALLOWED`
- `STOCHASTIC_REALISM_CONFLICT`

Requirements:

- [X] `service_strategy_class` shall normalize either a concrete strategy class or a callable strategy-class factory.
- [X] `optimization_tool_result` shall build the standard HaruQuant optimization result envelope.
- [X] `optimization_tool_context` shall extract request ID, agent name, environment, and dry-run context from tool keyword arguments.
- [X] `optimization_business_payload` shall remove standard context fields and retain only business request fields.
- [X] `package_optimization_request` shall create deterministic request packages without running compute-heavy optimization jobs.
- [X] Lazy attribute resolution shall resolve lower-level optimization service attributes without putting business logic in the package initializer.
- [X] `load_strategy_from_path` shall dynamically load a strategy class from a file path and class name.
- [X] `normalize_engine_type` shall normalize legacy engine labels to supported execution engine names.
- [X] `run_strategy_backtest` shall run one optimization candidate through the trading/backtest engine with supplied strategy, data, symbol, parameters, balance, engine type, and position size.
- [X] `run_strategy_backtest_from_path` shall load a strategy class from disk and run one optimization candidate through the backtest path.
- [X] `EngineOptimizationResult` shall expose a small optimization-facing result contract built from engine outputs.
- [X] Execution helpers shall convert engine trades, equity points, processed tick counts, and analytics into optimization-ready result objects.
- [X] Execution helpers shall return or raise structured `OptimizationExecutionError` results with deterministic `OPT_EXECUTION_FAILED`, `OPT_STRATEGY_LOAD_FAILED`, `OPT_ENGINE_CREATION_FAILED`, `OPT_SYMBOL_SETUP_FAILED`, or `OPT_CANDIDATE_EXECUTION_FAILED` codes when strategy loading, engine creation, symbol setup, or candidate execution fails.
- [X] Candidate execution shall occur only through a versioned `BacktestExecutionAdapter`.
- [X] The backtest adapter shall validate required data columns, strategy compatibility, cost model, engine type, deterministic seed behavior, and adapter version before execution.
- [X] Backtest adapter version mismatch shall fail closed before execution.
- [X] Unsupported simulator realism shocks shall return structured unsupported-feature errors and shall not be silently ignored.
- [X] Deterministic-only noisy-objective mode shall fail closed with `OPT_NOISY_OBJECTIVE_NOT_ALLOWED` when stochastic simulator realism is active, and failure details shall include conflict subtype `STOCHASTIC_REALISM_CONFLICT`.
- [X] Background tasks shall isolate database/progress-manager side effects from low-level deterministic optimization helpers.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.
- [X] Optimization behavior must be reproducible for the same inputs where deterministic algorithms are used.
- [X] Proposed engineering baseline: public packaging responses should complete in `<= 200 ms` under owner-approved payload-size limits, subject to owner finalization and benchmark validation.
- [X] Optimization must control compute load and warn about overfitting risks.
- [X] Optimization must not mutate production strategy state without governance.
- [X] Optimization must not place trades, call live brokers, or bypass risk/trading/live safety gates.
- [X] Error responses must be structured, traceable, and safe for API/agent consumption.
- [X] Optional lower-level dependencies shall either use a documented fallback or return a structured dependency error such as `OPT_SAMPLER_UNAVAILABLE`, `OPT_OPTIMIZER_BACKEND_UNAVAILABLE`, or `OPT_DEPENDENCY_UNAVAILABLE`; unhandled `ImportError` or backend-specific exceptions shall not cross public tool boundaries.
- [X] Logs, traces, reports, and errors shall redact secrets, credentials, authorization headers, private trade payloads, sensitive file paths, and environment variables.
- [X] Registry changes must remain covered by tests and catalog updates.
- [X] Hashing shall use SHA-256 over canonical JSON with sorted keys and normalized decimals, with decimals quantized to eight decimal places by default unless field-specific precision is declared.
- [X] Resource caps shall fail closed by default unless an explicitly approved override is present.
- [X] Official optimization tools shall not possess live broker credentials, live broker gateway network access, or permission to place or close trades.
- [X] Error codes shall use deterministic enum-style values and optimization-specific errors shall use the `OPT_` prefix. Custom optimization exceptions and error codes must inherit and reuse exceptions from `app.utils.errors` to prevent duplicate declaration.
- [X] Each requirement shall include a stable requirement ID, priority, scope tier, owner, acceptance criteria, and one or more mapped tests before Builder handoff.
- [X] Requirement priorities shall distinguish `P0 safety`, `P0 contract`, `P1 current public tool`, `P2 internal rebuild`, and `P3 future`.
- [X] Confirmed requirements, assumptions, proposed decisions, pending decisions, and future improvements shall remain separated.
- [X] The optimization registry must expose only intentional public service tools through `app.services.optimization.__all__`.
- [X] The optimization registry must keep exports unique, callable, documented, and synchronized with tests and catalog entries.
- [X] Public service tools that package work must not execute live broker actions or mutate production strategy state.
- [X] When a caller omits `dry_run`, public optimization tools shall default to `dry_run=True`.
- [X] Official optimization tools shall never place trades, close broker positions, access live broker gateways, or return `approved_for_live_trading`.
- [X] Official optimization tools shall include side-effect metadata with `places_trade=False`.
- [X] Portfolio Manager handoff packages shall include capacity estimates, exposure assumptions, cross-symbol validation, cross-timeframe validation, regime evidence, intended deployment AUM, estimated capacity in deployment base currency, and portfolio-impact warnings.
- [X] UI/reporting handoff packages shall provide chart-ready data without requiring recomputation and shall not render charts inside this module.
- [X] `build_optimization_report` shall package optimization report creation inputs for downstream reporting.
- [X] Optional backend-specific objects shall not leak into official tool responses.
- [X] CPCV validation shall support deterministic path generation when enabled and shall enforce purging and embargo on every path.
- [X] `resample_returns_simulation` shall sample returns with replacement from the empirical return distribution.
- [X] `calculate_confidence_intervals` shall calculate confidence intervals for selected metrics.
- [X] `position_sizing_simulation` shall compare linear and compounding position-sizing equity curves.
- [X] `consecutive_losing_simulation` shall simulate maximum consecutive losses for win-rate and reward/risk pairs.
- [X] `profit_target_simulation` shall estimate probability of reaching a target balance.
- [X] `multi_entry_simulation` shall simulate multi-entry strategy scenarios.
- [X] Prop-firm compliance gates shall support max daily loss, max total loss, monthly target, best-day consistency, news restrictions, weekend restrictions, overnight restrictions, exposure limits, correlated exposure limits, and forbidden behavior flags.
- [X] End-of-day-only prop-firm evaluation shall be allowed only when the specific versioned prop-firm profile explicitly permits it.
- [X] `compare_parallel_speedup` shall compare optimization runtime across different worker counts.
- [X] `get_optimal_n_jobs` shall recommend a worker count based on available CPU capacity.
- [X] `estimate_completion_time` shall estimate total execution time from single-run time, run count, and worker count.
- [X] The service layer shall depend on an `ExecutionOrchestrator` abstraction rather than direct multiprocessing.
- [X] Local sequential and local multiprocessing orchestration shall preserve deterministic aggregation order and equivalent failure isolation.
- [X] The `ExecutionOrchestrator` shall support backend-neutral early-stopping and pruning hooks.
- [X] `pfo_from_optimize_func` shall periodically optimize portfolio allocation weights from a deterministic callback.
- [X] `pfo_plot` shall package periodic allocation-weight data for inspection and may provide non-UI diagnostic serialization; UI chart rendering shall remain outside the Optimization module.

#### `app/services/optimization/models.py`

Functions/classes:

- `OptimizationResult`
- `UnsupervisedConfigRequest`
- `UnsupervisedRunSummary`
- `UnsupervisedAnalysisRequest`
- `ParameterRange`
- `OptimizationRequest`
- `OptimizationResponse`
- `OptimizationRunDetails`
- `OptimizationResultItem`
- `PositionSizingRequest`
- `WalkForwardRequest`
- `WalkForwardWindow`
- `WalkForwardResponse`
- `MonteCarloRequest`
- `ParametricMonteCarloRequest`
- `MonteCarloResponse`
- `ConsecutiveLosingRequest`
- `ConsecutiveLosingScenario`
- `ConsecutiveLosingResponse`
- `ProfitTargetRequest`
- `ProfitTargetResult`
- `ProfitTargetResponse`
- `MultiEntryRequest`
- `MultiEntryScenarioResult`
- `MultiEntryResponse`

Requirements:

- [X] `OptimizationResult` shall represent one candidate optimization result with parameters, score, metrics, and metadata.
- [X] `OptimizationSummary` shall represent an optimization run summary and expose top-N and dataframe conversion behavior.
- [X] `UnsupervisedConfigRequest`, `UnsupervisedRunSummary`, and `UnsupervisedAnalysisRequest` shall model unsupervised-analysis configuration and output attached to optimization flows.
- [X] `ParameterRange` shall model a named parameter range for optimization requests.
- [X] `OptimizationRequest`, `OptimizationResponse`, `OptimizationRunDetails`, and `OptimizationResultItem` shall model optimization request, response, run detail, and result item payloads.
- [X] `PositionSizingRequest` shall model position-sizing simulation requests.
- [X] `WalkForwardRequest`, `WalkForwardWindow`, and `WalkForwardResponse` shall model walk-forward analysis inputs and outputs.
- [X] `MonteCarloRequest`, `ParametricMonteCarloRequest`, and `MonteCarloResponse` shall model Monte Carlo inputs and outputs.
- [X] `ConsecutiveLosingRequest`, `ConsecutiveLosingScenario`, and `ConsecutiveLosingResponse` shall model consecutive-loss simulation inputs and outputs.
- [X] `ProfitTargetRequest`, `ProfitTargetResult`, and `ProfitTargetResponse` shall model profit-target simulation inputs and outputs.
- [X] `MultiEntryRequest`, `MultiEntryScenarioResult`, and `MultiEntryResponse` shall model multi-entry simulation inputs and outputs.
- [X] Evidence packages shall include institutional fields for raw Sharpe, Deflated Sharpe Ratio, multiple-testing method, purging and embargo data, leakage prevention status, parameter plateau score, isolation penalty, estimated capacity, simulator realism profiles, orchestrator backend, and resource quota.
- [X] Evidence packages shall include advanced research fields for PBO, CPCV, sensitivity, noisy-objective handling, repeated score statistics, and compute cost when applicable.
- [X] Capacity evidence shall include `deployment_base_currency`, `intended_deployment_aum`, and `estimated_capacity_in_base_currency`.
- [X] Reports shall be generated from evidence without recomputation and shall include constraint violations, WFE summary, sampler policy, Pareto selection method, PBO when enabled, pruning/partial-evidence behavior, and production/research threshold context.
- [X] No file-specific non-functional requirements defined.
- [X] No file-specific testing requirements defined.


### Hardening Amendments

#### Anti-overfitting and promotion governance

Requirements:

- [X] Adopt the Phase 1.5 `OptimizationCandidate` and `BacktestResult` contracts for all optimization outputs and evidence.
- [X] Require walk-forward or equivalent chronological validation for promotion-eligible optimization candidates.
- [X] Require IS/OOS split metadata, minimum trade count, robustness score, stability score, cost sensitivity, and slippage/spread sensitivity for promotion-eligible candidates.
- [X] Add multiple-comparison and data-snooping risk diagnostics where large parameter searches or strategy searches are performed.
- [X] Reject or flag candidates whose edge disappears after realistic costs, spread, slippage, latency, or execution constraints.
- [X] Ensure Optimization produces candidates, evidence packs, and recommendations only; it must not promote strategies, modify risk limits, or activate live trading directly.
- [X] Add tests proving optimization results cannot bypass Risk, Strategy Lifecycle, or human approval governance.

### Unit Tests Required

```text

tests/unit/app/services/optimization/

```

Test coverage:

- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text

tests/usage/app/services/09_optimization.py

```

Usage examples must show:

- `example_01_parameter_space`: Demonstrate parameter definitions, conditional parameters, validation, and candidate hashing.
- `example_02_grid_and_random_search`: Demonstrate grid/random sweeps, scoring functions, reproducibility, and progress callbacks.
- `example_03_bayesian_optimization`: Demonstrate Bayesian search wrapper, candidate ranking, and failure metadata.
- `example_04_genetic_algorithm`: Demonstrate population initialization, selection, crossover, mutation, elitism, and result ranking.
- `example_05_walk_forward_splits`: Demonstrate chronological, rolling, and expanding splits without leakage.
- `example_06_robustness_and_monte_carlo`: Demonstrate robustness checks, Monte Carlo runs, sensitivity summaries, and uncertainty metadata.
- `example_07_repository_and_resume`: Demonstrate optimization run persistence, resume, cancel, and idempotent progress lookup.
- `example_08_evidence_package`: Demonstrate reproducible optimization evidence packages and advisory-only boundaries.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 278 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text

feat(optimization-service): implement optimization parameter sweeps and genetic algorithms



- Implement Grid, Random, Bayesian, and Genetic search optimization algorithms

- Build parameter space definitions, checkpoints, and splitting matrices

- Setup parallel sweep runner and database optimization run repository

- Support walk-forward analysis and robustness scoring evaluation

```

- [X] Public service tools must not perform unbounded compute directly when their documented behavior is request packaging.
- [X] Public request-packaging API responses shall complete within an approved latency budget.
- [X] Proposed engineering baseline: execution-capable workflows should use a configurable default timeout of `30 minutes`, with overrides allowed only through approved resource profiles.
- [X] Large request payloads shall be rejected before expensive validation or execution with `OPT_PAYLOAD_TOO_LARGE` when they exceed configured size limits.
- [X] Generated reports, saved results, and logs must not expose secrets, credentials, broker tokens, private trade payloads, or authorization headers.
- [X] Resource overrides shall include approver, reason, requested cap, approved cap, timestamp, request ID, and workflow trust context in audit metadata.
- [X] Production signoff shall be blocked when required institutional evidence fields are missing or when performance benchmarks exceed configured limits without approved exception.
- [X] Public service tools shall return the documented standard optimization envelope containing `tool_name`, `status`, `request_id`, `data`, `errors`, `warnings`, `audit`, and `side_effects`; unit tests shall verify conformance to this contract.
- [X] Public service tools must include request/audit context including request ID, tool name, risk level, and approval requirement.
- [X] Public service tools must preserve business request payloads separately from standard context fields.
- [X] `dry_run` requested on a calculation-only public tool shall follow that tool contract and shall not change the calculation result except for side-effect metadata and audit context.
- [X] Public service tools must surface validation and runtime errors in structured result fields rather than uncaught exceptions.
- [X] Evidence package schemas shall be versioned and backward-compatible according to a documented compatibility policy.
- [X] `save_optimization_result` shall package optimization result metadata for downstream storage.
- [X] Sobol or Latin Hypercube unavailability shall be explicit and shall either return `OPT_SAMPLER_UNAVAILABLE` or use an approved configured fallback with sampler method, seed, scramble setting, fallback usage, and fallback reason recorded in evidence.
- [X] If average trade duration is known, effective embargo shall be at least the average trade duration in bars unless a stricter value is configured.
- [X] PBO shall be calculated when CPCV is enabled, and PBO above the configured threshold shall flag or reject overfit risk according to the workflow profile.
- [X] `calculate_probability_of_ruin` shall estimate probability that drawdown exceeds the configured ruin threshold.
- [X] `ParametricSimulationResult`, `PositionSizingResult`, `ConsecutiveLosingScenarioResult`, and `ProfitTargetScenarioResult` shall hold scenario-specific simulation results.
- [X] Prop-firm profiles shall be versioned configuration profiles and shall define rule-evaluation frequency as one of `per_tick`, `per_bar_close`, `per_trade_event`, `session_close`, or `end_of_day`.
- [X] Prop-firm compliance checks shall evaluate max daily loss, max exposure, and max correlated exposure at the configured intraday frequency when the selected profile requires intraday evidence.
- [X] `analyze_parallel_results` shall convert parallel optimization results into tabular analysis output.
- [X] Parallel processing must keep worker inputs serializable and preserve deterministic aggregation of results.
- [X] `PortfolioOptimizerResult` shall hold periodic portfolio weights and non-UI inspection metadata.
