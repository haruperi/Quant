# 06_analytics.md - Requirements

## 1. Purpose

The Analytics module provides read-only measurement and reporting tools for trading research, backtests, simulations, paper results, and historical/live result analysis. It converts trade records, equity curves, return streams, benchmark series, and report payloads into standardized analytics envelopes that can be consumed by API routes, dashboards, research workflows, optimization, simulation, and strategy-quality review.

The module exists to answer observable performance questions such as profitability, win/loss behavior, drawdown depth and duration, return distribution, benchmark-relative performance, risk exposure, statistical robustness, cost drag, efficiency, and strategy quality. It does not approve strategies, place trades, mutate live state, claim live-readiness, or emit a final promotable/live-ready verdict in any output. Analytics evidence is non-binding; agentic workflows must not auto-approve, auto-promote, auto-allocate, or auto-execute strategies from Analytics output without a separate governance/human approval loop.

The module should produce canonical, versioned analytics evidence such as `AnalyticsReport`, `PortfolioAnalyticsReport`, and dashboard payloads from normalized trading results. It is an evidence layer for Simulation, Optimization, Risk review, Portfolio review, Dashboard/UI, Agentic workflows, and Governance/Audit, not a governance or execution authority.

### 1.1 Assumptions and resolved decisions


### 1.2 Open Questions



## 2. Ownership

### 2.1 Owns

### 2.2 Does Not Own

## 3. Global API Contracts and Configuration

### 3.1 Public Capabilities Summary

### 3.3 Configuration Defaults

## 4. Module Architecture

### 4.1 Target Folder Structure

```text
app/
    __init__.py
    services/
        services/
                analytics/
                    __init__.py
                    adapters.py
                    trade.py
                    equity.py
                    drawdown.py
                    risk.py
                    ratios.py
                    distributions.py
                    benchmark.py
                    efficiency.py
                    scorecard.py
                    report.py
                    dashboard.py
tests/
    unit/
        app/
            services/
                services/
                        analytics/
                            test_metrics.py
                            test_report.py
                            test_scorecard.py
    usage/
        app/
            services/
                services/
                        analytics/
                            test_analytics_usage.py```

### 4.2 Class Diagrams

```mermaid
classDiagram
    class TradingResultAdapter {
        +to_canonical(source_payload) TradingResult
    }
    class MetricKernel {
        <<interface>>
        +calculate(series) float
    }
    class AnalyticsReportBuilder {
        +build_report(trading_result) AnalyticsReport
    }
    class StrategyQualityScorecard {
        +evaluate(report) ScorecardResult
    }
    AnalyticsReportBuilder --> TradingResultAdapter : uses
    AnalyticsReportBuilder --> MetricKernel : runs
    StrategyQualityScorecard --> AnalyticsReportBuilder : consumes
```

## 5. General / Cross-Cutting Non-Functional Requirements

- [x] Analytics behavior must be deterministic for the same inputs except where Monte Carlo, bootstrap, or permutation features intentionally use randomness; those features should support explicit seeds.
- [x] Analytics functions must be read-only and side-effect free at the domain level.
- [x] The module must degrade safely when optional acceleration libraries are unavailable.
- [x] Calculations over large datasets must use vectorized operations where feasible and must degrade to bounded chunked processing with warnings when vectorization or memory limits are exceeded.
- [x] Analytics output must not include secrets, credentials, broker tokens, authorization headers, or private raw provider payloads.
- [x] Public registry changes must remain auditable through tests and catalog updates.
- [x] Analytics outputs used by UI/API must remain backward-compatible or be versioned when payload structure changes.
- [x] Importing the analytics registry should not perform live broker calls, network calls, database mutations, or trading side effects.
- [x] Final analytics responses must not contain `NaN`, `inf`, `-inf`, invalid JSON values, pandas objects, NumPy objects, raw dataframes, raw series, or other unserializable values.
- [x] Official tools must be stateless, retry-safe, and safe for parallel optimization or portfolio workflows.
- [x] Metric kernels must not depend on mutable global calculation state.
- [x] Shared caches, if implemented, must be concurrency-safe or read-through and keyed by input hash, configuration hash, and analytics engine version.
- [x] Local/read-through caches, if implemented, must define TTL, maximum size, eviction behavior, invalidation keys, lock timeout, stale-read behavior, and single-flight or equivalent thundering-herd prevention before Builder handoff.
- [x] Distributed caching, distributed invalidation services, message queues, and async background workers must not be implemented inside Analytics.
- [x] Long-series cumulative operations must use numerically stable methods where feasible and must document any approximation or chunking behavior.
- [x] Duplicate timestamps must be rejected or resolved deterministically according to configuration and recorded in diagnostics.
- [x] Portfolio aggregation must fail closed when required base-currency conversion is unavailable.
- [x] Redaction rules must apply to sensitive keys and sensitive-looking values in inputs, warnings, errors, logs, metadata, and diagnostic details.

### 5.1 Other Global and Cross-Cutting Requirements

- [x] The analytics registry must expose only intentional public analytics tools and must not hide colliding function names; duplicate concepts must use module-qualified aliases where needed.
- [x] Every official exported analytics tool must be callable, documented, and accept a `request_id` parameter for traceability.
- [x] Official analytics tools must validate `request_id`; missing, empty, malformed, or unsafe request IDs must return a structured validation error envelope.
- [x] Official analytics tools must return the standard tool envelope on success and on controlled validation failure.
- [x] Invalid or missing required inputs must fail with a structured error envelope, not an uncaught exception. Custom analytics exceptions and error codes must inherit and reuse exceptions from `app.utils.errors` to prevent duplicate declaration.
- [x] Date/time analytics must parse supplied open/close timestamps, support both datetime-like and numeric timestamp inputs where implemented, and return JSON-safe values for durations and timestamps.
- [x] Statistical validation tools must expose deterministic options such as seeds, bootstrap/permutation counts, block sizes, confidence levels, alpha levels, and sample-size thresholds where supported.
- [x] The module must separate calculated facts from warnings, caveats, decisions, and recommended actions.
- [x] Official agent/API-facing analytics tools must be high-level, documented, typed, schema-compliant, traceable, and listed in the Official Analytics Tool Catalog.
- [x] Each official public capability must be labeled as stable, approved experimental, deprecated, or internal-support-only.
- [x] Each official public capability must document whether it is safe for agent/API use.
- [x] Every official analytics tool must have a documented input schema and output schema, including required fields, optional fields, default values, accepted aliases, units, validation errors, warning codes, and JSON-safe serialization behavior.
- [x] Low-level metric helpers such as individual average, skewness, kurtosis, tail-ratio, tracking-error, ulcer-index, omega-ratio, payoff-ratio, and date helper functions must remain internal/support-only unless explicitly promoted by the Official Analytics Tool Catalog.
- [x] Low-level metric kernels must not be exposed as official agent/API tools unless explicitly approved in the Official Analytics Tool Catalog.
- [x] The analytics registry must distinguish official tools, internal metric kernels, compatibility aliases, and deprecated exports.
- [x] Agentic workflows must import analytics capabilities from `app.services.analytics` rather than deep module files.
- [x] Official analytics tools must log call start, validation failure, successful completion, controlled warning, and execution failure without logging secrets or full raw private payloads.
- [x] Warnings and quality flags must include code, severity, affected section, source context, and enough bounded detail for downstream review.
- [x] Warning severity must support at least informational, warning, major, critical, and blocker-level meanings.
- [x] Quality flags must separate raw metrics, normalized score inputs, penalty flags, hard blockers, recommendation evidence, and final governance decisions.
- [x] Strategy-quality and prop-firm outputs must be labeled as non-binding analytics evidence or decision context only.
- [x] Warning and quality-flag catalogs must define code, severity, affected section, source-backed status, whether the flag blocks promotion, bounded detail rules, and linked test fixtures.
- [x] Live-vs-backtest and paper-vs-backtest degradation comparisons must validate strategy ID, strategy version, symbols, timeframe or return frequency, evaluation window, account base currency, and comparable cost/slippage model metadata before pairing.
- [x] Strategy-version mismatch must be handled explicitly during degradation pairing and must not be hidden inside aggregate scores.
- [x] Low-sample explainability drivers must not appear in ranked driver lists.
- [x] Explainability outputs must distinguish explained PnL, unexplained PnL, explained variance percentage, sample count, and driver stability when those inputs are supplied.
- [x] `common_avg_loss` shall expose the common-module average-loss function without colliding with metrics exports.
- [x] `common_get_r_multiples` shall expose the common-module R-multiple function without colliding with metrics exports.
- [x] `max_gross_size_held` shall calculate the maximum absolute total size held across positions.
- [x] `time_in_market_duration` shall calculate total duration where at least one position was open.
- [x] `percent_time_in_market` shall calculate percent of the trading period spent in the market.
- [x] `metrics_get_r_multiples` shall expose metrics-module R-multiple behavior without colliding with common exports.
- [x] `win_rate_fraction` shall calculate win rate on a 0-to-1 scale.
- [x] `avg_win_loss` shall calculate mean winning and losing outcomes.
- [x] `consecutive_wins_losses` shall calculate maximum consecutive wins and losses from numeric outcomes.
- [x] `median_mae_mfe` shall calculate median MAE and MFE values.
- [x] `get_mae_mfe_r` shall calculate MAE and MFE normalized to R-space.
- [x] `t_statistic` shall calculate the t-statistic for mean outcome.
- [x] `open_position_pnl` shall calculate total unrealized PnL from open positions.
- [x] `slippage_paid` shall calculate total absolute slippage costs paid.
- [x] `commission_paid` shall calculate total absolute commission costs paid.
- [x] `swap_paid` shall calculate total absolute swap costs paid.
- [x] `metrics_avg_loss` shall expose metrics-module average-loss behavior without colliding with common exports.
- [x] `expectancy_r` shall calculate R-expectancy.
- [x] `max_size_held` shall calculate maximum total contracts held.
- [x] `max_net_size_held` shall calculate maximum net directional size held.
- [x] `max_long_size_held` shall calculate maximum total long contracts held.
- [x] `max_short_size_held` shall calculate maximum total short contracts held.
- [x] `avg_r_multiple` shall calculate average R-multiple.
- [x] `median_r_multiple` shall calculate median R-multiple.
- [x] `metrics_r_multiple_distribution` shall calculate R-multiple distribution statistics.
- [x] `r_expectancy` shall calculate R-space expectancy.
- [x] `max_r_multiple` shall calculate maximum R-multiple.
- [x] `min_r_multiple` shall calculate minimum R-multiple.
- [x] `median_mae_r` shall calculate median MAE in R-multiple terms.
- [x] `median_mfe_r` shall calculate median MFE in R-multiple terms.
- [x] `avg_consecutive_wins` shall calculate average length of winning streaks.
- [x] `avg_consecutive_losses` shall calculate average length of losing streaks.
- [x] `win_loss_streaks` shall return winning and losing streak sequences.
- [x] `sqn` shall calculate system quality number.
- [x] `kelly_criterion` shall calculate Kelly criterion percentage from R-multiples or returns.
- [x] `r_signal_to_noise` shall calculate mean R relative to R volatility.
- [x] `rolling_expectancy_stability` shall calculate expectancy stability over a rolling window.
- [x] `win_after_win_probability` shall calculate probability that a win follows a win.
- [x] `runs_test_zscore` shall calculate Wald-Wolfowitz runs-test z-score.
- [x] `trading_period_duration` shall calculate total duration of the trading period.
- [x] `get_analytics_overview` shall calculate comprehensive analytics across all, long, and short subsets.
- [x] `calculate_spread_cost_impact` shall calculate spread cost drag.
- [x] `calculate_slippage_impact` shall calculate slippage cost drag.
- [x] `calculate_commission_impact` shall calculate commission cost drag.
- [x] `cagr` shall calculate compound annual growth rate.
- [x] `compound_monthly_growth_rate` shall calculate compound monthly growth rate.
- [x] `avg_monthly_return` shall calculate arithmetic average monthly return.
- [x] `monthly_return_stddev` shall calculate monthly return volatility.
- [x] `annualized_return` shall calculate geometric annualized return.
- [x] `geometric_mean_return` shall calculate geometric mean return.
- [x] `best_return` shall calculate best single-period return.
- [x] `worst_return` shall calculate worst single-period return.
- [x] `buy_and_hold_return` shall calculate total buy-and-hold return from price data.
- [x] `buy_and_hold_cagr` shall calculate buy-and-hold CAGR from price data.
- [x] `return_volatility` shall calculate return standard deviation.
- [x] `downside_return_volatility` shall calculate volatility of returns below target.
- [x] `return_skewness` shall calculate return-distribution skewness.
- [x] `return_kurtosis` shall calculate return-distribution excess kurtosis.
- [x] `adjusted_gross_profit` shall calculate adjusted gross profit.
- [x] `adjusted_gross_loss` shall calculate adjusted gross loss.
- [x] `adjusted_net_profit` shall calculate adjusted net profit.
- [x] `select_net_profit` shall calculate net profit after outlier selection.
- [x] `select_gross_profit` shall calculate gross profit after outlier selection.
- [x] `select_gross_loss` shall calculate gross loss after outlier selection.
- [x] `return_on_account` shall calculate return on required account size.
- [x] `max_runup` shall calculate maximum gain from valley to peak.
- [x] `max_runup_date` shall identify the timestamp of maximum runup peak.
- [x] `calculate_period_analysis` shall calculate performance by timestamp bucket.
- [x] `calculate_long_short_split` shall calculate long-versus-short profit split.
- [x] `calculate_session_performance` shall calculate session performance from timestamped records.
- [x] `whites_reality_check` shall assess data-snooping bias with White's Reality Check.
- [x] `permutation_test` shall run significance testing through random reshuffling or sign-flipping.
- [x] `bootstrap_confidence_intervals` shall estimate metric uncertainty with non-parametric bootstrap.
- [x] `deflated_sharpe_ratio` shall adjust Sharpe ratio diagnostics for multiple testing and non-normality.
- [x] `probability_of_backtest_overfitting` shall estimate probability of backtest overfitting.
- [x] `walk_forward_degradation_score` shall measure performance decay from in-sample to out-of-sample scores.
- [x] `bootstrap_probability_above_threshold` shall estimate probability that a bootstrapped metric exceeds a threshold.
- [x] `bonferroni_correction` shall apply Bonferroni correction for multiple hypothesis testing.
- [x] `benjamini_hochberg_correction` shall apply Benjamini-Hochberg false-discovery-rate control.
- [x] `sample_size_warning` shall assess metric reliability based on sample size.
- [x] `stability_score` shall calculate performance consistency across walk-forward windows.
- [x] `whites_reality_check_backtests` shall run White's Reality Check against backtest result objects.
- [x] `permutation_test_backtest` shall run permutation testing against a backtest result object.
- [x] `bootstrap_confidence_intervals_backtest` shall estimate bootstrap confidence intervals from a backtest result object.
- Tests proving Analytics validates and summarizes supplied execution evidence but does not generate, certify, repair, or enforce execution evidence.
- Placeholder stress tests must exercise owner-approved maximum input sizes once those limits exist and must fail safely on memory explosion, timeout, oversized response, or deterministic truncation failure.
- [x] Documentation must include the Official Analytics Tool Catalog.
- [x] Documentation must include the warning-code and quality-flag catalog.
- [x] Documentation must include adapter field-mapping tables for every supported upstream result type.
- [x] Documentation must include success examples for each approved official high-level tool.
- [x] Documentation must include validation-failure examples showing the standard error envelope.
- [x] Low-level metric examples must be labeled as internal/developer examples when they are not official agent/API tools.
- ADR Required: `ADR-ANALYTICS-PUBLIC-SURFACE` must classify existing `app.services.analytics` metric functions as official high-level tools, internal kernels, compatibility exports, deprecated exports, or reference-only historical names before Builder handoff.
- Metric kernels must not be treated as agent/API-facing just because they exist in the repository or appear in historical examples.
- Upstream result schemas from Simulation, Backtesting, Paper, Live, Optimization, Trading receipts, and Portfolio must be versioned and mapped through a schema compatibility matrix.
- Adapter logic from approved upstream result schemas into canonical `TradingResult` is Analytics responsibility; breaking upstream schema changes must be recorded through the compatibility matrix before Analytics can safely consume them.
- ADR Required: `ADR-ANALYTICS-PUBLIC-SURFACE` must resolve export classification by recording which current exports are official high-level tools, internal kernels, compatibility aliases, deprecated exports, or reference-only historical names.
- ADR Required: `ADR-ANALYTICS-FX` must approve authoritative FX conversion source, stale-rate age limits, currency override workflow, and blocker behavior for missing multi-currency conversion.
- ADR Required: `ADR-ANALYTICS-WARNINGS` must approve the warning-code and quality-flag catalog, including severity meanings, promotion-blocking behavior, source-backed status, bounded detail limits, and linked test fixtures.
- The current implementation exposes a large analytics registry; future work should keep catalog generation and registry tests synchronized whenever public tools change.
- Some analytics tools provide broad wrappers around pandas/NumPy objects; API-facing calls must not be treated as production-ready until stricter input schemas are approved in the Official Analytics Tool Catalog.
- Analytics should carry explicit environment/source labels for simulated, paper, live, and historical data so mixed-environment results cannot be misread.
- Statistical and Monte Carlo helpers must document runtime limits, default seeds, and reproducibility expectations before production handoff.
- Strategy-quality score thresholds are implementation-derived observations and should not be treated as approved production promotion rules until owner/governance approval records them.

## 6. Detailed Requirements by File

### File: app/__init__.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/__init__.py`.

#### Functional Requirements
- [x] Undefined or unsupported metric values must be represented as omitted fields or `None` according to the output schema plus structured warnings or skipped-section metadata; they must not be serialized as `NaN`, infinity, fabricated zero, or display-only caps.
- [x] R-multiple fallback proxies must be listed in the Metric Definition Catalog before use; fallback-derived R-multiple values must include warning metadata and mark the affected metric confidence as degraded.
- [x] Every official metric must define formula, units, required inputs, optional inputs, accepted aliases, return scale, annualization basis, sample/population convention, minimum sample size, undefined-result behavior, and golden-fixture expectations.
- [x] `total_return` shall calculate total return as a percentage of initial capital.
- [x] `return_on_initial_capital` shall calculate net profit as a percentage of initial capital.
- [x] Numeric outputs must avoid misleading precision and must handle empty, missing, non-finite, zero-denominator, and insufficient-sample scenarios consistently.
- [x] Documentation must include the Metric Definition Catalog.
- ADR Required: `ADR-ANALYTICS-METRIC-CATALOG` must approve the Metric Definition Catalog for all official metrics, including formulas, units, annualization basis, return scale, sample/population convention, minimum sample size, undefined-result behavior, `breakeven_epsilon`, non-finite handling, and golden-fixture expectations.
- [x] Official Analytics Tool Catalog is approved and maps every official tool to schemas, errors, metadata, side effects, stability, and tests.
- [x] Metric Definition Catalog is approved and no official schema references uncataloged metrics.
- [x] Public/internal export classification is approved, including compatibility aliases and deprecated exports.
- [x] Analytics-owned private canonical metric-kernel model is documented and enforced through public/internal export classification tests.
- [x] Schema compatibility matrix defines accepted, deprecated, legacy-adapted, rejected, and unsupported future versions.
- [x] Decimal monetary precision mandate and deterministic derived-ratio tolerance policy are documented in schemas, metadata, and tests.

#### Non-Functional & Security Requirements
- [x] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [x] No file-specific testing requirements defined.

### File: app/services/analytics/__init__.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/analytics/__init__.py`.

#### Functional Requirements
- [x] No file-specific functional requirements defined. Foundation properties apply.

#### Non-Functional & Security Requirements
- [x] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [x] No file-specific testing requirements defined.

### File: app/services/analytics/adapters.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/analytics/adapters.py`.

#### Functional Requirements
- Deterministic analytics adapters that convert `BacktestResult`, `PaperTradingResult`, `LiveTradingResult`, portfolio results, and other normalized caller outputs into a canonical `TradingResult` view without silent field loss; adapters must fail closed with structured errors when required fields, schema versions, or compatibility mappings are missing or incompatible.
- [x] Backtest, paper, live, portfolio, and normalized trading results must either inherit from a canonical `TradingResult` contract or be converted into it through deterministic adapters.
- [x] Deterministic adapters must preserve schema version, result ID, phase/environment, timestamps, account base currency, strategy identifiers, symbols, timeframe, trades, equity curve, optional balance curve, benchmark data, upstream quality metadata, and source metadata without silent field loss.
- [x] Deterministic adapters must define source-to-canonical field mappings, required fields, optional fields, defaulting behavior, unsupported-field behavior, lossless metadata preservation rules, and warning/error behavior for missing or incompatible fields.

#### Non-Functional & Security Requirements
- [x] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [x] No file-specific testing requirements defined.

### File: app/services/analytics/__init__.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/analytics/__init__.py`.

#### Functional Requirements
- [x] No file-specific functional requirements defined. Foundation properties apply.

#### Non-Functional & Security Requirements
- [x] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [x] No file-specific testing requirements defined.

### File: app/services/analytics/trade.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/analytics/trade.py`.

#### Functional Requirements
- [x] Official analytics tools must not write files, modify databases, place trades, or require network access.
- [x] Analytics input conversion must support common developer inputs such as pandas dataframes, pandas series, lists of trade records, and lists of numeric values where the public capability expects them.
- [x] Trade-oriented tools must use closed-trade semantics when a metric is defined over realized results.
- [x] Closed-trade filtering must exclude records explicitly marked as still open or end-of-data placeholders and must ignore records without close timestamps when close timestamps are required.
- [x] Trade classification must distinguish wins, losses, and breakevens using a configured `breakeven_epsilon` from the Metric Definition Catalog or numeric policy ADR so near-zero PnL does not become a false win or loss.
- [x] Exposure and time-in-market analytics must merge overlapping trade intervals so simultaneous positions are measured as market presence once for duration metrics.
- [x] Long/short split analytics must classify direction using the supplied trade direction/type fields and must not infer trade direction from PnL.
- [x] Cost-impact analytics must quantify spread, slippage, and commission drag from supplied cost and gross-profit inputs without mutating the source trades.
- [x] Aggregated analytics must preserve source context enough for downstream consumers to know whether inputs came from all trades, long trades, short trades, benchmark comparisons, cost analysis, or statistical validation.
- [x] `AnalyticsReport` output must include summary, trade metrics, equity metrics, return metrics, drawdown metrics, risk metrics, ratio metrics, distribution metrics, benchmark metrics, efficiency metrics, statistical validation, cost breakdown, warnings, quality flags, dashboard payloads, lineage, and metadata when those sections are applicable.
- [x] Report hashes must include deterministic input hash, config hash, report hash, trade ledger hash, equity curve hash, and optional benchmark hash where the source material exists.
- [x] ADR Required: `ADR-ANALYTICS-PUBLIC-SURFACE` must approve the initial official high-level tool surface before Builder implementation; candidate tools include `build_analytics_report`, `build_portfolio_analytics_report`, `evaluate_strategy_quality`, `compare_analytics_reports`, `calculate_trade_metrics`, `calculate_equity_metrics`, `calculate_drawdown_metrics`, `calculate_risk_metrics`, `calculate_benchmark_metrics`, `calculate_statistical_validation`, and `calculate_prop_firm_compliance`.
- [x] Candidate dashboard payloads include summary cards, equity curve chart, drawdown curve chart, monthly returns heatmap, rolling ratio charts, rolling drawdown chart, trade distribution chart, cost breakdown chart, symbol contribution chart, warning table, and quality flag table when source sections exist.
- [x] `get_closed_trades` shall filter trade records to realized closed trades.
- [x] `classify_trades` shall classify trades into wins, losses, and breakevens using a consistent threshold.
- [x] `avg_loss` shall calculate the mean loss of losing trades.
- [x] `get_r_multiples` shall calculate R-multiples for trades.
- [x] `trade_pnl_distribution` shall calculate a statistical summary of realized trade PnL.
- [x] `trade_level_drawdowns` shall calculate cumulative PnL drawdowns at trade close points.
- [x] `max_close_to_close_drawdown` shall calculate maximum trade-level peak-to-valley decline including excursion context where available.
- [x] `avg_trade_drawdown` shall calculate mean trade-level close-to-close drawdown depth.
- [x] `max_consecutive_drawdown_trades` shall calculate maximum number of consecutive trades inside a strategy drawdown.
- [x] `max_close_to_close_drawdown_date` shall identify the timestamp of deepest trade-level valley.
- [x] `avg_trade_notional_efficiency` shall provide the capital-efficiency metric under a clearer average-trade-notional name.
- [x] `avg_return_per_risk_unit` shall calculate average R-multiple per closed trade.
- [x] `return_per_trade_hour` shall calculate net profit per hour spent in active trades.
- [x] `return_per_market_hour` shall calculate net profit per hour where at least one trade was open.
- [x] `trades_per_day` shall calculate average number of closed trades per calendar day in the test period.
- [x] `profit_per_trade_per_day` shall calculate net profit normalized by both number of trades and calendar days.
- [x] `mfe_efficiency` shall calculate average percentage of MFE captured by winning trades.
- [x] `aggregate_mfe_capture_ratio` shall calculate aggregate MFE capture ratio for winning trades.
- [x] `mae_efficiency` shall calculate realized-loss-to-MAE efficiency for losing trades.
- [x] `aggregate_loss_containment_efficiency` shall calculate aggregate loss containment for losing trades.
- [x] `position_size_efficiency` shall calculate relationship between position size and normalized trade outcome.
- [x] `calculate_efficiency_metrics` shall calculate aggregate MAE/MFE efficiency context from trades.
- [x] `get_ordered_closed_trades` shall filter closed trades and sort them for sequence-dependent metrics.
- [x] `total_trades` shall count closed trades.
- [x] `winning_trades` shall count closed winning trades.
- [x] `losing_trades` shall count closed losing trades.
- [x] `breakeven_trades` shall count closed breakeven trades.
- [x] `long_trades` shall count closed long trades.
- [x] `short_trades` shall count closed short trades.
- [x] `count_open_trades` shall count currently open trades.
- [x] `win_rate` shall calculate percentage of winning trades.
- [x] `loss_rate` shall calculate percentage of losing trades.
- [x] `avg_win` shall calculate mean profit of winning trades.
- [x] `largest_win` shall calculate maximum single-trade profit.
- [x] `largest_loss` shall calculate maximum single-trade loss.
- [x] `median_win` shall calculate median PnL of winning trades.
- [x] `median_loss` shall calculate median PnL of losing trades.
- [x] `expectancy` shall calculate trade expectancy.
- [x] `max_consecutive_wins` shall calculate maximum consecutive winning trades.
- [x] `max_consecutive_losses` shall calculate maximum consecutive losing trades.
- [x] `avg_time_in_trade` shall calculate average trade duration.
- [x] `median_time_in_trade` shall calculate median trade duration.
- [x] `max_time_in_trade` shall calculate maximum trade duration.
- [x] `min_time_in_trade` shall calculate minimum trade duration.
- [x] `compute_r_trade_metrics` shall calculate trade metrics from R-multiple inputs.
- [x] `compute_trade_metrics` shall calculate trade metrics from numeric R values and optional MAE/MFE arrays.
- [x] `trade_efficiency` shall calculate realized outcome relative to maximum favorable excursion.
- [x] `trade_outcome_entropy` shall calculate Shannon entropy of trade outcomes.
- [x] `longest_flat_period_duration` shall calculate longest period without an active trade.
- [x] `calculate_trade_metrics` shall calculate aggregate core trade metrics from normalized trade records.
- [x] `calculate_analytics_for_subset` shall calculate all analytics categories for a supplied trade subset.
- [x] `return_over_drawdown` shall calculate total return relative to maximum trade drawdown.
- [x] `net_profit_as_percent_of_max_trade_drawdown` shall calculate net profit as a percentage of max trade drawdown.
- [x] `select_net_profit_as_percent_of_max_trade_drawdown` shall calculate selected net profit as a percentage of max trade drawdown.
- [x] `adjusted_net_profit_as_percent_of_max_trade_drawdown` shall calculate adjusted net profit as a percentage of max trade drawdown.
- [x] `net_profit` shall calculate total realized profit or loss from closed trades.
- [x] `gross_profit` shall sum winning closed-trade profit.
- [x] `gross_loss` shall sum losing closed-trade loss.
- [x] `balance_curve_from_closed_trades` shall generate a realized balance curve from closed trades.
- [x] `balance_curve` shall expose balance-curve behavior as an alias of closed-trade balance curve generation.
- [x] `equity_curve` shall expose equity-curve behavior for common orchestration using the closed-trade curve.
- [x] `max_loss_probability` shall calculate probability of a single trade loss exceeding a threshold.
- [x] `risk_of_ruin` shall estimate ruin probability through Monte Carlo simulation of trade outcomes.
- [x] `avg_trade_nominal_exposure` shall calculate average nominal exposure per trade.
- [x] `max_single_trade_margin_utilization` shall calculate maximum margin used by a single trade as a percentage of equity.
- [x] `avg_single_trade_margin_utilization` shall calculate average margin used per trade as a percentage of equity.
- [x] `risk_of_ruin_with_custom_horizon` shall estimate ruin probability over a fixed future trade horizon.
- [x] The module must define concrete maximum accepted input sizes for trades, equity points, benchmark points, portfolio components, dashboard payloads, and statistical observations before production handoff.
- ADR Required: `ADR-ANALYTICS-THRESHOLDS` must approve minimum thresholds for trade count, return observations, tail-risk observations, benchmark coverage, explainability samples, dashboard point counts, and promotion-blocking quality flags.

#### Non-Functional & Security Requirements
- [x] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [x] No file-specific testing requirements defined.

### File: app/services/analytics/equity.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/analytics/equity.py`.

#### Functional Requirements
- [x] Equity and return analytics must sort and normalize supplied series deterministically; optional `NaN`/`NaT` observations may be filtered only with recorded warning metadata, required `NaN`/`NaT` fields must fail validation unless the Metric Definition Catalog marks them skippable, and `Infinity`/`-Infinity` at official boundaries must return `VALIDATION_FAILED`.
- [x] Dashboard truncation/downsampling must be deterministic and must preserve first point, last point, local extrema where practical, drawdown troughs, equity highs, and timestamps associated with major, critical, or blocker warnings.
- [x] `benchmark_returns` shall generate a return series from benchmark equity or price values.
- [x] `relative_drawdown_series` shall generate relative underperformance between strategy and benchmark equity.
- [x] `drawdown_series` shall calculate drawdown values from an equity curve.
- [x] `drawdown_duration_series` shall calculate drawdown duration values from an equity curve.
- [x] `max_drawdown_duration_from_equity` shall calculate maximum drawdown duration from equity values.
- [x] `max_strategy_drawdown_date` shall identify the timestamp of deepest strategy equity valley.
- [x] `avg_underwater_drawdown_percent` shall calculate average drawdown depth while equity is below peak.
- [x] `calculate_drawdown_metrics` shall calculate aggregate drawdown metrics from an equity curve.
- [x] `compute_equity_metrics` shall calculate equity metrics from return inputs.
- [x] `total_return_usd` shall calculate total return in currency units from an equity curve.
- [x] `returns_series` shall calculate percentage returns between equity points.
- [x] `log_returns_series` shall calculate logarithmic returns between equity points.
- [x] `daily_returns` shall calculate daily percentage returns from an equity curve.
- [x] `weekly_returns` shall calculate weekly percentage returns from an equity curve.
- [x] `monthly_returns` shall calculate monthly percentage returns from an equity curve.
- [x] `annual_returns` shall calculate annual percentage returns from an equity curve.
- [x] `calculate_return_metrics` shall calculate aggregate cumulative and average returns from an equity curve.

#### Non-Functional & Security Requirements
- [x] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- Dashboard truncation that must preserve first/last points, important extrema, drawdown troughs, equity highs, and major warning timestamps.

### File: app/services/analytics/drawdown.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/analytics/drawdown.py`.

#### Functional Requirements
- [x] Strategy-quality evaluation must rely only on the supplied report payload and must surface warnings for weak profitability, high drawdown, overfitting risk, small sample size, or other observable quality concerns.
- [x] Optional sections such as TCA metrics, attribution, prop-firm compliance evidence, drawdown distribution, tail-risk metrics, dynamic correlation, walk-forward analytics, metric comparisons, live degradation, and explainability must be represented as calculated, skipped, or failed.
- [x] Formula definitions must be explicit for Sharpe, Sortino, Calmar, Jensen alpha, beta, tracking error, information ratio, VaR, CVaR, expected shortfall, SQN, Kelly, drawdown duration, CAGR, profit factor, expectancy, and R-multiple metrics before those metrics are locked as official contracts.
- [x] `max_relative_drawdown_percent` shall calculate maximum relative underperformance as a positive percentage.
- [x] `max_strategy_drawdown` shall calculate deepest peak-to-valley decline in currency units.
- [x] `max_strategy_drawdown_percent` shall calculate deepest percentage decline relative to running peak.
- [x] `max_drawdown` shall calculate maximum drawdown from returns.
- [x] `avg_drawdown` shall calculate average drawdown depth.
- [x] `drawdown_distribution` shall calculate detailed drawdown distribution statistics.
- [x] `max_drawdown_duration_from_returns` shall calculate maximum drawdown duration from return values.
- [x] `max_drawdown_duration` shall calculate maximum drawdown duration from the selected input type.
- [x] `avg_drawdown_duration` shall calculate average duration of drawdown episodes.
- [x] `time_to_recovery` shall calculate recovery periods for unique drawdowns.
- [x] `recovery_factor` shall calculate net profit relative to maximum drawdown.
- [x] `max_close_to_close_drawdown_percent` shall calculate close-to-close drawdown as a percentage.
- [x] `account_size_required` shall estimate capital required to withstand max close-to-close dips.
- [x] `avg_yearly_max_drawdown` shall average the maximum drawdown observed in each year.
- [x] `ulcer_index` shall calculate squared-drawdown-based ulcer index.
- [x] `pain_index` shall calculate mean absolute percentage drawdown.
- [x] `pain_ratio` shall calculate return relative to pain index.
- [x] `calmar_ratio` shall calculate annualized return relative to maximum drawdown.
- [x] `fouse_ratio` shall calculate Fouse drawdown-index-style ratio.
- [x] `sterling_ratio` shall calculate CAGR relative to adjusted average yearly maximum drawdown.
- [x] `rina_index` shall calculate select net profit relative to average drawdown and time in market.
- [x] `net_profit_as_percent_of_max_strategy_drawdown` shall calculate net profit as a percentage of max strategy drawdown.
- [x] `select_net_profit_as_percent_of_max_strategy_drawdown` shall calculate selected net profit as a percentage of max strategy drawdown.
- [x] `adjusted_net_profit_as_percent_of_max_strategy_drawdown` shall calculate adjusted net profit as a percentage of max strategy drawdown.
- [x] `return_on_max_strategy_drawdown` shall calculate total return relative to maximum strategy drawdown.
- [x] `return_on_max_close_to_close_drawdown` shall calculate net profit relative to maximum close-to-close drawdown.
- [x] `drawdown_probability` shall calculate probability of drawdown exceeding a threshold.

#### Non-Functional & Security Requirements
- [x] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [x] No file-specific testing requirements defined.

### File: app/services/analytics/risk.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/analytics/risk.py`.

#### Functional Requirements
- [x] Official analytics tools must be low-risk, read-only operations.
- [x] Metadata must include tool name, tool version, tool category, tool risk level, request ID, execution time, and side-effect flags.
- [x] R-multiple analytics must prefer explicit initial-risk fields when available and fall back only to documented analytics proxies when risk fields are absent.
- [x] Official analytics tool responses must include metadata, side-effect flags, risk flags, execution timing, and structured errors.
- [x] Metric definitions must document default configuration sources for annualization, risk-free rate, breakeven tolerance, minimum sample size, bootstrap count limits, dashboard limits, FX stale-rate limits, and confidence/alpha levels when those defaults are approved.
- [x] Strategy-quality scorecards must not make final live approval, promotion, prop-firm enforcement, or risk-governor decisions.
- [x] Strategy-quality outputs must not claim final approval, promotion, live-readiness, prop-firm compliance enforcement, risk-limit approval, or portfolio allocation authority.
- [x] `risk_adjusted_efficiency` shall calculate return relative to total defined initial risk.
- [x] `profit_per_pip_risk` shall calculate reward-to-risk based on profit pips relative to MAE pips.
- [x] `upside_potential_ratio` shall calculate upside potential relative to downside risk.
- [x] `volatility` shall calculate return standard deviation as a positive percentage.
- [x] `annualized_volatility` shall calculate annualized volatility as a positive percentage.
- [x] `downside_volatility` shall calculate downside deviation as a positive percentage.
- [x] `value_at_risk` shall calculate value-at-risk as a positive percentage.
- [x] `conditional_var` shall calculate conditional value-at-risk as a positive percentage.
- [x] `expected_shortfall` shall calculate expected shortfall.
- [x] `max_nominal_exposure_simple` shall calculate maximum nominal exposure held at one time.
- [x] `max_gross_exposure` shall calculate maximum gross nominal exposure.
- [x] `exposure_time_ratio` shall calculate percentage of total period spent in market.
- [x] `time_weighted_avg_exposure` shall calculate time-weighted average notional exposure.
- [x] `portfolio_margin_utilization_curve` shall generate portfolio margin-utilization curve over time.
- [x] `compounding_risk_of_ruin` shall estimate ruin probability with dynamic compounding risk.
- [x] `historical_var_by_symbol` shall calculate historical value-at-risk by symbol.
- [x] `portfolio_var_from_covariance` shall calculate portfolio value-at-risk from covariance and weights.
- [x] `calculate_risk_metrics` shall calculate aggregate risk metrics such as VaR, CVaR, and volatility.
- [x] Tool metadata must consistently identify the category as `analytics` and risk level as `low`.
- [x] Analytics input and output contracts must remain aligned with Simulation, Optimization, Risk, Portfolio, Trading receipt, and UI/API contracts.
- ADR Required: `ADR-ANALYTICS-PUBLIC-SURFACE` must approve the Official Analytics Tool Catalog, including official names, callable paths, public/internal status, stability, input schemas, output schemas, warning schemas, deterministic errors, side-effect flags, risk levels, and agent/API exposure.
- ADR Required: `ADR-ANALYTICS-SCHEMA-COMPATIBILITY` must approve accepted, deprecated, legacy-adapted, and unsupported analytics/report schema versions for Risk Governor, Portfolio Manager, UI/API, Strategy Reviewer, Simulation, Optimization, and Trading receipts.
- The module should continue to avoid live side effects and should remain downstream of Simulation, Trading receipts, Data, and Risk rather than owning those workflows.

#### Non-Functional & Security Requirements
- [x] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [x] No file-specific testing requirements defined.

### File: app/services/analytics/ratios.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/analytics/ratios.py`.

#### Functional Requirements
- [x] `benchmark_information_ratio` shall expose benchmark information ratio without colliding with the ratios module export.
- [x] `up_down_capture` shall calculate up-capture and down-capture ratios.
- [x] `metrics_win_rate_fraction` shall expose metrics-module win-rate fraction behavior without colliding with ratios exports.
- [x] `metrics_expectancy` shall expose metrics-module expectancy behavior without colliding with ratios exports.
- [x] `metrics_expectancy_r` shall expose metrics-module R-expectancy behavior without colliding with ratios exports.
- [x] `ratios_win_rate_fraction` shall expose ratios-module win-rate fraction behavior without colliding with metrics exports.
- [x] `sharpe_ratio` shall calculate excess return per unit of volatility.
- [x] `annualized_sharpe_ratio` shall calculate annualized Sharpe ratio from monthly inputs.
- [x] `sortino_ratio` shall calculate excess return per unit of downside volatility.
- [x] `ratios_information_ratio` shall expose ratios-module information ratio without colliding with benchmark exports.
- [x] `omega_ratio` shall calculate probability-weighted gains relative to losses.
- [x] `gain_to_pain_ratio` shall calculate gains relative to absolute negative returns.
- [x] `kappa_ratio` shall calculate generalized Sortino-style Kappa ratio.
- [x] `profit_factor` shall calculate gross profit relative to gross loss.
- [x] `payoff_ratio` shall calculate average win relative to average loss.
- [x] `edge_ratio` shall calculate payoff edge adjusted by win rate.
- [x] `profit_to_mae_ratio` shall calculate profit capture relative to adverse excursion.
- [x] `mfe_to_mae_ratio` shall calculate favorable excursion relative to adverse excursion.
- [x] `expectancy_over_std` shall calculate expectancy stability relative to standard deviation.
- [x] `net_profit_as_percent_of_largest_loss` shall calculate net profit as a percentage of largest loss.
- [x] `select_net_profit_as_percent_of_largest_loss` shall calculate selected net profit as a percentage of largest loss.
- [x] `adjusted_net_profit_as_percent_of_largest_loss` shall calculate adjusted net profit as a percentage of largest loss.
- [x] `adjusted_profit_factor` shall calculate adjusted gross profit relative to adjusted gross loss.
- [x] `select_profit_factor` shall calculate selected gross profit relative to selected gross loss.
- [x] `ratios_expectancy` shall expose ratios-module expectancy behavior without colliding with metrics exports.
- [x] `ratios_expectancy_r` shall expose ratios-module R-expectancy behavior without colliding with metrics exports.
- [x] `calculate_ratio_metrics` shall calculate aggregate ratio metrics from return values.
- [x] Architectural Mandate: derived ratios may use deterministic `float64` arithmetic only where exact decimal arithmetic is not appropriate, with documented tolerance stored in configuration, tests, and report metadata.

#### Non-Functional & Security Requirements
- [x] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [x] No file-specific testing requirements defined.

### File: app/services/analytics/distributions.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/analytics/distributions.py`.

#### Functional Requirements
- [x] `return_distribution` shall calculate a statistical summary of returns.
- [x] `r_multiple_distribution` shall calculate a statistical summary of R-multiple values.
- [x] `distributions_r_multiple_distribution` shall expose distribution-module R-multiple distribution behavior without colliding with metrics exports.
- [x] `percentile_summary` shall return selected percentile values.
- [x] `upside_downside_summary` shall summarize positive and negative outcome distributions.
- [x] `skewness` shall calculate return or value skewness.
- [x] `kurtosis` shall calculate excess kurtosis.
- [x] `higher_moments` shall calculate detailed skewness and kurtosis context.
- [x] `fat_tail_score` shall estimate tail heaviness relative to normal behavior.
- [x] `tail_ratio` shall calculate the ratio between upper-tail and lower-tail percentile magnitudes.
- [x] `jarque_bera_test` shall run a Jarque-Bera normality diagnostic.
- [x] `shapiro_wilk_test` shall run a Shapiro-Wilk normality diagnostic.
- [x] `qq_plot_data` shall generate theoretical and actual quantile data for Q-Q plotting.
- [x] `fit_distribution` shall fit a theoretical distribution and return fit parameters.
- [x] `distribution_fit_quality` shall return fit-quality diagnostics such as likelihood and information criteria.
- [x] `histogram_data` shall generate histogram bin data for plotting.
- [x] `detect_outliers` shall identify outliers with the requested method and threshold.
- [x] `outlier_ratio` shall calculate the percentage of data points flagged as outliers.
- [x] `calculate_distribution_metrics` shall calculate aggregate distribution metrics from numeric values.

#### Non-Functional & Security Requirements
- [x] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [x] No file-specific testing requirements defined.

### File: app/services/analytics/benchmark.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/analytics/benchmark.py`.

#### Functional Requirements
- [x] Benchmark analytics must align strategy and benchmark return streams before comparison and must handle missing or non-overlapping periods safely.
- [x] Benchmark metrics must only be calculated after deterministic alignment of strategy and benchmark series.
- [x] Strategy and benchmark timestamps must be normalized to UTC before alignment.
- [x] Benchmark data must be restricted to the strategy analytics window unless explicit lookback is configured and recorded.
- [x] Missing benchmark currency metadata must emit a warning and restrict calculations to currency-neutral metrics unless a validated currency policy exists.
- [x] Portfolio analytics must not sum raw PnL across different profit currencies.
- [x] Portfolio, TCA, and base-currency analytics must require validated FX conversion data when source money values are in different currencies.
- [x] Missing required FX conversion data must produce blocker-level quality evidence for affected multi-currency portfolio or TCA sections.
- [x] Stale FX rates must be identified when FX age limits are configured, and affected converted values must be marked as estimated when stale data is used.
- [x] All money fields must include explicit currency or inherit a validated account base currency with lineage explaining the inheritance.
- [x] `beta` shall calculate the strategy beta coefficient relative to benchmark returns.
- [x] `alpha` shall calculate annualized Jensen-style alpha relative to benchmark returns.
- [x] `r_squared` shall calculate coefficient of determination between strategy and benchmark returns.
- [x] `tracking_error` shall calculate annualized tracking error between strategy and benchmark returns.
- [x] `information_ratio` shall calculate relative Sharpe-style information ratio.
- [x] `batting_average` shall calculate the percentage of periods where the strategy outperformed the benchmark.
- [x] `calculate_benchmark_metrics` shall calculate combined benchmark-relative metrics such as alpha and beta.
- [x] The module must not overstate strategy quality, robustness, or live readiness; report outputs should expose caveats where sample size, overfitting, missing benchmark, or partial data weaken confidence.
- [x] All timestamps must be timezone-aware or explicitly normalized to UTC before metric calculation, benchmark alignment, report hashing, or dashboard payload generation.
- [x] ADR Required: `ADR-ANALYTICS-LIMITS` must record exact maximum input sizes, response payload limits, runtime budgets, memory budgets, statistical iteration limits, dashboard point limits, reference hardware, and benchmark method before Builder handoff.
- [x] Performance benchmark tests must fail the handoff gate until `ADR-ANALYTICS-LIMITS` supplies exact dataset sizes, hardware profile, benchmark method, runtime thresholds, memory thresholds, and statistical-validation iteration limits.
- ADR Required: `ADR-ANALYTICS-LIMITS` must approve maximum accepted input sizes, response payload sizes, runtime budgets, memory budgets, statistical iteration limits, reference hardware profile, and performance benchmark method.

#### Non-Functional & Security Requirements
- [x] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [x] No file-specific testing requirements defined.

### File: app/services/analytics/efficiency.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/analytics/efficiency.py`.

#### Functional Requirements
- [x] `capital_efficiency` shall calculate return per unit of nominal capital deployed.
- [x] `return_per_unit_mae` shall calculate total return relative to adverse excursion experienced.
- [x] `return_per_calendar_day` shall calculate net profit per calendar day in the test period.
- [x] `exit_efficiency` shall calculate combined win-capture and loss-containment efficiency.
- [x] `loss_containment_efficiency` shall calculate how well realized losses stayed above their adverse excursion.

#### Non-Functional & Security Requirements
- [x] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [x] No file-specific testing requirements defined.

### File: app/services/analytics/scorecard.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/analytics/scorecard.py`.

#### Functional Requirements
- [x] No metric may be referenced in an official tool schema, report schema, dashboard payload, scorecard rule, warning rule, or quality-flag rule until its Metric Definition Catalog entry is approved.
- [x] Metric definitions must document whether outputs are calculated facts, diagnostic estimates, warning evidence, scorecard inputs, or non-binding review context.
- [x] `evaluate_strategy_quality` shall evaluate a supplied analytics report and return strategy-quality decision context, score, strengths, warnings, and recommended action.

#### Non-Functional & Security Requirements
- [x] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [x] No file-specific testing requirements defined.

### File: app/services/analytics/report.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/analytics/report.py`.

#### Functional Requirements
- [x] Overview/report tools must combine lower-level analytics into grouped payloads that remain serializable for API and dashboard consumers.
- [x] The module must generate a complete, versioned `AnalyticsReport` from a valid backtest, optimization candidate, out-of-sample, walk-forward, paper, live, or normalized trading result when required inputs are available.
- [x] Report building must validate inputs, normalize result data, run required metric groups, run optional metric groups, collect warnings and quality flags, build dashboard payloads, validate output, compute hashes, and return a standard tool response.
- [x] Missing optional inputs must produce warnings or skipped-section metadata rather than fabricated metric values.
- [x] Critical metric group failures must return an error unless diagnostic partial mode is explicitly configured.
- [x] Partial reports must include `report_status = "partial"`, affected sections, skipped/failed/degraded section metadata, warnings, quality flags, lineage, and JSON-safe values.
- [x] Report generation must define section criticality as required, optional, diagnostic-only, disabled, skipped, failed, or degraded.
- [x] Required-section failure must return an error unless diagnostic partial mode is explicitly enabled.
- [x] Optional-section failure must produce skipped or failed section metadata without fabricating the missing section.
- [x] Partial reports must be marked non-promotable and must not be consumed as final approval evidence.
- [x] Report metadata must preserve `request_id`, optional `workflow_id`, run IDs, strategy identifiers, strategy version, schema version, analytics engine version, annualization settings, optional-section status, source context, and creation time.
- [x] Hashing rules must exclude non-deterministic fields such as generation timestamps unless explicitly documented.
- [x] Hashes must be computed from canonical JSON serialization with deterministic key ordering, documented numeric normalization, and documented exclusion rules for non-deterministic fields.
- [x] Analytics must propagate upstream data-quality and bias evidence into report warnings and quality flags.
- [x] Dashboard payload builders must consume validated `AnalyticsReport` sections and must not recompute core metrics.
- [x] `format_summary_as_rows` shall format raw summary data into report/display rows.
- [x] `build_backtest_report` shall build a structured backtest analytics report payload.
- [x] `print_statistical_validation_report` shall package a comprehensive statistical validation report.
- [x] Report generation must be idempotent for the same input, configuration, and analytics engine version.
- [x] Reports must include reproducibility metadata, input hashes, configuration hashes, report hashes, and lineage.
- [x] Annualized metrics must use explicit annualization settings stored in configuration and report metadata; the module must not silently guess annualization when frequency cannot be inferred safely.
- [x] Cache hits, misses, evictions, and concurrent duplicate requests must not change metric values, warning order, report hashes, dashboard payloads, or quality-flag outcomes.
- [x] Sequential and parallel execution over the same report inputs must not change metric values, warning order, report hashes, dashboard payloads, or quality-flag outcomes.
- [x] Warning and quality-flag ordering must be deterministic where output hashes, dashboard payloads, report comparison, or tests depend on order.
- [x] Architectural Mandate: canonical monetary sums, cost aggregation, and base-currency aggregation must use `Decimal` normalization for hashing and report contracts.
- [x] Report metadata must identify the monetary precision mode used, such as `decimal` or `float64_with_tolerance`.
- [x] The module must define concrete runtime limits for bootstrap, permutation, Monte Carlo, distribution fitting, dashboard downsampling, and report generation before production handoff.
- [x] `build_analytics_report` latency, statistical-validation runtime, throughput, memory, and payload-size targets must be measurable before Builder handoff.
- [x] Documentation must include report section criticality and partial-report behavior.
- [x] Documentation must include schema compatibility policy for accepted, deprecated, legacy-adapted, and unsupported report/result versions.
- [x] Documentation must include partial-report examples showing skipped, failed, and degraded section metadata.
- Metric kernels are exposed only through stable, versioned official tool/report interfaces and must not be treated as agent/API-facing just because they exist in source files, imports, or historical examples.
- ADR Required: `ADR-ANALYTICS-REPORT-CONTRACTS` must approve report section criticality for `AnalyticsReport`, `PortfolioAnalyticsReport`, dashboard payloads, prop-firm evidence, live degradation, and diagnostic partial mode.
- ADR Required: `ADR-ANALYTICS-TRACEABILITY` must approve requirement-to-test traceability matrix coverage for every official public tool, canonical report contract, dashboard payload, adapter mapping, and failure envelope.
- [x] `TradingResult`, `AnalyticsReport`, `PortfolioAnalyticsReport`, dashboard payloads, warning objects, quality flags, and error envelopes have versioned schemas.
- [x] Report section criticality and partial-report non-promotable behavior are approved.
- [x] Requirement-to-test traceability matrix maps every official tool, report contract, adapter mapping, warning/quality flag, and failure envelope to tests.
- [x] Usage examples cover success, validation failure, partial report, dashboard truncation, and request-ID traceability.

#### Non-Functional & Security Requirements
- [x] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- Partial report outputs that must remain non-promotable and JSON-safe.

### File: app/services/analytics/dashboard.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/analytics/dashboard.py`.

#### Functional Requirements
- [x] Dashboard payloads must include chart/table data, finite numeric values, ISO-8601 timestamps, units, warnings, and metadata sufficient for UI/API consumers.
- [x] If a required source section is missing, failed, skipped, or degraded, the dashboard payload must include section-status metadata and warnings rather than recomputing or fabricating chart/table values.
- [x] Dashboard/UI consumers must not need to recalculate core metrics.
- [x] Dashboard payload support must be classified by chart/table type as required, optional, or future before Builder implementation.
- [x] Truncated payload metadata must include whether truncation occurred, original point count, returned point count, truncation method or algorithm, and truncation reason.
- [x] `build_overview_payload` shall build the API/dashboard analytics overview payload.
- [x] Result payloads must be JSON-safe or convertible to JSON-safe structures for API and dashboard consumers.
- [x] Dashboard payloads must obey configured size limits and deterministic truncation policies when limits are defined.
- [x] The module must define concrete maximum response payload size and deterministic truncation behavior for dashboard and API payloads before production handoff.
- [x] Documentation must include required, optional, and future dashboard payload classes.
- [x] Documentation must include dashboard truncation examples showing truncation metadata.
- ADR Required: `ADR-ANALYTICS-DASHBOARD` must approve dashboard required/optional/future payload classes and deterministic downsampling/truncation method.
- [x] Concrete input-size, runtime, memory, response-size, dashboard truncation, statistical iteration, and performance targets are approved with a hardware/profile context.
- ADR Required: `ADR-ANALYTICS-DASHBOARD` must select a deterministic, auditable dashboard downsampling algorithm before production handoff.

#### Non-Functional & Security Requirements
- [x] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [x] No file-specific testing requirements defined.

## 7. Global Testing, Quality Gates, and Usage Examples


### 7.3 Usage Examples

#### Example 1
```python
import pandas as pd
from app.services.analytics import total_trades, win_rate, profit_factor

trades = pd.DataFrame(
    [
        {"open_time": "2026-01-01", "close_time": "2026-01-02", "type": "buy", "profit_loss": 120.0},
        {"open_time": "2026-01-03", "close_time": "2026-01-04", "type": "sell", "profit_loss": -40.0},
    ]
)

trade_count = total_trades(trades, request_id="req_analytics_example")
win_rate_result = win_rate(trades, request_id="req_analytics_example")
profit_factor_result = profit_factor(trades, request_id="req_analytics_example")

assert trade_count["metadata"]["tool_category"] == "analytics"
assert win_rate_result["status"] in {"success", "error"}
assert profit_factor_result["metadata"]["read_only"] is True
```

#### Example 2
```python
import pandas as pd
from app.services.analytics import get_analytics_overview

trades = pd.DataFrame(
    [
        {
            "open_time": "2026-01-01T00:00:00Z",
            "close_time": "2026-01-01T04:00:00Z",
            "type": "buy",
            "profit_loss": 100.0,
            "initial_risk": 50.0,
            "mae": -20.0,
            "mfe": 140.0,
            "size": 1.0,
        }
    ]
)

overview = get_analytics_overview(
    trades,
    initial_balance=10000.0,
    start_time="2026-01-01T00:00:00Z",
    end_time="2026-01-02T00:00:00Z",
    request_id="req_analytics_overview",
)

if overview["status"] == "success":
    payload = overview["data"]
else:
    error = overview["error"]
```

#### Example 3
```python
from app.services.analytics import sample_size_warning, bootstrap_probability_above_threshold

returns = [0.01, -0.005, 0.012, 0.004, -0.003]

sample_warning = sample_size_warning(
    len(returns),
    min_recommended=100,
    request_id="req_analytics_stats",
)

probability = bootstrap_probability_above_threshold(
    returns,
    threshold=0.0,
    seed=42,
    request_id="req_analytics_stats",
)
```

#### Example 4
```python
from app.services.analytics import build_analytics_report, evaluate_strategy_quality

trading_result = {
    "schema_version": "1.3.1",
    "result_id": "bt_run_example",
    "phase": "backtest",
    "strategy_id": "strategy_demo",
    "strategy_version": "v1",
    "account_base_currency": "USD",
    "start_time": "2026-01-01T00:00:00Z",
    "end_time": "2026-01-31T23:59:59Z",
    "symbols": ["EURUSD"],
    "timeframe": "H1",
    "trades": [
        {
            "trade_id": "t1",
            "symbol": "EURUSD",
            "direction": "long",
            "open_time": "2026-01-02T00:00:00Z",
            "close_time": "2026-01-02T04:00:00Z",
            "net_pnl": 100.0,
            "currency": "USD",
        }
    ],
    "equity_curve": [
        {"timestamp": "2026-01-01T00:00:00Z", "equity": 10000.0, "currency": "USD"},
        {"timestamp": "2026-01-02T04:00:00Z", "equity": 10100.0, "currency": "USD"},
    ],
    "metadata": {"data_quality_status": "passed"},
}

report_response = build_analytics_report(
    trading_result,
    request_id="req_analytics_report",
)

if report_response["status"] == "success":
    scorecard = evaluate_strategy_quality(
        report_response["data"],
        request_id="req_analytics_scorecard",
    )
```

#### Example 5
```python
from app.services.analytics import build_portfolio_analytics_report, compare_analytics_reports

portfolio_response = build_portfolio_analytics_report(
    {
        "schema_version": "1.3.1",
        "portfolio_run_id": "portfolio_run_example",
        "account_base_currency": "USD",
        "component_results": [],
        "fx_rates": [],
    },
    request_id="req_portfolio_analytics",
)

comparison_response = compare_analytics_reports(
    reference_report={"schema_version": "1.3.1", "report_id": "reference"},
    candidate_report={"schema_version": "1.3.1", "report_id": "candidate"},
    request_id="req_report_compare",
)
```

#### Example 6
```python
from app.services.analytics import build_analytics_report

response = build_analytics_report(
    {"schema_version": "1.3.1", "result_id": "missing_required_sections"},
    request_id="req_analytics_validation_failure",
)

assert response["status"] == "error"
assert response["error"]["code"] in {"VALIDATION_FAILED", "INVALID_INPUT"}
assert response["metadata"]["request_id"] == "req_analytics_validation_failure"
assert response["metadata"]["tool_category"] == "analytics"
assert response["metadata"]["read_only"] is True
assert response["metadata"]["places_trade"] is False
```

#### Example 7
```python
from app.services.analytics import build_analytics_report

response = build_analytics_report(
    {
        "schema_version": "1.3.1",
        "result_id": "bt_run_partial_example",
        "phase": "backtest",
        "strategy_id": "strategy_demo",
        "strategy_version": "v1",
        "account_base_currency": "USD",
        "trades": [],
        "equity_curve": [
            {"timestamp": "2026-01-01T00:00:00Z", "equity": 10000.0, "currency": "USD"}
        ],
    },
    diagnostic_partial_mode=True,
    request_id="req_analytics_partial",
)

assert response["status"] == "success"
assert response["data"]["report_status"] == "partial"
assert response["data"]["sections"]["benchmark_metrics"]["status"] == "skipped"
assert response["data"]["sections"]["benchmark_metrics"]["skipped"]["reason"] == "missing_benchmark_data"
assert response["data"]["warnings"][0]["code"] == "ANALYTICS_SECTION_SKIPPED"
assert response["data"]["quality_flags"][0]["blocks_promotion"] is True
assert response["metadata"]["request_id"] == "req_analytics_partial"
```

## 8. Acceptance
