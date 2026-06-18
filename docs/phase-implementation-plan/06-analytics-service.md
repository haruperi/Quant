## Phase 6 Analytics Service

### Goal

Implement the Analytics Service requirements under `app/services/analytics/` while preserving the phase module boundaries and governance rules.

Task inventory: 460 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

Required files:

```text

app/utils/__init__.py

app/utils/dataframe_tools.py

app/services/risk/__init__.py

```

Required functionality:

- Risk state records and trade log models are structured and readable.
- Lazy pandas dataframe operations are accessible for return calculations.
- Safe path traversal handles persistent report output storage.

### Files to Create

```text

app/services/analytics/

app/__init__.py

app/services/analytics/__init__.py

app/services/analytics/adapters.py

app/services/analytics/trade.py

app/services/analytics/equity.py

app/services/analytics/drawdown.py

app/services/analytics/risk.py

app/services/analytics/ratios.py

app/services/analytics/distributions.py

app/services/analytics/benchmark.py

app/services/analytics/efficiency.py

app/services/analytics/scorecard.py

app/services/analytics/report.py

app/services/analytics/dashboard.py

```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `app/services/analytics/models.py`

Functions/classes:

- `Request`
- `Result`
- `Config`
- `Metadata`

Requirements:

- [ ] Analytics functions must be read-only and side-effect free at the domain level.
- [ ] Importing the analytics registry should not perform live broker calls, network calls, database mutations, or trading side effects.
- [ ] Official tools must be stateless, retry-safe, and safe for parallel optimization or portfolio workflows.
- [ ] Metric kernels must not depend on mutable global calculation state.
- [ ] Local/read-through caches, if implemented, must define TTL, maximum size, eviction behavior, invalidation keys, lock timeout, stale-read behavior, and single-flight or equivalent thundering-herd prevention before Builder handoff.
- [ ] Distributed caching, distributed invalidation services, message queues, and async background workers must not be implemented inside Analytics.
- [ ] Portfolio aggregation must fail closed when required base-currency conversion is unavailable.
- [ ] The analytics registry must expose only intentional public analytics tools and must not hide colliding function names; duplicate concepts must use module-qualified aliases where needed.
- [ ] Every official exported analytics tool must be callable, documented, and accept a `request_id` parameter for traceability.
- [ ] Each official public capability must be labeled as stable, approved experimental, deprecated, or internal-support-only.
- [ ] Each official public capability must document whether it is safe for agent/API use.
- [ ] The analytics registry must distinguish official tools, internal metric kernels, compatibility aliases, and deprecated exports.
- [ ] Agentic workflows must import analytics capabilities from `app.services.analytics` rather than deep module files.
- [ ] Strategy-version mismatch must be handled explicitly during degradation pairing and must not be hidden inside aggregate scores.
- [ ] Low-sample explainability drivers must not appear in ranked driver lists.
- [ ] `common_avg_loss` shall expose the common-module average-loss function without colliding with metrics exports.
- [ ] `common_get_r_multiples` shall expose the common-module R-multiple function without colliding with metrics exports.
- [ ] `max_gross_size_held` shall calculate the maximum absolute total size held across positions.
- [ ] `percent_time_in_market` shall calculate percent of the trading period spent in the market.
- [ ] `metrics_get_r_multiples` shall expose metrics-module R-multiple behavior without colliding with common exports.
- [ ] `win_rate_fraction` shall calculate win rate on a 0-to-1 scale.
- [ ] `avg_win_loss` shall calculate mean winning and losing outcomes.
- [ ] `consecutive_wins_losses` shall calculate maximum consecutive wins and losses from numeric outcomes.
- [ ] `t_statistic` shall calculate the t-statistic for mean outcome.
- [ ] `open_position_pnl` shall calculate total unrealized PnL from open positions.
- [ ] `slippage_paid` shall calculate total absolute slippage costs paid.
- [ ] `commission_paid` shall calculate total absolute commission costs paid.
- [ ] `swap_paid` shall calculate total absolute swap costs paid.
- [ ] `metrics_avg_loss` shall expose metrics-module average-loss behavior without colliding with common exports.
- [ ] `expectancy_r` shall calculate R-expectancy.
- [ ] `max_size_held` shall calculate maximum total contracts held.
- [ ] `max_net_size_held` shall calculate maximum net directional size held.
- [ ] `max_long_size_held` shall calculate maximum total long contracts held.
- [ ] `max_short_size_held` shall calculate maximum total short contracts held.
- [ ] `avg_r_multiple` shall calculate average R-multiple.
- [ ] `median_r_multiple` shall calculate median R-multiple.
- [ ] `r_expectancy` shall calculate R-space expectancy.
- [ ] `max_r_multiple` shall calculate maximum R-multiple.
- [ ] `min_r_multiple` shall calculate minimum R-multiple.
- [ ] `avg_consecutive_wins` shall calculate average length of winning streaks.
- [ ] `avg_consecutive_losses` shall calculate average length of losing streaks.
- [ ] `r_signal_to_noise` shall calculate mean R relative to R volatility.
- [ ] `rolling_expectancy_stability` shall calculate expectancy stability over a rolling window.
- [ ] `win_after_win_probability` shall calculate probability that a win follows a win.
- [ ] `runs_test_zscore` shall calculate Wald-Wolfowitz runs-test z-score.
- [ ] `get_analytics_overview` shall calculate comprehensive analytics across all, long, and short subsets.
- [ ] `calculate_spread_cost_impact` shall calculate spread cost drag.
- [ ] `calculate_slippage_impact` shall calculate slippage cost drag.
- [ ] `calculate_commission_impact` shall calculate commission cost drag.
- [ ] `cagr` shall calculate compound annual growth rate.
- [ ] `compound_monthly_growth_rate` shall calculate compound monthly growth rate.
- [ ] `buy_and_hold_cagr` shall calculate buy-and-hold CAGR from price data.
- [ ] `adjusted_gross_profit` shall calculate adjusted gross profit.
- [ ] `adjusted_gross_loss` shall calculate adjusted gross loss.
- [ ] `adjusted_net_profit` shall calculate adjusted net profit.
- [ ] `select_net_profit` shall calculate net profit after outlier selection.
- [ ] `select_gross_profit` shall calculate gross profit after outlier selection.
- [ ] `select_gross_loss` shall calculate gross loss after outlier selection.
- [ ] `max_runup` shall calculate maximum gain from valley to peak.
- [ ] `max_runup_date` shall identify the timestamp of maximum runup peak.
- [ ] `calculate_period_analysis` shall calculate performance by timestamp bucket.
- [ ] `calculate_long_short_split` shall calculate long-versus-short profit split.
- [ ] `calculate_session_performance` shall calculate session performance from timestamped records.
- [ ] `whites_reality_check` shall assess data-snooping bias with White's Reality Check.
- [ ] `probability_of_backtest_overfitting` shall estimate probability of backtest overfitting.
- [ ] `walk_forward_degradation_score` shall measure performance decay from in-sample to out-of-sample scores.
- [ ] `bonferroni_correction` shall apply Bonferroni correction for multiple hypothesis testing.
- [ ] `benjamini_hochberg_correction` shall apply Benjamini-Hochberg false-discovery-rate control.
- [ ] `stability_score` shall calculate performance consistency across walk-forward windows.
- [ ] `whites_reality_check_backtests` shall run White's Reality Check against backtest result objects.
- [ ] Documentation must include success examples for each approved official high-level tool.
- [ ] Documentation must include validation-failure examples showing the standard error envelope.
- [ ] Low-level metric examples must be labeled as internal/developer examples when they are not official agent/API tools.

#### `app/__init__.py`

Functions/classes:

- `total_return`
- `return_on_initial_capital`
- `MetricDefinitionCatalog`

Requirements:

- [ ] Undefined or unsupported metric values must be represented as omitted fields or `None` according to the output schema plus structured warnings or skipped-section metadata; they must not be serialized as `NaN`, infinity, fabricated zero, or display-only caps.
- [ ] R-multiple fallback proxies must be listed in the Metric Definition Catalog before use; fallback-derived R-multiple values must include warning metadata and mark the affected metric confidence as degraded.
- [ ] Every official metric must define formula, units, required inputs, optional inputs, accepted aliases, return scale, annualization basis, sample/population convention, minimum sample size, undefined-result behavior, and golden-fixture expectations.
- [ ] `total_return` shall calculate total return as a percentage of initial capital.
- [ ] `return_on_initial_capital` shall calculate net profit as a percentage of initial capital.
- [ ] Numeric outputs must avoid misleading precision and must handle empty, missing, non-finite, zero-denominator, and insufficient-sample scenarios consistently.
- [ ] Documentation must include the Metric Definition Catalog.
- [ ] Official Analytics Tool Catalog is approved and maps every official tool to schemas, errors, metadata, side effects, stability, and tests.
- [ ] Metric Definition Catalog is approved and no official schema references uncataloged metrics.
- [ ] Public/internal export classification is approved, including compatibility aliases and deprecated exports.
- [ ] Analytics-owned private canonical metric-kernel model is documented and enforced through public/internal export classification tests.
- [ ] Schema compatibility matrix defines accepted, deprecated, legacy-adapted, rejected, and unsupported future versions.
- [ ] Decimal monetary precision mandate and deterministic derived-ratio tolerance policy are documented in schemas, metadata, and tests.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.

#### `app/services/analytics/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] No file-specific functional requirements defined. Foundation properties apply.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.

#### `app/services/analytics/adapters.py`

Functions/classes:

- `BacktestResult`
- `PaperTradingResult`
- `LiveTradingResult`
- `TradingResult`

Requirements:

- [ ] Backtest, paper, live, portfolio, and normalized trading results must either inherit from a canonical `TradingResult` contract or be converted into it through deterministic adapters.
- [ ] Deterministic adapters must preserve schema version, result ID, phase/environment, timestamps, account base currency, strategy identifiers, symbols, timeframe, trades, equity curve, optional balance curve, benchmark data, upstream quality metadata, and source metadata without silent field loss.
- [ ] Deterministic adapters must define source-to-canonical field mappings, required fields, optional fields, defaulting behavior, unsupported-field behavior, lossless metadata preservation rules, and warning/error behavior for missing or incompatible fields.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Documentation must include adapter field-mapping tables for every supported upstream result type.

#### `app/services/analytics/trade.py`

Functions/classes:

- `AnalyticsReport`
- `build_analytics_report`
- `build_portfolio_analytics_report`
- `calculate_trade_metrics`
- `calculate_equity_metrics`
- `calculate_drawdown_metrics`
- `calculate_risk_metrics`
- `calculate_benchmark_metrics`
- `calculate_statistical_validation`
- `calculate_prop_firm_compliance`
- `get_r_multiples`
- `calculate_efficiency_metrics`
- `compute_r_trade_metrics`
- `compute_trade_metrics`
- `calculate_analytics_for_subset`

Requirements:

- [ ] Official analytics tools must not write files, modify databases, place trades, or require network access.
- [ ] Analytics input conversion must support common developer inputs such as pandas dataframes, pandas series, lists of trade records, and lists of numeric values where the public capability expects them.
- [ ] Trade-oriented tools must use closed-trade semantics when a metric is defined over realized results.
- [ ] Closed-trade filtering must exclude records explicitly marked as still open or end-of-data placeholders and must ignore records without close timestamps when close timestamps are required.
- [ ] Trade classification must distinguish wins, losses, and breakevens using a configured `breakeven_epsilon` from the Metric Definition Catalog or numeric policy ADR so near-zero PnL does not become a false win or loss.
- [ ] Exposure and time-in-market analytics must merge overlapping trade intervals so simultaneous positions are measured as market presence once for duration metrics.
- [ ] Long/short split analytics must classify direction using the supplied trade direction/type fields and must not infer trade direction from PnL.
- [ ] Cost-impact analytics must quantify spread, slippage, and commission drag from supplied cost and gross-profit inputs without mutating the source trades.
- [ ] Aggregated analytics must preserve source context enough for downstream consumers to know whether inputs came from all trades, long trades, short trades, benchmark comparisons, cost analysis, or statistical validation.
- [ ] `AnalyticsReport` output must include summary, trade metrics, equity metrics, return metrics, drawdown metrics, risk metrics, ratio metrics, distribution metrics, benchmark metrics, efficiency metrics, statistical validation, cost breakdown, warnings, quality flags, dashboard payloads, lineage, and metadata when those sections are applicable.
- [ ] Report hashes must include deterministic input hash, config hash, report hash, trade ledger hash, equity curve hash, and optional benchmark hash where the source material exists.
- [ ] ADR Required: `ADR-ANALYTICS-PUBLIC-SURFACE` must approve the initial official high-level tool surface before Builder implementation; candidate tools include `build_analytics_report`, `build_portfolio_analytics_report`, `evaluate_strategy_quality`, `compare_analytics_reports`, `calculate_trade_metrics`, `calculate_equity_metrics`, `calculate_drawdown_metrics`, `calculate_risk_metrics`, `calculate_benchmark_metrics`, `calculate_statistical_validation`, and `calculate_prop_firm_compliance`.
- [ ] Candidate dashboard payloads include summary cards, equity curve chart, drawdown curve chart, monthly returns heatmap, rolling ratio charts, rolling drawdown chart, trade distribution chart, cost breakdown chart, symbol contribution chart, warning table, and quality flag table when source sections exist.
- [ ] `get_closed_trades` shall filter trade records to realized closed trades.
- [ ] `classify_trades` shall classify trades into wins, losses, and breakevens using a consistent threshold.
- [ ] `avg_loss` shall calculate the mean loss of losing trades.
- [ ] `get_r_multiples` shall calculate R-multiples for trades.
- [ ] `trade_pnl_distribution` shall calculate a statistical summary of realized trade PnL.
- [ ] `trade_level_drawdowns` shall calculate cumulative PnL drawdowns at trade close points.
- [ ] `max_close_to_close_drawdown` shall calculate maximum trade-level peak-to-valley decline including excursion context where available.
- [ ] `avg_trade_drawdown` shall calculate mean trade-level close-to-close drawdown depth.
- [ ] `max_consecutive_drawdown_trades` shall calculate maximum number of consecutive trades inside a strategy drawdown.
- [ ] `max_close_to_close_drawdown_date` shall identify the timestamp of deepest trade-level valley.
- [ ] `avg_trade_notional_efficiency` shall provide the capital-efficiency metric under a clearer average-trade-notional name.
- [ ] `avg_return_per_risk_unit` shall calculate average R-multiple per closed trade.
- [ ] `return_per_trade_hour` shall calculate net profit per hour spent in active trades.
- [ ] `return_per_market_hour` shall calculate net profit per hour where at least one trade was open.
- [ ] `trades_per_day` shall calculate average number of closed trades per calendar day in the test period.
- [ ] `profit_per_trade_per_day` shall calculate net profit normalized by both number of trades and calendar days.
- [ ] `mfe_efficiency` shall calculate average percentage of MFE captured by winning trades.
- [ ] `aggregate_mfe_capture_ratio` shall calculate aggregate MFE capture ratio for winning trades.
- [ ] `mae_efficiency` shall calculate realized-loss-to-MAE efficiency for losing trades.
- [ ] `aggregate_loss_containment_efficiency` shall calculate aggregate loss containment for losing trades.
- [ ] `position_size_efficiency` shall calculate relationship between position size and normalized trade outcome.
- [ ] `calculate_efficiency_metrics` shall calculate aggregate MAE/MFE efficiency context from trades.
- [ ] `get_ordered_closed_trades` shall filter closed trades and sort them for sequence-dependent metrics.
- [ ] `total_trades` shall count closed trades.
- [ ] `winning_trades` shall count closed winning trades.
- [ ] `losing_trades` shall count closed losing trades.
- [ ] `breakeven_trades` shall count closed breakeven trades.
- [ ] `long_trades` shall count closed long trades.
- [ ] `short_trades` shall count closed short trades.
- [ ] `count_open_trades` shall count currently open trades.
- [ ] `win_rate` shall calculate percentage of winning trades.
- [ ] `loss_rate` shall calculate percentage of losing trades.
- [ ] `avg_win` shall calculate mean profit of winning trades.
- [ ] `largest_win` shall calculate maximum single-trade profit.
- [ ] `largest_loss` shall calculate maximum single-trade loss.
- [ ] `median_win` shall calculate median PnL of winning trades.
- [ ] `median_loss` shall calculate median PnL of losing trades.
- [ ] `expectancy` shall calculate trade expectancy.
- [ ] `max_consecutive_wins` shall calculate maximum consecutive winning trades.
- [ ] `max_consecutive_losses` shall calculate maximum consecutive losing trades.
- [ ] `avg_time_in_trade` shall calculate average trade duration.
- [ ] `median_time_in_trade` shall calculate median trade duration.
- [ ] `max_time_in_trade` shall calculate maximum trade duration.
- [ ] `min_time_in_trade` shall calculate minimum trade duration.
- [ ] `compute_r_trade_metrics` shall calculate trade metrics from R-multiple inputs.
- [ ] `compute_trade_metrics` shall calculate trade metrics from numeric R values and optional MAE/MFE arrays.
- [ ] `trade_efficiency` shall calculate realized outcome relative to maximum favorable excursion.
- [ ] `trade_outcome_entropy` shall calculate Shannon entropy of trade outcomes.
- [ ] `longest_flat_period_duration` shall calculate longest period without an active trade.
- [ ] `calculate_trade_metrics` shall calculate aggregate core trade metrics from normalized trade records.
- [ ] `calculate_analytics_for_subset` shall calculate all analytics categories for a supplied trade subset.
- [ ] `return_over_drawdown` shall calculate total return relative to maximum trade drawdown.
- [ ] `net_profit_as_percent_of_max_trade_drawdown` shall calculate net profit as a percentage of max trade drawdown.
- [ ] `select_net_profit_as_percent_of_max_trade_drawdown` shall calculate selected net profit as a percentage of max trade drawdown.
- [ ] `adjusted_net_profit_as_percent_of_max_trade_drawdown` shall calculate adjusted net profit as a percentage of max trade drawdown.
- [ ] `net_profit` shall calculate total realized profit or loss from closed trades.
- [ ] `gross_profit` shall sum winning closed-trade profit.
- [ ] `gross_loss` shall sum losing closed-trade loss.
- [ ] `balance_curve_from_closed_trades` shall generate a realized balance curve from closed trades.
- [ ] `balance_curve` shall expose balance-curve behavior as an alias of closed-trade balance curve generation.
- [ ] `equity_curve` shall expose equity-curve behavior for common orchestration using the closed-trade curve.
- [ ] `max_loss_probability` shall calculate probability of a single trade loss exceeding a threshold.
- [ ] `risk_of_ruin` shall estimate ruin probability through Monte Carlo simulation of trade outcomes.
- [ ] `avg_trade_nominal_exposure` shall calculate average nominal exposure per trade.
- [ ] `max_single_trade_margin_utilization` shall calculate maximum margin used by a single trade as a percentage of equity.
- [ ] `avg_single_trade_margin_utilization` shall calculate average margin used per trade as a percentage of equity.
- [ ] `risk_of_ruin_with_custom_horizon` shall estimate ruin probability over a fixed future trade horizon.
- [ ] The module must define concrete maximum accepted input sizes for trades, equity points, benchmark points, portfolio components, dashboard payloads, and statistical observations before production handoff.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.

#### `app/services/analytics/equity.py`

Functions/classes:

- `NaT`
- `Infinity`
- `VALIDATION_FAILED`
- `calculate_drawdown_metrics`
- `compute_equity_metrics`
- `calculate_return_metrics`

Requirements:

- [ ] Equity and return analytics must sort and normalize supplied series deterministically; optional `NaN`/`NaT` observations may be filtered only with recorded warning metadata, required `NaN`/`NaT` fields must fail validation unless the Metric Definition Catalog marks them skippable, and `Infinity`/`-Infinity` at official boundaries must return `VALIDATION_FAILED`.
- [ ] Dashboard truncation/downsampling must be deterministic and must preserve first point, last point, local extrema where practical, drawdown troughs, equity highs, and timestamps associated with major, critical, or blocker warnings.
- [ ] `benchmark_returns` shall generate a return series from benchmark equity or price values.
- [ ] `relative_drawdown_series` shall generate relative underperformance between strategy and benchmark equity.
- [ ] `drawdown_series` shall calculate drawdown values from an equity curve.
- [ ] `drawdown_duration_series` shall calculate drawdown duration values from an equity curve.
- [ ] `max_drawdown_duration_from_equity` shall calculate maximum drawdown duration from equity values.
- [ ] `max_strategy_drawdown_date` shall identify the timestamp of deepest strategy equity valley.
- [ ] `avg_underwater_drawdown_percent` shall calculate average drawdown depth while equity is below peak.
- [ ] `calculate_drawdown_metrics` shall calculate aggregate drawdown metrics from an equity curve.
- [ ] `compute_equity_metrics` shall calculate equity metrics from return inputs.
- [ ] `total_return_usd` shall calculate total return in currency units from an equity curve.
- [ ] `returns_series` shall calculate percentage returns between equity points.
- [ ] `log_returns_series` shall calculate logarithmic returns between equity points.
- [ ] `daily_returns` shall calculate daily percentage returns from an equity curve.
- [ ] `weekly_returns` shall calculate weekly percentage returns from an equity curve.
- [ ] `monthly_returns` shall calculate monthly percentage returns from an equity curve.
- [ ] `annual_returns` shall calculate annual percentage returns from an equity curve.
- [ ] `calculate_return_metrics` shall calculate aggregate cumulative and average returns from an equity curve.
- [ ] No file-specific non-functional requirements defined.
- [ ] Official analytics tools must validate `request_id`; missing, empty, malformed, or unsafe request IDs must return a structured validation error envelope.
- [ ] Official analytics tools must return the standard tool envelope on success and on controlled validation failure.
- [ ] Date/time analytics must parse supplied open/close timestamps, support both datetime-like and numeric timestamp inputs where implemented, and return JSON-safe values for durations and timestamps.
- [ ] Live-vs-backtest and paper-vs-backtest degradation comparisons must validate strategy ID, strategy version, symbols, timeframe or return frequency, evaluation window, account base currency, and comparable cost/slippage model metadata before pairing.
- [ ] `win_loss_streaks` shall return winning and losing streak sequences.
- [ ] `kelly_criterion` shall calculate Kelly criterion percentage from R-multiples or returns.
- [ ] `avg_monthly_return` shall calculate arithmetic average monthly return.
- [ ] `monthly_return_stddev` shall calculate monthly return volatility.
- [ ] `annualized_return` shall calculate geometric annualized return.
- [ ] `geometric_mean_return` shall calculate geometric mean return.
- [ ] `best_return` shall calculate best single-period return.
- [ ] `worst_return` shall calculate worst single-period return.
- [ ] `buy_and_hold_return` shall calculate total buy-and-hold return from price data.
- [ ] `return_volatility` shall calculate return standard deviation.
- [ ] `downside_return_volatility` shall calculate volatility of returns below target.
- [ ] `return_skewness` shall calculate return-distribution skewness.
- [ ] `return_kurtosis` shall calculate return-distribution excess kurtosis.
- [ ] `return_on_account` shall calculate return on required account size.

#### `app/services/analytics/drawdown.py`

Functions/classes:

- `calculate_drawdown_series`
- `max_drawdown`
- `drawdown_duration`
- `drawdown_recovery`
- `underwater_curve`

Requirements:

- [ ] Strategy-quality evaluation must rely only on the supplied report payload and must surface warnings for weak profitability, high drawdown, overfitting risk, small sample size, or other observable quality concerns.
- [ ] Optional sections such as TCA metrics, attribution, prop-firm compliance evidence, drawdown distribution, tail-risk metrics, dynamic correlation, walk-forward analytics, metric comparisons, live degradation, and explainability must be represented as calculated, skipped, or failed.
- [ ] Formula definitions must be explicit for Sharpe, Sortino, Calmar, Jensen alpha, beta, tracking error, information ratio, VaR, CVaR, expected shortfall, SQN, Kelly, drawdown duration, CAGR, profit factor, expectancy, and R-multiple metrics before those metrics are locked as official contracts.
- [ ] `max_relative_drawdown_percent` shall calculate maximum relative underperformance as a positive percentage.
- [ ] `max_strategy_drawdown` shall calculate deepest peak-to-valley decline in currency units.
- [ ] `max_strategy_drawdown_percent` shall calculate deepest percentage decline relative to running peak.
- [ ] `max_drawdown` shall calculate maximum drawdown from returns.
- [ ] `avg_drawdown` shall calculate average drawdown depth.
- [ ] `drawdown_distribution` shall calculate detailed drawdown distribution statistics.
- [ ] `max_drawdown_duration_from_returns` shall calculate maximum drawdown duration from return values.
- [ ] `max_drawdown_duration` shall calculate maximum drawdown duration from the selected input type.
- [ ] `avg_drawdown_duration` shall calculate average duration of drawdown episodes.
- [ ] `time_to_recovery` shall calculate recovery periods for unique drawdowns.
- [ ] `recovery_factor` shall calculate net profit relative to maximum drawdown.
- [ ] `max_close_to_close_drawdown_percent` shall calculate close-to-close drawdown as a percentage.
- [ ] `account_size_required` shall estimate capital required to withstand max close-to-close dips.
- [ ] `avg_yearly_max_drawdown` shall average the maximum drawdown observed in each year.
- [ ] `ulcer_index` shall calculate squared-drawdown-based ulcer index.
- [ ] `pain_index` shall calculate mean absolute percentage drawdown.
- [ ] `pain_ratio` shall calculate return relative to pain index.
- [ ] `calmar_ratio` shall calculate annualized return relative to maximum drawdown.
- [ ] `fouse_ratio` shall calculate Fouse drawdown-index-style ratio.
- [ ] `sterling_ratio` shall calculate CAGR relative to adjusted average yearly maximum drawdown.
- [ ] `rina_index` shall calculate select net profit relative to average drawdown and time in market.
- [ ] `net_profit_as_percent_of_max_strategy_drawdown` shall calculate net profit as a percentage of max strategy drawdown.
- [ ] `select_net_profit_as_percent_of_max_strategy_drawdown` shall calculate selected net profit as a percentage of max strategy drawdown.
- [ ] `adjusted_net_profit_as_percent_of_max_strategy_drawdown` shall calculate adjusted net profit as a percentage of max strategy drawdown.
- [ ] `return_on_max_strategy_drawdown` shall calculate total return relative to maximum strategy drawdown.
- [ ] `return_on_max_close_to_close_drawdown` shall calculate net profit relative to maximum close-to-close drawdown.
- [ ] `drawdown_probability` shall calculate probability of drawdown exceeding a threshold.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.

#### `app/services/analytics/risk.py`

Functions/classes:

- `calculate_risk_metrics`

Requirements:

- [ ] Official analytics tools must be low-risk, read-only operations.
- [ ] Metadata must include tool name, tool version, tool category, tool risk level, request ID, execution time, and side-effect flags.
- [ ] R-multiple analytics must prefer explicit initial-risk fields when available and fall back only to documented analytics proxies when risk fields are absent.
- [ ] Official analytics tool responses must include metadata, side-effect flags, risk flags, execution timing, and structured errors.
- [ ] Metric definitions must document default configuration sources for annualization, risk-free rate, breakeven tolerance, minimum sample size, bootstrap count limits, dashboard limits, FX stale-rate limits, and confidence/alpha levels when those defaults are approved.
- [ ] Strategy-quality scorecards must not make final live approval, promotion, prop-firm enforcement, or risk-governor decisions.
- [ ] Strategy-quality outputs must not claim final approval, promotion, live-readiness, prop-firm compliance enforcement, risk-limit approval, or portfolio allocation authority.
- [ ] `risk_adjusted_efficiency` shall calculate return relative to total defined initial risk.
- [ ] `profit_per_pip_risk` shall calculate reward-to-risk based on profit pips relative to MAE pips.
- [ ] `upside_potential_ratio` shall calculate upside potential relative to downside risk.
- [ ] `volatility` shall calculate return standard deviation as a positive percentage.
- [ ] `annualized_volatility` shall calculate annualized volatility as a positive percentage.
- [ ] `downside_volatility` shall calculate downside deviation as a positive percentage.
- [ ] `value_at_risk` shall calculate value-at-risk as a positive percentage.
- [ ] `conditional_var` shall calculate conditional value-at-risk as a positive percentage.
- [ ] `expected_shortfall` shall calculate expected shortfall.
- [ ] `max_nominal_exposure_simple` shall calculate maximum nominal exposure held at one time.
- [ ] `max_gross_exposure` shall calculate maximum gross nominal exposure.
- [ ] `exposure_time_ratio` shall calculate percentage of total period spent in market.
- [ ] `time_weighted_avg_exposure` shall calculate time-weighted average notional exposure.
- [ ] `portfolio_margin_utilization_curve` shall generate portfolio margin-utilization curve over time.
- [ ] `compounding_risk_of_ruin` shall estimate ruin probability with dynamic compounding risk.
- [ ] `historical_var_by_symbol` shall calculate historical value-at-risk by symbol.
- [ ] `portfolio_var_from_covariance` shall calculate portfolio value-at-risk from covariance and weights.
- [ ] `calculate_risk_metrics` shall calculate aggregate risk metrics such as VaR, CVaR, and volatility.
- [ ] Tool metadata must consistently identify the category as `analytics` and risk level as `low`.
- [ ] Analytics input and output contracts must remain aligned with Simulation, Optimization, Risk, Portfolio, Trading receipt, and UI/API contracts.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Redaction rules must apply to sensitive keys and sensitive-looking values in inputs, warnings, errors, logs, metadata, and diagnostic details.
- [ ] Low-level metric helpers such as individual average, skewness, kurtosis, tail-ratio, tracking-error, ulcer-index, omega-ratio, payoff-ratio, and date helper functions must remain internal/support-only unless explicitly promoted by the Official Analytics Tool Catalog.
- [ ] Warnings and quality flags must include code, severity, affected section, source context, and enough bounded detail for downstream review.
- [ ] Warning and quality-flag catalogs must define code, severity, affected section, source-backed status, whether the flag blocks promotion, bounded detail rules, and linked test fixtures.
- [ ] Explainability outputs must distinguish explained PnL, unexplained PnL, explained variance percentage, sample count, and driver stability when those inputs are supplied.

#### `app/services/analytics/ratios.py`

Functions/classes:

- `calculate_ratio_metrics`

Requirements:

- [ ] `benchmark_information_ratio` shall expose benchmark information ratio without colliding with the ratios module export.
- [ ] `up_down_capture` shall calculate up-capture and down-capture ratios.
- [ ] `metrics_win_rate_fraction` shall expose metrics-module win-rate fraction behavior without colliding with ratios exports.
- [ ] `metrics_expectancy` shall expose metrics-module expectancy behavior without colliding with ratios exports.
- [ ] `metrics_expectancy_r` shall expose metrics-module R-expectancy behavior without colliding with ratios exports.
- [ ] `ratios_win_rate_fraction` shall expose ratios-module win-rate fraction behavior without colliding with metrics exports.
- [ ] `sharpe_ratio` shall calculate excess return per unit of volatility.
- [ ] `annualized_sharpe_ratio` shall calculate annualized Sharpe ratio from monthly inputs.
- [ ] `sortino_ratio` shall calculate excess return per unit of downside volatility.
- [ ] `ratios_information_ratio` shall expose ratios-module information ratio without colliding with benchmark exports.
- [ ] `omega_ratio` shall calculate probability-weighted gains relative to losses.
- [ ] `gain_to_pain_ratio` shall calculate gains relative to absolute negative returns.
- [ ] `kappa_ratio` shall calculate generalized Sortino-style Kappa ratio.
- [ ] `profit_factor` shall calculate gross profit relative to gross loss.
- [ ] `payoff_ratio` shall calculate average win relative to average loss.
- [ ] `edge_ratio` shall calculate payoff edge adjusted by win rate.
- [ ] `profit_to_mae_ratio` shall calculate profit capture relative to adverse excursion.
- [ ] `mfe_to_mae_ratio` shall calculate favorable excursion relative to adverse excursion.
- [ ] `expectancy_over_std` shall calculate expectancy stability relative to standard deviation.
- [ ] `net_profit_as_percent_of_largest_loss` shall calculate net profit as a percentage of largest loss.
- [ ] `select_net_profit_as_percent_of_largest_loss` shall calculate selected net profit as a percentage of largest loss.
- [ ] `adjusted_net_profit_as_percent_of_largest_loss` shall calculate adjusted net profit as a percentage of largest loss.
- [ ] `adjusted_profit_factor` shall calculate adjusted gross profit relative to adjusted gross loss.
- [ ] `select_profit_factor` shall calculate selected gross profit relative to selected gross loss.
- [ ] `ratios_expectancy` shall expose ratios-module expectancy behavior without colliding with metrics exports.
- [ ] `ratios_expectancy_r` shall expose ratios-module R-expectancy behavior without colliding with metrics exports.
- [ ] `calculate_ratio_metrics` shall calculate aggregate ratio metrics from return values.
- [ ] Architectural Mandate: derived ratios may use deterministic `float64` arithmetic only where exact decimal arithmetic is not appropriate, with documented tolerance stored in configuration, tests, and report metadata.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] The module must degrade safely when optional acceleration libraries are unavailable.
- [ ] Calculations over large datasets must use vectorized operations where feasible and must degrade to bounded chunked processing with warnings when vectorization or memory limits are exceeded.
- [ ] Shared caches, if implemented, must be concurrency-safe or read-through and keyed by input hash, configuration hash, and analytics engine version.
- [ ] Long-series cumulative operations must use numerically stable methods where feasible and must document any approximation or chunking behavior.
- [ ] Duplicate timestamps must be rejected or resolved deterministically according to configuration and recorded in diagnostics.
- [ ] Invalid or missing required inputs must fail with a structured error envelope, not an uncaught exception. Custom analytics exceptions and error codes must inherit and reuse exceptions from `app.utils.errors` to prevent duplicate declaration.
- [ ] `time_in_market_duration` shall calculate total duration where at least one position was open.
- [ ] `trading_period_duration` shall calculate total duration of the trading period.
- [ ] `deflated_sharpe_ratio` shall adjust Sharpe ratio diagnostics for multiple testing and non-normality.

#### `app/services/analytics/distributions.py`

Functions/classes:

- `calculate_distribution_metrics`

Requirements:

- [ ] `return_distribution` shall calculate a statistical summary of returns.
- [ ] `r_multiple_distribution` shall calculate a statistical summary of R-multiple values.
- [ ] `distributions_r_multiple_distribution` shall expose distribution-module R-multiple distribution behavior without colliding with metrics exports.
- [ ] `percentile_summary` shall return selected percentile values.
- [ ] `upside_downside_summary` shall summarize positive and negative outcome distributions.
- [ ] `skewness` shall calculate return or value skewness.
- [ ] `kurtosis` shall calculate excess kurtosis.
- [ ] `higher_moments` shall calculate detailed skewness and kurtosis context.
- [ ] `fat_tail_score` shall estimate tail heaviness relative to normal behavior.
- [ ] `tail_ratio` shall calculate the ratio between upper-tail and lower-tail percentile magnitudes.
- [ ] `jarque_bera_test` shall run a Jarque-Bera normality diagnostic.
- [ ] `shapiro_wilk_test` shall run a Shapiro-Wilk normality diagnostic.
- [ ] `qq_plot_data` shall generate theoretical and actual quantile data for Q-Q plotting.
- [ ] `fit_distribution` shall fit a theoretical distribution and return fit parameters.
- [ ] `distribution_fit_quality` shall return fit-quality diagnostics such as likelihood and information criteria.
- [ ] `histogram_data` shall generate histogram bin data for plotting.
- [ ] `detect_outliers` shall identify outliers with the requested method and threshold.
- [ ] `outlier_ratio` shall calculate the percentage of data points flagged as outliers.
- [ ] `calculate_distribution_metrics` shall calculate aggregate distribution metrics from numeric values.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Analytics behavior must be deterministic for the same inputs except where Monte Carlo, bootstrap, or permutation features intentionally use randomness; those features should support explicit seeds.
- [ ] Statistical validation tools must expose deterministic options such as seeds, bootstrap/permutation counts, block sizes, confidence levels, alpha levels, and sample-size thresholds where supported.
- [ ] `metrics_r_multiple_distribution` shall calculate R-multiple distribution statistics.
- [ ] `permutation_test` shall run significance testing through random reshuffling or sign-flipping.
- [ ] `bootstrap_confidence_intervals` shall estimate metric uncertainty with non-parametric bootstrap.
- [ ] `bootstrap_probability_above_threshold` shall estimate probability that a bootstrapped metric exceeds a threshold.
- [ ] `permutation_test_backtest` shall run permutation testing against a backtest result object.
- [ ] `bootstrap_confidence_intervals_backtest` shall estimate bootstrap confidence intervals from a backtest result object.

#### `app/services/analytics/benchmark.py`

Functions/classes:

- `calculate_benchmark_metrics`

Requirements:

- [ ] Benchmark analytics must align strategy and benchmark return streams before comparison and must handle missing or non-overlapping periods safely.
- [ ] Benchmark metrics must only be calculated after deterministic alignment of strategy and benchmark series.
- [ ] Strategy and benchmark timestamps must be normalized to UTC before alignment.
- [ ] Benchmark data must be restricted to the strategy analytics window unless explicit lookback is configured and recorded.
- [ ] Missing benchmark currency metadata must emit a warning and restrict calculations to currency-neutral metrics unless a validated currency policy exists.
- [ ] Portfolio analytics must not sum raw PnL across different profit currencies.
- [ ] Portfolio, TCA, and base-currency analytics must require validated FX conversion data when source money values are in different currencies.
- [ ] Missing required FX conversion data must produce blocker-level quality evidence for affected multi-currency portfolio or TCA sections.
- [ ] Stale FX rates must be identified when FX age limits are configured, and affected converted values must be marked as estimated when stale data is used.
- [ ] All money fields must include explicit currency or inherit a validated account base currency with lineage explaining the inheritance.
- [ ] `beta` shall calculate the strategy beta coefficient relative to benchmark returns.
- [ ] `alpha` shall calculate annualized Jensen-style alpha relative to benchmark returns.
- [ ] `r_squared` shall calculate coefficient of determination between strategy and benchmark returns.
- [ ] `tracking_error` shall calculate annualized tracking error between strategy and benchmark returns.
- [ ] `information_ratio` shall calculate relative Sharpe-style information ratio.
- [ ] `batting_average` shall calculate the percentage of periods where the strategy outperformed the benchmark.
- [ ] `calculate_benchmark_metrics` shall calculate combined benchmark-relative metrics such as alpha and beta.
- [ ] The module must not overstate strategy quality, robustness, or live readiness; report outputs should expose caveats where sample size, overfitting, missing benchmark, or partial data weaken confidence.
- [ ] All timestamps must be timezone-aware or explicitly normalized to UTC before metric calculation, benchmark alignment, report hashing, or dashboard payload generation.
- [ ] ADR Required: `ADR-ANALYTICS-LIMITS` must record exact maximum input sizes, response payload limits, runtime budgets, memory budgets, statistical iteration limits, dashboard point limits, reference hardware, and benchmark method before Builder handoff.
- [ ] Performance benchmark tests must fail the handoff gate until `ADR-ANALYTICS-LIMITS` supplies exact dataset sizes, hardware profile, benchmark method, runtime thresholds, memory thresholds, and statistical-validation iteration limits.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.

#### `app/services/analytics/efficiency.py`

Functions/classes:

- `capital_efficiency`
- `return_per_unit_mae`
- `return_per_unit_mfe`
- `exposure_efficiency`

Requirements:

- [ ] `capital_efficiency` shall calculate return per unit of nominal capital deployed.
- [ ] `return_per_unit_mae` shall calculate total return relative to adverse excursion experienced.
- [ ] `return_per_calendar_day` shall calculate net profit per calendar day in the test period.
- [ ] `exit_efficiency` shall calculate combined win-capture and loss-containment efficiency.
- [ ] `loss_containment_efficiency` shall calculate how well realized losses stayed above their adverse excursion.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] `median_mae_mfe` shall calculate median MAE and MFE values.
- [ ] `get_mae_mfe_r` shall calculate MAE and MFE normalized to R-space.
- [ ] `median_mae_r` shall calculate median MAE in R-multiple terms.
- [ ] `median_mfe_r` shall calculate median MFE in R-multiple terms.

#### `app/services/analytics/scorecard.py`

Functions/classes:

- `MetricDefinition`
- `ScorecardRule`
- `ScorecardResult`
- `evaluate_scorecard`
- `validate_metric_catalog`

Requirements:

- [ ] No metric may be referenced in an official tool schema, report schema, dashboard payload, scorecard rule, warning rule, or quality-flag rule until its Metric Definition Catalog entry is approved.
- [ ] Metric definitions must document whether outputs are calculated facts, diagnostic estimates, warning evidence, scorecard inputs, or non-binding review context.
- [ ] `evaluate_strategy_quality` shall evaluate a supplied analytics report and return strategy-quality decision context, score, strengths, warnings, and recommended action.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.
- [ ] Public registry changes must remain auditable through tests and catalog updates.
- [ ] The module must separate calculated facts from warnings, caveats, decisions, and recommended actions.
- [ ] Official agent/API-facing analytics tools must be high-level, documented, typed, schema-compliant, traceable, and listed in the Official Analytics Tool Catalog.
- [ ] Every official analytics tool must have a documented input schema and output schema, including required fields, optional fields, default values, accepted aliases, units, validation errors, warning codes, and JSON-safe serialization behavior.
- [ ] Low-level metric kernels must not be exposed as official agent/API tools unless explicitly approved in the Official Analytics Tool Catalog.
- [ ] Official analytics tools must log call start, validation failure, successful completion, controlled warning, and execution failure without logging secrets or full raw private payloads.
- [ ] Warning severity must support at least informational, warning, major, critical, and blocker-level meanings.
- [ ] Quality flags must separate raw metrics, normalized score inputs, penalty flags, hard blockers, recommendation evidence, and final governance decisions.
- [ ] Strategy-quality and prop-firm outputs must be labeled as non-binding analytics evidence or decision context only.
- [ ] `sqn` shall calculate system quality number.
- [ ] `sample_size_warning` shall assess metric reliability based on sample size.
- [ ] Documentation must include the Official Analytics Tool Catalog.
- [ ] Documentation must include the warning-code and quality-flag catalog.

#### `app/services/analytics/report.py`

Functions/classes:

- `AnalyticsReport`
- `PortfolioAnalyticsReport`

Requirements:

- [ ] Overview/report tools must combine lower-level analytics into grouped payloads that remain serializable for API and dashboard consumers.
- [ ] The module must generate a complete, versioned `AnalyticsReport` from a valid backtest, optimization candidate, out-of-sample, walk-forward, paper, live, or normalized trading result when required inputs are available.
- [ ] Report building must validate inputs, normalize result data, run required metric groups, run optional metric groups, collect warnings and quality flags, build dashboard payloads, validate output, compute hashes, and return a standard tool response.
- [ ] Missing optional inputs must produce warnings or skipped-section metadata rather than fabricated metric values.
- [ ] Critical metric group failures must return an error unless diagnostic partial mode is explicitly configured.
- [ ] Partial reports must include `report_status = "partial"`, affected sections, skipped/failed/degraded section metadata, warnings, quality flags, lineage, and JSON-safe values.
- [ ] Report generation must define section criticality as required, optional, diagnostic-only, disabled, skipped, failed, or degraded.
- [ ] Required-section failure must return an error unless diagnostic partial mode is explicitly enabled.
- [ ] Optional-section failure must produce skipped or failed section metadata without fabricating the missing section.
- [ ] Partial reports must be marked non-promotable and must not be consumed as final approval evidence.
- [ ] Report metadata must preserve `request_id`, optional `workflow_id`, run IDs, strategy identifiers, strategy version, schema version, analytics engine version, annualization settings, optional-section status, source context, and creation time.
- [ ] Hashing rules must exclude non-deterministic fields such as generation timestamps unless explicitly documented.
- [ ] Hashes must be computed from canonical JSON serialization with deterministic key ordering, documented numeric normalization, and documented exclusion rules for non-deterministic fields.
- [ ] Analytics must propagate upstream data-quality and bias evidence into report warnings and quality flags.
- [ ] Dashboard payload builders must consume validated `AnalyticsReport` sections and must not recompute core metrics.
- [ ] `format_summary_as_rows` shall format raw summary data into report/display rows.
- [ ] `build_backtest_report` shall build a structured backtest analytics report payload.
- [ ] `print_statistical_validation_report` shall package a comprehensive statistical validation report.
- [ ] Report generation must be idempotent for the same input, configuration, and analytics engine version.
- [ ] Reports must include reproducibility metadata, input hashes, configuration hashes, report hashes, and lineage.
- [ ] Annualized metrics must use explicit annualization settings stored in configuration and report metadata; the module must not silently guess annualization when frequency cannot be inferred safely.
- [ ] Cache hits, misses, evictions, and concurrent duplicate requests must not change metric values, warning order, report hashes, dashboard payloads, or quality-flag outcomes.
- [ ] Sequential and parallel execution over the same report inputs must not change metric values, warning order, report hashes, dashboard payloads, or quality-flag outcomes.
- [ ] Warning and quality-flag ordering must be deterministic where output hashes, dashboard payloads, report comparison, or tests depend on order.
- [ ] Architectural Mandate: canonical monetary sums, cost aggregation, and base-currency aggregation must use `Decimal` normalization for hashing and report contracts.
- [ ] Report metadata must identify the monetary precision mode used, such as `decimal` or `float64_with_tolerance`.
- [ ] The module must define concrete runtime limits for bootstrap, permutation, Monte Carlo, distribution fitting, dashboard downsampling, and report generation before production handoff.
- [ ] `build_analytics_report` latency, statistical-validation runtime, throughput, memory, and payload-size targets must be measurable before Builder handoff.
- [ ] Documentation must include report section criticality and partial-report behavior.
- [ ] Documentation must include schema compatibility policy for accepted, deprecated, legacy-adapted, and unsupported report/result versions.
- [ ] Documentation must include partial-report examples showing skipped, failed, and degraded section metadata.
- [ ] `TradingResult`, `AnalyticsReport`, `PortfolioAnalyticsReport`, dashboard payloads, warning objects, quality flags, and error envelopes have versioned schemas.
- [ ] Report section criticality and partial-report non-promotable behavior are approved.
- [ ] Requirement-to-test traceability matrix maps every official tool, report contract, adapter mapping, warning/quality flag, and failure envelope to tests.
- [ ] Usage examples cover success, validation failure, partial report, dashboard truncation, and request-ID traceability.
- [ ] No file-specific non-functional requirements defined.
- [ ] Final analytics responses must not contain `NaN`, `inf`, `-inf`, invalid JSON values, pandas objects, NumPy objects, raw dataframes, raw series, or other unserializable values.

#### `app/services/analytics/dashboard.py`

Functions/classes:

- `build_overview_payload`

Requirements:

- [ ] Dashboard payloads must include chart/table data, finite numeric values, ISO-8601 timestamps, units, warnings, and metadata sufficient for UI/API consumers.
- [ ] If a required source section is missing, failed, skipped, or degraded, the dashboard payload must include section-status metadata and warnings rather than recomputing or fabricating chart/table values.
- [ ] Dashboard/UI consumers must not need to recalculate core metrics.
- [ ] Dashboard payload support must be classified by chart/table type as required, optional, or future before Builder implementation.
- [ ] Truncated payload metadata must include whether truncation occurred, original point count, returned point count, truncation method or algorithm, and truncation reason.
- [ ] `build_overview_payload` shall build the API/dashboard analytics overview payload.
- [ ] Result payloads must be JSON-safe or convertible to JSON-safe structures for API and dashboard consumers.
- [ ] Dashboard payloads must obey configured size limits and deterministic truncation policies when limits are defined.
- [ ] The module must define concrete maximum response payload size and deterministic truncation behavior for dashboard and API payloads before production handoff.
- [ ] Documentation must include required, optional, and future dashboard payload classes.
- [ ] Documentation must include dashboard truncation examples showing truncation metadata.
- [ ] Concrete input-size, runtime, memory, response-size, dashboard truncation, statistical iteration, and performance targets are approved with a hardware/profile context.
- [ ] No file-specific non-functional requirements defined.
- [ ] No file-specific testing requirements defined.


### Hardening Amendments

#### Canonical analytics inputs

Requirements:

- [ ] Adopt Phase 1.5 contracts for TradeResult, ExecutionReport, Fill, PortfolioSnapshot, BacktestResult, RiskDecision, and AuditEvent analytics inputs.
- [ ] Define analytics adapters that consume simulation journals and live trade journals through the same canonical event/result model.
- [ ] Prohibit Analytics from reading raw broker SDK payloads, UI DTOs, or conversation memory as primary metric sources.
- [ ] Define metric provenance using run ID, strategy ID, dataset hash, cost model, fill model, risk policy version, and journal reference.
- [ ] Ensure Analytics can run before UI/API exists and can be consumed by UI/API later without changing metric definitions.

### Unit Tests Required

```text

tests/unit/app/services/analytics/

```

Test coverage:

- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text

tests/usage/app/services/06_analytics.py

```

Usage examples must show:

- `example_01_trade_and_equity_metrics`: Demonstrate trade summaries, equity curves, returns, and canonical metric definitions.
- `example_02_drawdown_and_risk_metrics`: Demonstrate drawdown series, max drawdown, recovery, risk ratios, and undefined-result behavior.
- `example_03_distribution_and_benchmark_metrics`: Demonstrate distribution stats, benchmark comparisons, and missing benchmark handling.
- `example_04_efficiency_metrics`: Demonstrate capital efficiency, return per MAE/MFE, exposure efficiency, and warning metadata.
- `example_05_scorecard_evaluation`: Demonstrate scorecard rules, warning flags, metric catalog validation, and failed/skipped sections.
- `example_06_report_generation`: Demonstrate report payload generation, markdown/json serialization, provenance, and reproducibility hashes.
- `example_07_dashboard_payloads`: Demonstrate dashboard-ready payloads, chart/table data, and schema-versioned outputs.
- `example_08_read_only_boundaries`: Demonstrate analytics read-only behavior and lack of trading/risk approval authority.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 460 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text

feat(analytics-service): implement portfolio analytics scorecard and dashboard



- Build trade statistics, equity curve analysis, and drawdown metrics

- Compute key risk ratios: Sharpe, Sortino, Calmar, and Profit Factor

- Create performance scorecard, return distribution analysis, and efficiency scores

- Expose read-only analytics service methods and official report generation tools

```

- [ ] Analytics output must not include secrets, credentials, broker tokens, authorization headers, or private raw provider payloads.
- [ ] Analytics outputs used by UI/API must remain backward-compatible or be versioned when payload structure changes.
