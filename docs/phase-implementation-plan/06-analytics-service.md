## Phase 6 Analytics Service

### Goal

Implement the Analytics Service requirements under `app/services/analytics/` while preserving the phase module boundaries and governance rules.

Task inventory: 465 checkbox tasks (465 checked, 0 unchecked).

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

- [X] Analytics functions must be read-only and side-effect free at the domain level. *tests/unit/app/services/analytics/test_catalogs.py:170*
- [X] Importing the analytics registry should not perform live broker calls, network calls, database mutations, or trading side effects. *tests/unit/app/services/analytics/test_catalogs.py:170*
- [X] Official tools must be stateless, retry-safe, and safe for parallel optimization or portfolio workflows. *tests/unit/app/services/analytics/test_catalogs.py:122*
- [X] Metric kernels must not depend on mutable global calculation state. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] Local/read-through caches, if implemented, must define TTL, maximum size, eviction behavior, invalidation keys, lock timeout, stale-read behavior, and single-flight or equivalent thundering-herd prevention before Builder handoff. *tests/unit/app/services/analytics/test_catalogs.py:122*
- [X] Distributed caching, distributed invalidation services, message queues, and async background workers must not be implemented inside Analytics. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Portfolio aggregation must fail closed when required base-currency conversion is unavailable. *tests/unit/app/services/analytics/test_report.py:100*
- [X] The analytics registry must expose only intentional public analytics tools and must not hide colliding function names; duplicate concepts must use module-qualified aliases where needed. *app/services/analytics/models.py:281*
- [X] Every official exported analytics tool must be callable, documented, and accept a `request_id` parameter for traceability. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Each official public capability must be labeled as stable, approved experimental, deprecated, or internal-support-only. *app/services/analytics/models.py:281*
- [X] Each official public capability must document whether it is safe for agent/API use. *app/services/analytics/models.py:281*
- [X] The analytics registry must distinguish official tools, internal metric kernels, compatibility aliases, and deprecated exports. *app/services/analytics/models.py:201*
- [X] Agentic workflows must import analytics capabilities from `app.services.analytics` rather than deep module files. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Strategy-version mismatch must be handled explicitly during degradation pairing and must not be hidden inside aggregate scores. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Low-sample explainability drivers must not appear in ranked driver lists. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] `common_avg_loss` shall expose the common-module average-loss function without colliding with metrics exports. *app/services/analytics/__init__.py:330*
- [X] `common_get_r_multiples` shall expose the common-module R-multiple function without colliding with metrics exports. *app/services/analytics/__init__.py:331*
- [X] `max_gross_size_held` shall calculate the maximum absolute total size held across positions. *app/services/analytics/trade.py:612*
- [X] `percent_time_in_market` shall calculate percent of the trading period spent in the market. *app/services/analytics/trade.py:647*
- [X] `metrics_get_r_multiples` shall expose metrics-module R-multiple behavior without colliding with common exports. *app/services/analytics/__init__.py:332*
- [X] `win_rate_fraction` shall calculate win rate on a 0-to-1 scale. *app/services/analytics/trade.py:655*
- [X] `avg_win_loss` shall calculate mean winning and losing outcomes. *app/services/analytics/trade.py:662*
- [X] `consecutive_wins_losses` shall calculate maximum consecutive wins and losses from numeric outcomes. *app/services/analytics/trade.py:670*
- [X] `t_statistic` shall calculate the t-statistic for mean outcome. *app/services/analytics/trade.py:695*
- [X] `open_position_pnl` shall calculate total unrealized PnL from open positions. *app/services/analytics/trade.py:708*
- [X] `slippage_paid` shall calculate total absolute slippage costs paid. *app/services/analytics/trade.py:716*
- [X] `commission_paid` shall calculate total absolute commission costs paid. *app/services/analytics/trade.py:720*
- [X] `swap_paid` shall calculate total absolute swap costs paid. *app/services/analytics/trade.py:724*
- [X] `metrics_avg_loss` shall expose metrics-module average-loss behavior without colliding with common exports. *app/services/analytics/__init__.py:333*
- [X] `expectancy_r` shall calculate R-expectancy. *app/services/analytics/trade.py:728*
- [X] `max_size_held` shall calculate maximum total contracts held. *app/services/analytics/trade.py:735*
- [X] `max_net_size_held` shall calculate maximum net directional size held. *app/services/analytics/trade.py:739*
- [X] `max_long_size_held` shall calculate maximum total long contracts held. *app/services/analytics/trade.py:743*
- [X] `max_short_size_held` shall calculate maximum total short contracts held. *app/services/analytics/trade.py:752*
- [X] `avg_r_multiple` shall calculate average R-multiple. *app/services/analytics/trade.py:761*
- [X] `median_r_multiple` shall calculate median R-multiple. *app/services/analytics/trade.py:765*
- [X] `r_expectancy` shall calculate R-space expectancy. *app/services/analytics/__init__.py:344*
- [X] `max_r_multiple` shall calculate maximum R-multiple. *app/services/analytics/trade.py:775*
- [X] `min_r_multiple` shall calculate minimum R-multiple. *app/services/analytics/trade.py:780*
- [X] `avg_consecutive_wins` shall calculate average length of winning streaks. *app/services/analytics/trade.py:809*
- [X] `avg_consecutive_losses` shall calculate average length of losing streaks. *app/services/analytics/trade.py:825*
- [X] `r_signal_to_noise` shall calculate mean R relative to R volatility. *app/services/analytics/trade.py:892*
- [X] `rolling_expectancy_stability` shall calculate expectancy stability over a rolling window. *app/services/analytics/trade.py:905*
- [X] `win_after_win_probability` shall calculate probability that a win follows a win. *app/services/analytics/trade.py:921*
- [X] `runs_test_zscore` shall calculate Wald-Wolfowitz runs-test z-score. *app/services/analytics/trade.py:935*
- [X] `get_analytics_overview` shall calculate comprehensive analytics across all, long, and short subsets. *app/services/analytics/trade.py:1362*
- [X] `calculate_spread_cost_impact` shall calculate spread cost drag. *app/services/analytics/trade.py:969*
- [X] `calculate_slippage_impact` shall calculate slippage cost drag. *app/services/analytics/trade.py:973*
- [X] `calculate_commission_impact` shall calculate commission cost drag. *app/services/analytics/trade.py:977*
- [X] `cagr` shall calculate compound annual growth rate. *app/services/analytics/equity.py:218*
- [X] `compound_monthly_growth_rate` shall calculate compound monthly growth rate. *app/services/analytics/equity.py:238*
- [X] `buy_and_hold_cagr` shall calculate buy-and-hold CAGR from price data. *app/services/analytics/equity.py:258*
- [X] `adjusted_gross_profit` shall calculate adjusted gross profit. *app/services/analytics/trade.py:981*
- [X] `adjusted_gross_loss` shall calculate adjusted gross loss. *app/services/analytics/trade.py:997*
- [X] `adjusted_net_profit` shall calculate adjusted net profit. *app/services/analytics/trade.py:1013*
- [X] `select_net_profit` shall calculate net profit after outlier selection. *app/services/analytics/trade.py:1017*
- [X] `select_gross_profit` shall calculate gross profit after outlier selection. *app/services/analytics/trade.py:1026*
- [X] `select_gross_loss` shall calculate gross loss after outlier selection. *app/services/analytics/trade.py:1035*
- [X] `max_runup` shall calculate maximum gain from valley to peak. *app/services/analytics/trade.py:1050*
- [X] `max_runup_date` shall identify the timestamp of maximum runup peak. *app/services/analytics/trade.py:1063*
- [X] `calculate_period_analysis` shall calculate performance by timestamp bucket. *app/services/analytics/trade.py:1082*
- [X] `calculate_long_short_split` shall calculate long-versus-short profit split. *app/services/analytics/trade.py:1096*
- [X] `calculate_session_performance` shall calculate session performance from timestamped records. *app/services/analytics/trade.py:1109*
- [X] `whites_reality_check` shall assess data-snooping bias with White's Reality Check. *app/services/analytics/distributions.py:272*
- [X] `probability_of_backtest_overfitting` shall estimate probability of backtest overfitting. *app/services/analytics/distributions.py:307*
- [X] `walk_forward_degradation_score` shall measure performance decay from in-sample to out-of-sample scores. *app/services/analytics/distributions.py:312*
- [X] `bonferroni_correction` shall apply Bonferroni correction for multiple hypothesis testing. *app/services/analytics/distributions.py:322*
- [X] `benjamini_hochberg_correction` shall apply Benjamini-Hochberg false-discovery-rate control. *app/services/analytics/distributions.py:327*
- [X] `stability_score` shall calculate performance consistency across walk-forward windows. *app/services/analytics/distributions.py:338*
- [X] `whites_reality_check_backtests` shall run White's Reality Check against backtest result objects. *app/services/analytics/distributions.py:349*
- [X] Documentation must include success examples for each approved official high-level tool. *app/services/analytics/README.md:9*
- [X] Documentation must include validation-failure examples showing the standard error envelope. *app/services/analytics/README.md:9*
- [X] Low-level metric examples must be labeled as internal/developer examples when they are not official agent/API tools. *app/services/analytics/models.py:201*

#### `app/__init__.py`

Functions/classes:

- `total_return`
- `return_on_initial_capital`
- `MetricDefinitionCatalog`

Requirements:

- [X] Undefined or unsupported metric values must be represented as omitted fields or `None` according to the output schema plus structured warnings or skipped-section metadata; they must not be serialized as `NaN`, infinity, fabricated zero, or display-only caps. *tests/unit/app/services/analytics/test_report.py:47*
- [X] R-multiple fallback proxies must be listed in the Metric Definition Catalog before use; fallback-derived R-multiple values must include warning metadata and mark the affected metric confidence as degraded. *app/services/analytics/models.py:201*
- [X] Every official metric must define formula, units, required inputs, optional inputs, accepted aliases, return scale, annualization basis, sample/population convention, minimum sample size, undefined-result behavior, and golden-fixture expectations. *app/services/analytics/models.py:201*
- [X] `total_return` shall calculate total return as a percentage of initial capital. *app/services/analytics/equity.py:90*
- [X] `return_on_initial_capital` shall calculate net profit as a percentage of initial capital. *app/services/analytics/equity.py:97*
- [X] Numeric outputs must avoid misleading precision and must handle empty, missing, non-finite, zero-denominator, and insufficient-sample scenarios consistently. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Documentation must include the Metric Definition Catalog. *app/services/analytics/models.py:201*
- [X] Official Analytics Tool Catalog is approved and maps every official tool to schemas, errors, metadata, side effects, stability, and tests. *app/services/analytics/models.py:281*
- [X] Metric Definition Catalog is approved and no official schema references uncataloged metrics. *app/services/analytics/models.py:201*
- [X] Public/internal export classification is approved, including compatibility aliases and deprecated exports. *app/services/analytics/models.py:281*
- [X] Analytics-owned private canonical metric-kernel model is documented and enforced through public/internal export classification tests. *app/services/analytics/models.py:281*
- [X] Schema compatibility matrix defines accepted, deprecated, legacy-adapted, rejected, and unsupported future versions. *app/services/analytics/models.py:12*
- [X] Decimal monetary precision mandate and deterministic derived-ratio tolerance policy are documented in schemas, metadata, and tests. *tests/unit/app/services/analytics/test_report.py:47*
- [X] No file-specific non-functional requirements defined. *app/services/analytics/README.md:9*
- [X] No file-specific testing requirements defined. *app/services/analytics/README.md:9*

#### `app/services/analytics/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [X] No file-specific functional requirements defined. Foundation properties apply. *app/services/analytics/README.md:9*
- [X] No file-specific non-functional requirements defined. *app/services/analytics/README.md:9*
- [X] No file-specific testing requirements defined. *app/services/analytics/README.md:9*
- [X] No file-specific functional requirements defined. Foundation properties apply. *app/services/analytics/README.md:9*
- [X] No file-specific non-functional requirements defined. *app/services/analytics/README.md:9*
- [X] No file-specific testing requirements defined. *app/services/analytics/README.md:9*

#### `app/services/analytics/adapters.py`

Functions/classes:

- `BacktestResult`
- `PaperTradingResult`
- `LiveTradingResult`
- `TradingResult`

Requirements:

- [X] Backtest, paper, live, portfolio, and normalized trading results must either inherit from a canonical `TradingResult` contract or be converted into it through deterministic adapters. *app/services/analytics/adapters.py:13*
- [X] Deterministic adapters must preserve schema version, result ID, phase/environment, timestamps, account base currency, strategy identifiers, symbols, timeframe, trades, equity curve, optional balance curve, benchmark data, upstream quality metadata, and source metadata without silent field loss. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Deterministic adapters must define source-to-canonical field mappings, required fields, optional fields, defaulting behavior, unsupported-field behavior, lossless metadata preservation rules, and warning/error behavior for missing or incompatible fields. *tests/unit/app/services/analytics/test_report.py:47*
- [X] No file-specific non-functional requirements defined. *app/services/analytics/README.md:9*
- [X] No file-specific testing requirements defined. *app/services/analytics/README.md:9*
- [X] Documentation must include adapter field-mapping tables for every supported upstream result type. *app/services/analytics/README.md:9*

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

- [X] Official analytics tools must not write files, modify databases, place trades, or require network access. *tests/unit/app/services/analytics/test_catalogs.py:170*
- [X] Analytics input conversion must support common developer inputs such as pandas dataframes, pandas series, lists of trade records, and lists of numeric values where the public capability expects them. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Trade-oriented tools must use closed-trade semantics when a metric is defined over realized results. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Closed-trade filtering must exclude records explicitly marked as still open or end-of-data placeholders and must ignore records without close timestamps when close timestamps are required. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Trade classification must distinguish wins, losses, and breakevens using a configured `breakeven_epsilon` from the Metric Definition Catalog or numeric policy ADR so near-zero PnL does not become a false win or loss. *app/services/analytics/models.py:201*
- [X] Exposure and time-in-market analytics must merge overlapping trade intervals so simultaneous positions are measured as market presence once for duration metrics. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Long/short split analytics must classify direction using the supplied trade direction/type fields and must not infer trade direction from PnL. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Cost-impact analytics must quantify spread, slippage, and commission drag from supplied cost and gross-profit inputs without mutating the source trades. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Aggregated analytics must preserve source context enough for downstream consumers to know whether inputs came from all trades, long trades, short trades, benchmark comparisons, cost analysis, or statistical validation. *tests/unit/app/services/analytics/test_catalogs.py:122*
- [X] `AnalyticsReport` output must include summary, trade metrics, equity metrics, return metrics, drawdown metrics, risk metrics, ratio metrics, distribution metrics, benchmark metrics, efficiency metrics, statistical validation, cost breakdown, warnings, quality flags, dashboard payloads, lineage, and metadata when those sections are applicable. *app/services/analytics/report.py:40*
- [X] Report hashes must include deterministic input hash, config hash, report hash, trade ledger hash, equity curve hash, and optional benchmark hash where the source material exists. *tests/unit/app/services/analytics/test_report.py:47*
- [X] ADR Required: `ADR-ANALYTICS-PUBLIC-SURFACE` must approve the initial official high-level tool surface before Builder implementation; candidate tools include `build_analytics_report`, `build_portfolio_analytics_report`, `evaluate_strategy_quality`, `compare_analytics_reports`, `calculate_trade_metrics`, `calculate_equity_metrics`, `calculate_drawdown_metrics`, `calculate_risk_metrics`, `calculate_benchmark_metrics`, `calculate_statistical_validation`, and `calculate_prop_firm_compliance`. *app/services/analytics/report.py:92*
- [X] Candidate dashboard payloads include summary cards, equity curve chart, drawdown curve chart, monthly returns heatmap, rolling ratio charts, rolling drawdown chart, trade distribution chart, cost breakdown chart, symbol contribution chart, warning table, and quality flag table when source sections exist. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] `get_closed_trades` shall filter trade records to realized closed trades. *app/services/analytics/trade.py:63*
- [X] `classify_trades` shall classify trades into wins, losses, and breakevens using a consistent threshold. *app/services/analytics/trade.py:76*
- [X] `avg_loss` shall calculate the mean loss of losing trades. *app/services/analytics/trade.py:264*
- [X] `get_r_multiples` shall calculate R-multiples for trades. *app/services/analytics/trade.py:94*
- [X] `trade_pnl_distribution` shall calculate a statistical summary of realized trade PnL. *app/services/analytics/trade.py:1126*
- [X] `trade_level_drawdowns` shall calculate cumulative PnL drawdowns at trade close points. *app/services/analytics/trade.py:1140*
- [X] `max_close_to_close_drawdown` shall calculate maximum trade-level peak-to-valley decline including excursion context where available. *app/services/analytics/trade.py:1157*
- [X] `avg_trade_drawdown` shall calculate mean trade-level close-to-close drawdown depth. *app/services/analytics/trade.py:1162*
- [X] `max_consecutive_drawdown_trades` shall calculate maximum number of consecutive trades inside a strategy drawdown. *app/services/analytics/trade.py:1167*
- [X] `max_close_to_close_drawdown_date` shall identify the timestamp of deepest trade-level valley. *app/services/analytics/trade.py:1180*
- [X] `avg_trade_notional_efficiency` shall provide the capital-efficiency metric under a clearer average-trade-notional name. *app/services/analytics/trade.py:1201*
- [X] `avg_return_per_risk_unit` shall calculate average R-multiple per closed trade. *app/services/analytics/trade.py:1214*
- [X] `return_per_trade_hour` shall calculate net profit per hour spent in active trades. *app/services/analytics/trade.py:1219*
- [X] `return_per_market_hour` shall calculate net profit per hour where at least one trade was open. *app/services/analytics/trade.py:1226*
- [X] `trades_per_day` shall calculate average number of closed trades per calendar day in the test period. *app/services/analytics/trade.py:1233*
- [X] `profit_per_trade_per_day` shall calculate net profit normalized by both number of trades and calendar days. *app/services/analytics/trade.py:1240*
- [X] `mfe_efficiency` shall calculate average percentage of MFE captured by winning trades. *app/services/analytics/trade.py:1249*
- [X] `aggregate_mfe_capture_ratio` shall calculate aggregate MFE capture ratio for winning trades. *app/services/analytics/trade.py:1262*
- [X] `mae_efficiency` shall calculate realized-loss-to-MAE efficiency for losing trades. *app/services/analytics/trade.py:1266*
- [X] `aggregate_loss_containment_efficiency` shall calculate aggregate loss containment for losing trades. *app/services/analytics/trade.py:1272*
- [X] `position_size_efficiency` shall calculate relationship between position size and normalized trade outcome. *app/services/analytics/trade.py:1278*
- [X] `calculate_efficiency_metrics` shall calculate aggregate MAE/MFE efficiency context from trades. *app/services/analytics/trade.py:1294*
- [X] `get_ordered_closed_trades` shall filter closed trades and sort them for sequence-dependent metrics. *app/services/analytics/trade.py:120*
- [X] `total_trades` shall count closed trades. *app/services/analytics/trade.py:132*
- [X] `winning_trades` shall count closed winning trades. *app/services/analytics/trade.py:220*
- [X] `losing_trades` shall count closed losing trades. *app/services/analytics/trade.py:224*
- [X] `breakeven_trades` shall count closed breakeven trades. *app/services/analytics/trade.py:228*
- [X] `long_trades` shall count closed long trades. *app/services/analytics/trade.py:232*
- [X] `short_trades` shall count closed short trades. *app/services/analytics/trade.py:238*
- [X] `count_open_trades` shall count currently open trades. *app/services/analytics/trade.py:244*
- [X] `win_rate` shall calculate percentage of winning trades. *app/services/analytics/trade.py:154*
- [X] `loss_rate` shall calculate percentage of losing trades. *app/services/analytics/trade.py:250*
- [X] `avg_win` shall calculate mean profit of winning trades. *app/services/analytics/trade.py:257*
- [X] `largest_win` shall calculate maximum single-trade profit. *app/services/analytics/trade.py:271*
- [X] `largest_loss` shall calculate maximum single-trade loss. *app/services/analytics/trade.py:278*
- [X] `median_win` shall calculate median PnL of winning trades. *app/services/analytics/trade.py:285*
- [X] `median_loss` shall calculate median PnL of losing trades. *app/services/analytics/trade.py:295*
- [X] `expectancy` shall calculate trade expectancy. *app/services/analytics/trade.py:305*
- [X] `max_consecutive_wins` shall calculate maximum consecutive winning trades. *app/services/analytics/trade.py:313*
- [X] `max_consecutive_losses` shall calculate maximum consecutive losing trades. *app/services/analytics/trade.py:327*
- [X] `avg_time_in_trade` shall calculate average trade duration. *app/services/analytics/trade.py:349*
- [X] `median_time_in_trade` shall calculate median trade duration. *app/services/analytics/trade.py:356*
- [X] `max_time_in_trade` shall calculate maximum trade duration. *app/services/analytics/trade.py:366*
- [X] `min_time_in_trade` shall calculate minimum trade duration. *app/services/analytics/trade.py:371*
- [X] `compute_r_trade_metrics` shall calculate trade metrics from R-multiple inputs. *app/services/analytics/trade.py:376*
- [X] `compute_trade_metrics` shall calculate trade metrics from numeric R values and optional MAE/MFE arrays. *app/services/analytics/trade.py:384*
- [X] `trade_efficiency` shall calculate realized outcome relative to maximum favorable excursion. *app/services/analytics/trade.py:392*
- [X] `trade_outcome_entropy` shall calculate Shannon entropy of trade outcomes. *app/services/analytics/trade.py:400*
- [X] `longest_flat_period_duration` shall calculate longest period without an active trade. *app/services/analytics/trade.py:416*
- [X] `calculate_trade_metrics` shall calculate aggregate core trade metrics from normalized trade records. *app/services/analytics/trade.py:1303*
- [X] `calculate_analytics_for_subset` shall calculate all analytics categories for a supplied trade subset. *app/services/analytics/trade.py:1349*
- [X] `return_over_drawdown` shall calculate total return relative to maximum trade drawdown. *app/services/analytics/trade.py:442*
- [X] `net_profit_as_percent_of_max_trade_drawdown` shall calculate net profit as a percentage of max trade drawdown. *app/services/analytics/trade.py:448*
- [X] `select_net_profit_as_percent_of_max_trade_drawdown` shall calculate selected net profit as a percentage of max trade drawdown. *app/services/analytics/trade.py:454*
- [X] `adjusted_net_profit_as_percent_of_max_trade_drawdown` shall calculate adjusted net profit as a percentage of max trade drawdown. *app/services/analytics/trade.py:460*
- [X] `net_profit` shall calculate total realized profit or loss from closed trades. *app/services/analytics/trade.py:466*
- [X] `gross_profit` shall sum winning closed-trade profit. *app/services/analytics/trade.py:470*
- [X] `gross_loss` shall sum losing closed-trade loss. *app/services/analytics/trade.py:476*
- [X] `balance_curve_from_closed_trades` shall generate a realized balance curve from closed trades. *app/services/analytics/trade.py:482*
- [X] `balance_curve` shall expose balance-curve behavior as an alias of closed-trade balance curve generation. *app/services/analytics/trade.py:518*
- [X] `equity_curve` shall expose equity-curve behavior for common orchestration using the closed-trade curve. *app/services/analytics/trade.py:524*
- [X] `max_loss_probability` shall calculate probability of a single trade loss exceeding a threshold. *app/services/analytics/trade.py:530*
- [X] `risk_of_ruin` shall estimate ruin probability through Monte Carlo simulation of trade outcomes. *app/services/analytics/trade.py:538*
- [X] `avg_trade_nominal_exposure` shall calculate average nominal exposure per trade. *app/services/analytics/trade.py:563*
- [X] `max_single_trade_margin_utilization` shall calculate maximum margin used by a single trade as a percentage of equity. *app/services/analytics/trade.py:575*
- [X] `avg_single_trade_margin_utilization` shall calculate average margin used per trade as a percentage of equity. *app/services/analytics/trade.py:580*
- [X] `risk_of_ruin_with_custom_horizon` shall estimate ruin probability over a fixed future trade horizon. *app/services/analytics/trade.py:588*
- [X] The module must define concrete maximum accepted input sizes for trades, equity points, benchmark points, portfolio components, dashboard payloads, and statistical observations before production handoff. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] No file-specific non-functional requirements defined. *app/services/analytics/README.md:9*
- [X] No file-specific testing requirements defined. *app/services/analytics/README.md:9*

#### `app/services/analytics/equity.py`

Functions/classes:

- `NaT`
- `Infinity`
- `VALIDATION_FAILED`
- `calculate_drawdown_metrics`
- `compute_equity_metrics`
- `calculate_return_metrics`

Requirements:

- [X] Equity and return analytics must sort and normalize supplied series deterministically; optional `NaN`/`NaT` observations may be filtered only with recorded warning metadata, required `NaN`/`NaT` fields must fail validation unless the Metric Definition Catalog marks them skippable, and `Infinity`/`-Infinity` at official boundaries must return `VALIDATION_FAILED`. *app/services/analytics/models.py:201*
- [X] Dashboard truncation/downsampling must be deterministic and must preserve first point, last point, local extrema where practical, drawdown troughs, equity highs, and timestamps associated with major, critical, or blocker warnings. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] `benchmark_returns` shall generate a return series from benchmark equity or price values. *app/services/analytics/equity.py:165*
- [X] `relative_drawdown_series` shall generate relative underperformance between strategy and benchmark equity. *app/services/analytics/equity.py:351*
- [X] `drawdown_series` shall calculate drawdown values from an equity curve. *app/services/analytics/equity.py:373*
- [X] `drawdown_duration_series` shall calculate drawdown duration values from an equity curve. *app/services/analytics/equity.py:387*
- [X] `max_drawdown_duration_from_equity` shall calculate maximum drawdown duration from equity values. *app/services/analytics/equity.py:405*
- [X] `max_strategy_drawdown_date` shall identify the timestamp of deepest strategy equity valley. *app/services/analytics/equity.py:410*
- [X] `avg_underwater_drawdown_percent` shall calculate average drawdown depth while equity is below peak. *app/services/analytics/equity.py:427*
- [X] `calculate_drawdown_metrics` shall calculate aggregate drawdown metrics from an equity curve. *app/services/analytics/drawdown.py:319*
- [X] `compute_equity_metrics` shall calculate equity metrics from return inputs. *app/services/analytics/equity.py:457*
- [X] `total_return_usd` shall calculate total return in currency units from an equity curve. *app/services/analytics/equity.py:83*
- [X] `returns_series` shall calculate percentage returns between equity points. *app/services/analytics/equity.py:101*
- [X] `log_returns_series` shall calculate logarithmic returns between equity points. *app/services/analytics/equity.py:114*
- [X] `daily_returns` shall calculate daily percentage returns from an equity curve. *app/services/analytics/equity.py:149*
- [X] `weekly_returns` shall calculate weekly percentage returns from an equity curve. *app/services/analytics/equity.py:153*
- [X] `monthly_returns` shall calculate monthly percentage returns from an equity curve. *app/services/analytics/equity.py:157*
- [X] `annual_returns` shall calculate annual percentage returns from an equity curve. *app/services/analytics/equity.py:161*
- [X] `calculate_return_metrics` shall calculate aggregate cumulative and average returns from an equity curve. *app/services/analytics/equity.py:473*
- [X] No file-specific non-functional requirements defined. *app/services/analytics/README.md:9*
- [X] Official analytics tools must validate `request_id`; missing, empty, malformed, or unsafe request IDs must return a structured validation error envelope. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Official analytics tools must return the standard tool envelope on success and on controlled validation failure. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Date/time analytics must parse supplied open/close timestamps, support both datetime-like and numeric timestamp inputs where implemented, and return JSON-safe values for durations and timestamps. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Live-vs-backtest and paper-vs-backtest degradation comparisons must validate strategy ID, strategy version, symbols, timeframe or return frequency, evaluation window, account base currency, and comparable cost/slippage model metadata before pairing. *tests/unit/app/services/analytics/test_report.py:47*
- [X] `win_loss_streaks` shall return winning and losing streak sequences. *app/services/analytics/trade.py:841*
- [X] `kelly_criterion` shall calculate Kelly criterion percentage from R-multiples or returns. *app/services/analytics/trade.py:881*
- [X] `avg_monthly_return` shall calculate arithmetic average monthly return. *app/services/analytics/equity.py:273*
- [X] `monthly_return_stddev` shall calculate monthly return volatility. *app/services/analytics/equity.py:288*
- [X] `annualized_return` shall calculate geometric annualized return. *app/services/analytics/equity.py:202*
- [X] `geometric_mean_return` shall calculate geometric mean return. *app/services/analytics/equity.py:183*
- [X] `best_return` shall calculate best single-period return. *app/services/analytics/equity.py:301*
- [X] `worst_return` shall calculate worst single-period return. *app/services/analytics/equity.py:306*
- [X] `buy_and_hold_return` shall calculate total buy-and-hold return from price data. *app/services/analytics/equity.py:169*
- [X] `return_volatility` shall calculate return standard deviation. *app/services/analytics/equity.py:311*
- [X] `downside_return_volatility` shall calculate volatility of returns below target. *app/services/analytics/equity.py:320*
- [X] `return_skewness` shall calculate return-distribution skewness. *app/services/analytics/equity.py:329*
- [X] `return_kurtosis` shall calculate return-distribution excess kurtosis. *app/services/analytics/equity.py:340*
- [X] `return_on_account` shall calculate return on required account size. *app/services/analytics/trade.py:1044*

#### `app/services/analytics/drawdown.py`

Functions/classes:

- `calculate_drawdown_series`
- `max_drawdown`
- `drawdown_duration`
- `drawdown_recovery`
- `underwater_curve`

Requirements:

- [X] Strategy-quality evaluation must rely only on the supplied report payload and must surface warnings for weak profitability, high drawdown, overfitting risk, small sample size, or other observable quality concerns. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Optional sections such as TCA metrics, attribution, prop-firm compliance evidence, drawdown distribution, tail-risk metrics, dynamic correlation, walk-forward analytics, metric comparisons, live degradation, and explainability must be represented as calculated, skipped, or failed. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Formula definitions must be explicit for Sharpe, Sortino, Calmar, Jensen alpha, beta, tracking error, information ratio, VaR, CVaR, expected shortfall, SQN, Kelly, drawdown duration, CAGR, profit factor, expectancy, and R-multiple metrics before those metrics are locked as official contracts. *app/services/analytics/models.py:201*
- [X] `max_relative_drawdown_percent` shall calculate maximum relative underperformance as a positive percentage. *app/services/analytics/drawdown.py:61*
- [X] `max_strategy_drawdown` shall calculate deepest peak-to-valley decline in currency units. *app/services/analytics/drawdown.py:36*
- [X] `max_strategy_drawdown_percent` shall calculate deepest percentage decline relative to running peak. *app/services/analytics/drawdown.py:48*
- [X] `max_drawdown` shall calculate maximum drawdown from returns. *app/services/analytics/drawdown.py:70*
- [X] `avg_drawdown` shall calculate average drawdown depth. *app/services/analytics/drawdown.py:80*
- [X] `drawdown_distribution` shall calculate detailed drawdown distribution statistics. *app/services/analytics/drawdown.py:92*
- [X] `max_drawdown_duration_from_returns` shall calculate maximum drawdown duration from return values. *app/services/analytics/drawdown.py:112*
- [X] `max_drawdown_duration` shall calculate maximum drawdown duration from the selected input type. *app/services/analytics/drawdown.py:123*
- [X] `avg_drawdown_duration` shall calculate average duration of drawdown episodes. *app/services/analytics/drawdown.py:128*
- [X] `time_to_recovery` shall calculate recovery periods for unique drawdowns. *app/services/analytics/drawdown.py:151*
- [X] `recovery_factor` shall calculate net profit relative to maximum drawdown. *app/services/analytics/drawdown.py:172*
- [X] `max_close_to_close_drawdown_percent` shall calculate close-to-close drawdown as a percentage. *app/services/analytics/drawdown.py:178*
- [X] `account_size_required` shall estimate capital required to withstand max close-to-close dips. *app/services/analytics/drawdown.py:189*
- [X] `avg_yearly_max_drawdown` shall average the maximum drawdown observed in each year. *app/services/analytics/drawdown.py:199*
- [X] `ulcer_index` shall calculate squared-drawdown-based ulcer index. *app/services/analytics/drawdown.py:213*
- [X] `pain_index` shall calculate mean absolute percentage drawdown. *app/services/analytics/drawdown.py:225*
- [X] `pain_ratio` shall calculate return relative to pain index. *app/services/analytics/drawdown.py:236*
- [X] `calmar_ratio` shall calculate annualized return relative to maximum drawdown. *app/services/analytics/drawdown.py:242*
- [X] `fouse_ratio` shall calculate Fouse drawdown-index-style ratio. *app/services/analytics/drawdown.py:248*
- [X] `sterling_ratio` shall calculate CAGR relative to adjusted average yearly maximum drawdown. *app/services/analytics/drawdown.py:254*
- [X] `rina_index` shall calculate select net profit relative to average drawdown and time in market. *app/services/analytics/drawdown.py:262*
- [X] `net_profit_as_percent_of_max_strategy_drawdown` shall calculate net profit as a percentage of max strategy drawdown. *app/services/analytics/drawdown.py:270*
- [X] `select_net_profit_as_percent_of_max_strategy_drawdown` shall calculate selected net profit as a percentage of max strategy drawdown. *app/services/analytics/drawdown.py:278*
- [X] `adjusted_net_profit_as_percent_of_max_strategy_drawdown` shall calculate adjusted net profit as a percentage of max strategy drawdown. *app/services/analytics/drawdown.py:284*
- [X] `return_on_max_strategy_drawdown` shall calculate total return relative to maximum strategy drawdown. *app/services/analytics/drawdown.py:290*
- [X] `return_on_max_close_to_close_drawdown` shall calculate net profit relative to maximum close-to-close drawdown. *app/services/analytics/drawdown.py:296*
- [X] `drawdown_probability` shall calculate probability of drawdown exceeding a threshold. *app/services/analytics/drawdown.py:304*
- [X] No file-specific non-functional requirements defined. *app/services/analytics/README.md:9*
- [X] No file-specific testing requirements defined. *app/services/analytics/README.md:9*

#### `app/services/analytics/risk.py`

Functions/classes:

- `calculate_risk_metrics`

Requirements:

- [X] Official analytics tools must be low-risk, read-only operations. *tests/unit/app/services/analytics/test_catalogs.py:170*
- [X] Metadata must include tool name, tool version, tool category, tool risk level, request ID, execution time, and side-effect flags. *tests/unit/app/services/analytics/test_catalogs.py:170*
- [X] R-multiple analytics must prefer explicit initial-risk fields when available and fall back only to documented analytics proxies when risk fields are absent. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Official analytics tool responses must include metadata, side-effect flags, risk flags, execution timing, and structured errors. *tests/unit/app/services/analytics/test_catalogs.py:170*
- [X] Metric definitions must document default configuration sources for annualization, risk-free rate, breakeven tolerance, minimum sample size, bootstrap count limits, dashboard limits, FX stale-rate limits, and confidence/alpha levels when those defaults are approved. *app/services/analytics/models.py:201*
- [X] Strategy-quality scorecards must not make final live approval, promotion, prop-firm enforcement, or risk-governor decisions. *tests/unit/app/services/analytics/test_scorecard.py:69*
- [X] Strategy-quality outputs must not claim final approval, promotion, live-readiness, prop-firm compliance enforcement, risk-limit approval, or portfolio allocation authority. *tests/unit/app/services/analytics/test_scorecard.py:69*
- [X] `risk_adjusted_efficiency` shall calculate return relative to total defined initial risk. *app/services/analytics/risk.py:41*
- [X] `profit_per_pip_risk` shall calculate reward-to-risk based on profit pips relative to MAE pips. *app/services/analytics/risk.py:47*
- [X] `upside_potential_ratio` shall calculate upside potential relative to downside risk. *app/services/analytics/risk.py:77*
- [X] `volatility` shall calculate return standard deviation as a positive percentage. *app/services/analytics/risk.py:56*
- [X] `annualized_volatility` shall calculate annualized volatility as a positive percentage. *app/services/analytics/risk.py:64*
- [X] `downside_volatility` shall calculate downside deviation as a positive percentage. *app/services/analytics/risk.py:68*
- [X] `value_at_risk` shall calculate value-at-risk as a positive percentage. *app/services/analytics/risk.py:88*
- [X] `conditional_var` shall calculate conditional value-at-risk as a positive percentage. *app/services/analytics/risk.py:98*
- [X] `expected_shortfall` shall calculate expected shortfall. *app/services/analytics/risk.py:109*
- [X] `max_nominal_exposure_simple` shall calculate maximum nominal exposure held at one time. *app/services/analytics/risk.py:113*
- [X] `max_gross_exposure` shall calculate maximum gross nominal exposure. *app/services/analytics/risk.py:123*
- [X] `exposure_time_ratio` shall calculate percentage of total period spent in market. *app/services/analytics/risk.py:127*
- [X] `time_weighted_avg_exposure` shall calculate time-weighted average notional exposure. *app/services/analytics/risk.py:135*
- [X] `portfolio_margin_utilization_curve` shall generate portfolio margin-utilization curve over time. *app/services/analytics/risk.py:155*
- [X] `compounding_risk_of_ruin` shall estimate ruin probability with dynamic compounding risk. *app/services/analytics/risk.py:173*
- [X] `historical_var_by_symbol` shall calculate historical value-at-risk by symbol. *app/services/analytics/risk.py:182*
- [X] `portfolio_var_from_covariance` shall calculate portfolio value-at-risk from covariance and weights. *app/services/analytics/risk.py:197*
- [X] `calculate_risk_metrics` shall calculate aggregate risk metrics such as VaR, CVaR, and volatility. *app/services/analytics/risk.py:212*
- [X] Tool metadata must consistently identify the category as `analytics` and risk level as `low`. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Analytics input and output contracts must remain aligned with Simulation, Optimization, Risk, Portfolio, Trading receipt, and UI/API contracts. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] No file-specific non-functional requirements defined. *app/services/analytics/README.md:9*
- [X] No file-specific testing requirements defined. *app/services/analytics/README.md:9*
- [X] Redaction rules must apply to sensitive keys and sensitive-looking values in inputs, warnings, errors, logs, metadata, and diagnostic details. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Low-level metric helpers such as individual average, skewness, kurtosis, tail-ratio, tracking-error, ulcer-index, omega-ratio, payoff-ratio, and date helper functions must remain internal/support-only unless explicitly promoted by the Official Analytics Tool Catalog. *app/services/analytics/models.py:201*
- [X] Warnings and quality flags must include code, severity, affected section, source context, and enough bounded detail for downstream review. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Warning and quality-flag catalogs must define code, severity, affected section, source-backed status, whether the flag blocks promotion, bounded detail rules, and linked test fixtures. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Explainability outputs must distinguish explained PnL, unexplained PnL, explained variance percentage, sample count, and driver stability when those inputs are supplied. *tests/unit/app/services/analytics/test_metrics.py:394*

#### `app/services/analytics/ratios.py`

Functions/classes:

- `calculate_ratio_metrics`

Requirements:

- [X] `benchmark_information_ratio` shall expose benchmark information ratio without colliding with the ratios module export. *app/services/analytics/__init__.py:341*
- [X] `up_down_capture` shall calculate up-capture and down-capture ratios. *app/services/analytics/benchmark.py:161*
- [X] `metrics_win_rate_fraction` shall expose metrics-module win-rate fraction behavior without colliding with ratios exports. *app/services/analytics/__init__.py:335*
- [X] `metrics_expectancy` shall expose metrics-module expectancy behavior without colliding with ratios exports. *app/services/analytics/__init__.py:336*
- [X] `metrics_expectancy_r` shall expose metrics-module R-expectancy behavior without colliding with ratios exports. *app/services/analytics/__init__.py:337*
- [X] `ratios_win_rate_fraction` shall expose ratios-module win-rate fraction behavior without colliding with metrics exports. *app/services/analytics/__init__.py:334*
- [X] `sharpe_ratio` shall calculate excess return per unit of volatility. *app/services/analytics/ratios.py:41*
- [X] `annualized_sharpe_ratio` shall calculate annualized Sharpe ratio from monthly inputs. *app/services/analytics/ratios.py:54*
- [X] `sortino_ratio` shall calculate excess return per unit of downside volatility. *app/services/analytics/ratios.py:62*
- [X] `ratios_information_ratio` shall expose ratios-module information ratio without colliding with benchmark exports. *app/services/analytics/__init__.py:340*
- [X] `omega_ratio` shall calculate probability-weighted gains relative to losses. *app/services/analytics/ratios.py:75*
- [X] `gain_to_pain_ratio` shall calculate gains relative to absolute negative returns. *app/services/analytics/ratios.py:83*
- [X] `kappa_ratio` shall calculate generalized Sortino-style Kappa ratio. *app/services/analytics/ratios.py:91*
- [X] `profit_factor` shall calculate gross profit relative to gross loss. *app/services/analytics/ratios.py:101*
- [X] `payoff_ratio` shall calculate average win relative to average loss. *app/services/analytics/ratios.py:111*
- [X] `edge_ratio` shall calculate payoff edge adjusted by win rate. *app/services/analytics/ratios.py:117*
- [X] `profit_to_mae_ratio` shall calculate profit capture relative to adverse excursion. *app/services/analytics/ratios.py:126*
- [X] `mfe_to_mae_ratio` shall calculate favorable excursion relative to adverse excursion. *app/services/analytics/ratios.py:132*
- [X] `expectancy_over_std` shall calculate expectancy stability relative to standard deviation. *app/services/analytics/ratios.py:140*
- [X] `net_profit_as_percent_of_largest_loss` shall calculate net profit as a percentage of largest loss. *app/services/analytics/ratios.py:158*
- [X] `select_net_profit_as_percent_of_largest_loss` shall calculate selected net profit as a percentage of largest loss. *app/services/analytics/ratios.py:166*
- [X] `adjusted_net_profit_as_percent_of_largest_loss` shall calculate adjusted net profit as a percentage of largest loss. *app/services/analytics/ratios.py:172*
- [X] `adjusted_profit_factor` shall calculate adjusted gross profit relative to adjusted gross loss. *app/services/analytics/ratios.py:178*
- [X] `select_profit_factor` shall calculate selected gross profit relative to selected gross loss. *app/services/analytics/ratios.py:188*
- [X] `ratios_expectancy` shall expose ratios-module expectancy behavior without colliding with metrics exports. *app/services/analytics/__init__.py:338*
- [X] `ratios_expectancy_r` shall expose ratios-module R-expectancy behavior without colliding with metrics exports. *app/services/analytics/__init__.py:339*
- [X] `calculate_ratio_metrics` shall calculate aggregate ratio metrics from return values. *app/services/analytics/ratios.py:198*
- [X] Architectural Mandate: derived ratios may use deterministic `float64` arithmetic only where exact decimal arithmetic is not appropriate, with documented tolerance stored in configuration, tests, and report metadata. *tests/unit/app/services/analytics/test_report.py:47*
- [X] No file-specific non-functional requirements defined. *app/services/analytics/README.md:9*
- [X] No file-specific testing requirements defined. *app/services/analytics/README.md:9*
- [X] The module must degrade safely when optional acceleration libraries are unavailable. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Calculations over large datasets must use vectorized operations where feasible and must degrade to bounded chunked processing with warnings when vectorization or memory limits are exceeded. *tests/unit/app/services/analytics/test_catalogs.py:188*
- [X] Shared caches, if implemented, must be concurrency-safe or read-through and keyed by input hash, configuration hash, and analytics engine version. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Long-series cumulative operations must use numerically stable methods where feasible and must document any approximation or chunking behavior. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] Duplicate timestamps must be rejected or resolved deterministically according to configuration and recorded in diagnostics. *tests/unit/app/services/analytics/test_catalogs.py:122*
- [X] Invalid or missing required inputs must fail with a structured error envelope, not an uncaught exception. Custom analytics exceptions and error codes must inherit and reuse exceptions from `app.utils.errors` to prevent duplicate declaration. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] `time_in_market_duration` shall calculate total duration where at least one position was open. *app/services/analytics/trade.py:618*
- [X] `trading_period_duration` shall calculate total duration of the trading period. *app/services/analytics/trade.py:956*
- [X] `deflated_sharpe_ratio` shall adjust Sharpe ratio diagnostics for multiple testing and non-normality. *app/services/analytics/distributions.py:302*

#### `app/services/analytics/distributions.py`

Functions/classes:

- `calculate_distribution_metrics`

Requirements:

- [X] `return_distribution` shall calculate a statistical summary of returns. *app/services/analytics/distributions.py:243*
- [X] `r_multiple_distribution` shall calculate a statistical summary of R-multiple values. *app/services/analytics/distributions.py:247*
- [X] `distributions_r_multiple_distribution` shall expose distribution-module R-multiple distribution behavior without colliding with metrics exports. *app/services/analytics/__init__.py:342*
- [X] `percentile_summary` shall return selected percentile values. *app/services/analytics/distributions.py:81*
- [X] `upside_downside_summary` shall summarize positive and negative outcome distributions. *app/services/analytics/distributions.py:95*
- [X] `skewness` shall calculate return or value skewness. *app/services/analytics/distributions.py:41*
- [X] `kurtosis` shall calculate excess kurtosis. *app/services/analytics/distributions.py:54*
- [X] `higher_moments` shall calculate detailed skewness and kurtosis context. *app/services/analytics/distributions.py:67*
- [X] `fat_tail_score` shall estimate tail heaviness relative to normal behavior. *app/services/analytics/distributions.py:108*
- [X] `tail_ratio` shall calculate the ratio between upper-tail and lower-tail percentile magnitudes. *app/services/analytics/distributions.py:113*
- [X] `jarque_bera_test` shall run a Jarque-Bera normality diagnostic. *app/services/analytics/distributions.py:124*
- [X] `shapiro_wilk_test` shall run a Shapiro-Wilk normality diagnostic. *app/services/analytics/distributions.py:136*
- [X] `qq_plot_data` shall generate theoretical and actual quantile data for Q-Q plotting. *app/services/analytics/distributions.py:147*
- [X] `fit_distribution` shall fit a theoretical distribution and return fit parameters. *app/services/analytics/distributions.py:170*
- [X] `distribution_fit_quality` shall return fit-quality diagnostics such as likelihood and information criteria. *app/services/analytics/distributions.py:178*
- [X] `histogram_data` shall generate histogram bin data for plotting. *app/services/analytics/distributions.py:197*
- [X] `detect_outliers` shall identify outliers with the requested method and threshold. *app/services/analytics/distributions.py:216*
- [X] `outlier_ratio` shall calculate the percentage of data points flagged as outliers. *app/services/analytics/distributions.py:235*
- [X] `calculate_distribution_metrics` shall calculate aggregate distribution metrics from numeric values. *app/services/analytics/distributions.py:440*
- [X] No file-specific non-functional requirements defined. *app/services/analytics/README.md:9*
- [X] No file-specific testing requirements defined. *app/services/analytics/README.md:9*
- [X] Analytics behavior must be deterministic for the same inputs except where Monte Carlo, bootstrap, or permutation features intentionally use randomness; those features should support explicit seeds. *tests/unit/app/services/analytics/test_catalogs.py:122*
- [X] Statistical validation tools must expose deterministic options such as seeds, bootstrap/permutation counts, block sizes, confidence levels, alpha levels, and sample-size thresholds where supported. *tests/unit/app/services/analytics/test_catalogs.py:122*
- [X] `metrics_r_multiple_distribution` shall calculate R-multiple distribution statistics. *app/services/analytics/__init__.py:343*
- [X] `permutation_test` shall run significance testing through random reshuffling or sign-flipping. *app/services/analytics/distributions.py:279*
- [X] `bootstrap_confidence_intervals` shall estimate metric uncertainty with non-parametric bootstrap. *app/services/analytics/distributions.py:254*
- [X] `bootstrap_probability_above_threshold` shall estimate probability that a bootstrapped metric exceeds a threshold. *app/services/analytics/distributions.py:400*
- [X] `permutation_test_backtest` shall run permutation testing against a backtest result object. *app/services/analytics/distributions.py:353*
- [X] `bootstrap_confidence_intervals_backtest` shall estimate bootstrap confidence intervals from a backtest result object. *app/services/analytics/distributions.py:359*

#### `app/services/analytics/benchmark.py`

Functions/classes:

- `calculate_benchmark_metrics`

Requirements:

- [X] Benchmark analytics must align strategy and benchmark return streams before comparison and must handle missing or non-overlapping periods safely. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Benchmark metrics must only be calculated after deterministic alignment of strategy and benchmark series. *tests/unit/app/services/analytics/test_catalogs.py:122*
- [X] Strategy and benchmark timestamps must be normalized to UTC before alignment. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Benchmark data must be restricted to the strategy analytics window unless explicit lookback is configured and recorded. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Missing benchmark currency metadata must emit a warning and restrict calculations to currency-neutral metrics unless a validated currency policy exists. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Portfolio analytics must not sum raw PnL across different profit currencies. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] Portfolio, TCA, and base-currency analytics must require validated FX conversion data when source money values are in different currencies. *tests/unit/app/services/analytics/test_report.py:100*
- [X] Missing required FX conversion data must produce blocker-level quality evidence for affected multi-currency portfolio or TCA sections. *tests/unit/app/services/analytics/test_report.py:100*
- [X] Stale FX rates must be identified when FX age limits are configured, and affected converted values must be marked as estimated when stale data is used. *tests/unit/app/services/analytics/test_metrics.py:394*
- [X] All money fields must include explicit currency or inherit a validated account base currency with lineage explaining the inheritance. *tests/unit/app/services/analytics/test_report.py:47*
- [X] `beta` shall calculate the strategy beta coefficient relative to benchmark returns. *app/services/analytics/benchmark.py:64*
- [X] `alpha` shall calculate annualized Jensen-style alpha relative to benchmark returns. *app/services/analytics/benchmark.py:80*
- [X] `r_squared` shall calculate coefficient of determination between strategy and benchmark returns. *app/services/analytics/benchmark.py:101*
- [X] `tracking_error` shall calculate annualized tracking error between strategy and benchmark returns. *app/services/analytics/benchmark.py:119*
- [X] `information_ratio` shall calculate relative Sharpe-style information ratio. *app/services/analytics/benchmark.py:133*
- [X] `batting_average` shall calculate the percentage of periods where the strategy outperformed the benchmark. *app/services/analytics/benchmark.py:150*
- [X] `calculate_benchmark_metrics` shall calculate combined benchmark-relative metrics such as alpha and beta. *app/services/analytics/benchmark.py:205*
- [X] The module must not overstate strategy quality, robustness, or live readiness; report outputs should expose caveats where sample size, overfitting, missing benchmark, or partial data weaken confidence. *tests/unit/app/services/analytics/test_report.py:47*
- [X] All timestamps must be timezone-aware or explicitly normalized to UTC before metric calculation, benchmark alignment, report hashing, or dashboard payload generation. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] ADR Required: `ADR-ANALYTICS-LIMITS` must record exact maximum input sizes, response payload limits, runtime budgets, memory budgets, statistical iteration limits, dashboard point limits, reference hardware, and benchmark method before Builder handoff. *tests/unit/app/services/analytics/test_catalogs.py:188*
- [X] Performance benchmark tests must fail the handoff gate until `ADR-ANALYTICS-LIMITS` supplies exact dataset sizes, hardware profile, benchmark method, runtime thresholds, memory thresholds, and statistical-validation iteration limits. *tests/unit/app/services/analytics/test_catalogs.py:188*
- [X] No file-specific non-functional requirements defined. *app/services/analytics/README.md:9*
- [X] No file-specific testing requirements defined. *app/services/analytics/README.md:9*

#### `app/services/analytics/efficiency.py`

Functions/classes:

- `capital_efficiency`
- `return_per_unit_mae`
- `return_per_unit_mfe`
- `exposure_efficiency`

Requirements:

- [X] `capital_efficiency` shall calculate return per unit of nominal capital deployed. *app/services/analytics/efficiency.py:17*
- [X] `return_per_unit_mae` shall calculate total return relative to adverse excursion experienced. *app/services/analytics/efficiency.py:23*
- [X] `return_per_calendar_day` shall calculate net profit per calendar day in the test period. *app/services/analytics/efficiency.py:32*
- [X] `exit_efficiency` shall calculate combined win-capture and loss-containment efficiency. *app/services/analytics/efficiency.py:54*
- [X] `loss_containment_efficiency` shall calculate how well realized losses stayed above their adverse excursion. *app/services/analytics/efficiency.py:38*
- [X] No file-specific non-functional requirements defined. *app/services/analytics/README.md:9*
- [X] No file-specific testing requirements defined. *app/services/analytics/README.md:9*
- [X] `median_mae_mfe` shall calculate median MAE and MFE values. *app/services/analytics/trade.py:677*
- [X] `get_mae_mfe_r` shall calculate MAE and MFE normalized to R-space. *app/services/analytics/trade.py:685*
- [X] `median_mae_r` shall calculate median MAE in R-multiple terms. *app/services/analytics/trade.py:785*
- [X] `median_mfe_r` shall calculate median MFE in R-multiple terms. *app/services/analytics/trade.py:797*

#### `app/services/analytics/scorecard.py`

Functions/classes:

- `MetricDefinition`
- `ScorecardRule`
- `ScorecardResult`
- `evaluate_scorecard`
- `validate_metric_catalog`

Requirements:

- [X] No metric may be referenced in an official tool schema, report schema, dashboard payload, scorecard rule, warning rule, or quality-flag rule until its Metric Definition Catalog entry is approved. *app/services/analytics/models.py:201*
- [X] Metric definitions must document whether outputs are calculated facts, diagnostic estimates, warning evidence, scorecard inputs, or non-binding review context. *app/services/analytics/models.py:201*
- [X] `evaluate_strategy_quality` shall evaluate a supplied analytics report and return strategy-quality decision context, score, strengths, warnings, and recommended action. *app/services/analytics/scorecard.py:84*
- [X] No file-specific non-functional requirements defined. *app/services/analytics/README.md:9*
- [X] No file-specific testing requirements defined. *app/services/analytics/README.md:9*
- [X] Public registry changes must remain auditable through tests and catalog updates. *app/services/analytics/models.py:281*
- [X] The module must separate calculated facts from warnings, caveats, decisions, and recommended actions. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Official agent/API-facing analytics tools must be high-level, documented, typed, schema-compliant, traceable, and listed in the Official Analytics Tool Catalog. *app/services/analytics/models.py:281*
- [X] Every official analytics tool must have a documented input schema and output schema, including required fields, optional fields, default values, accepted aliases, units, validation errors, warning codes, and JSON-safe serialization behavior. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Low-level metric kernels must not be exposed as official agent/API tools unless explicitly approved in the Official Analytics Tool Catalog. *app/services/analytics/models.py:201*
- [X] Official analytics tools must log call start, validation failure, successful completion, controlled warning, and execution failure without logging secrets or full raw private payloads. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Warning severity must support at least informational, warning, major, critical, and blocker-level meanings. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Quality flags must separate raw metrics, normalized score inputs, penalty flags, hard blockers, recommendation evidence, and final governance decisions. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Strategy-quality and prop-firm outputs must be labeled as non-binding analytics evidence or decision context only. *tests/unit/app/services/analytics/test_scorecard.py:69*
- [X] `sqn` shall calculate system quality number. *app/services/analytics/trade.py:866*
- [X] `sample_size_warning` shall assess metric reliability based on sample size. *app/services/analytics/distributions.py:368*
- [X] Documentation must include the Official Analytics Tool Catalog. *app/services/analytics/models.py:281*
- [X] Documentation must include the warning-code and quality-flag catalog. *app/services/analytics/README.md:9*

#### `app/services/analytics/report.py`

Functions/classes:

- `AnalyticsReport`
- `PortfolioAnalyticsReport`

Requirements:

- [X] Overview/report tools must combine lower-level analytics into grouped payloads that remain serializable for API and dashboard consumers. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] The module must generate a complete, versioned `AnalyticsReport` from a valid backtest, optimization candidate, out-of-sample, walk-forward, paper, live, or normalized trading result when required inputs are available. *app/services/analytics/report.py:40*
- [X] Report building must validate inputs, normalize result data, run required metric groups, run optional metric groups, collect warnings and quality flags, build dashboard payloads, validate output, compute hashes, and return a standard tool response. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] Missing optional inputs must produce warnings or skipped-section metadata rather than fabricated metric values. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Critical metric group failures must return an error unless diagnostic partial mode is explicitly configured. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Partial reports must include `report_status = "partial"`, affected sections, skipped/failed/degraded section metadata, warnings, quality flags, lineage, and JSON-safe values. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Report generation must define section criticality as required, optional, diagnostic-only, disabled, skipped, failed, or degraded. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Required-section failure must return an error unless diagnostic partial mode is explicitly enabled. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Optional-section failure must produce skipped or failed section metadata without fabricating the missing section. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Partial reports must be marked non-promotable and must not be consumed as final approval evidence. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] Report metadata must preserve `request_id`, optional `workflow_id`, run IDs, strategy identifiers, strategy version, schema version, analytics engine version, annualization settings, optional-section status, source context, and creation time. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Hashing rules must exclude non-deterministic fields such as generation timestamps unless explicitly documented. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Hashes must be computed from canonical JSON serialization with deterministic key ordering, documented numeric normalization, and documented exclusion rules for non-deterministic fields. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Analytics must propagate upstream data-quality and bias evidence into report warnings and quality flags. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Dashboard payload builders must consume validated `AnalyticsReport` sections and must not recompute core metrics. *app/services/analytics/report.py:40*
- [X] `format_summary_as_rows` shall format raw summary data into report/display rows. *app/services/analytics/report.py:365*
- [X] `build_backtest_report` shall build a structured backtest analytics report payload. *app/services/analytics/report.py:369*
- [X] `print_statistical_validation_report` shall package a comprehensive statistical validation report. *app/services/analytics/report.py:378*
- [X] Report generation must be idempotent for the same input, configuration, and analytics engine version. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Reports must include reproducibility metadata, input hashes, configuration hashes, report hashes, and lineage. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Annualized metrics must use explicit annualization settings stored in configuration and report metadata; the module must not silently guess annualization when frequency cannot be inferred safely. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Cache hits, misses, evictions, and concurrent duplicate requests must not change metric values, warning order, report hashes, dashboard payloads, or quality-flag outcomes. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] Sequential and parallel execution over the same report inputs must not change metric values, warning order, report hashes, dashboard payloads, or quality-flag outcomes. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] Warning and quality-flag ordering must be deterministic where output hashes, dashboard payloads, report comparison, or tests depend on order. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] Architectural Mandate: canonical monetary sums, cost aggregation, and base-currency aggregation must use `Decimal` normalization for hashing and report contracts. *tests/unit/app/services/analytics/test_report.py:100*
- [X] Report metadata must identify the monetary precision mode used, such as `decimal` or `float64_with_tolerance`. *tests/unit/app/services/analytics/test_report.py:47*
- [X] The module must define concrete runtime limits for bootstrap, permutation, Monte Carlo, distribution fitting, dashboard downsampling, and report generation before production handoff. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] `build_analytics_report` latency, statistical-validation runtime, throughput, memory, and payload-size targets must be measurable before Builder handoff. *app/services/analytics/report.py:92*
- [X] Documentation must include report section criticality and partial-report behavior. *app/services/analytics/README.md:9*
- [X] Documentation must include schema compatibility policy for accepted, deprecated, legacy-adapted, and unsupported report/result versions. *app/services/analytics/models.py:12*
- [X] Documentation must include partial-report examples showing skipped, failed, and degraded section metadata. *app/services/analytics/README.md:9*
- [X] `TradingResult`, `AnalyticsReport`, `PortfolioAnalyticsReport`, dashboard payloads, warning objects, quality flags, and error envelopes have versioned schemas. *app/services/analytics/adapters.py:13*
- [X] Report section criticality and partial-report non-promotable behavior are approved. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] Requirement-to-test traceability matrix maps every official tool, report contract, adapter mapping, warning/quality flag, and failure envelope to tests. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Usage examples cover success, validation failure, partial report, dashboard truncation, and request-ID traceability. *app/services/analytics/README.md:9*
- [X] No file-specific non-functional requirements defined. *app/services/analytics/README.md:9*
- [X] Final analytics responses must not contain `NaN`, `inf`, `-inf`, invalid JSON values, pandas objects, NumPy objects, raw dataframes, raw series, or other unserializable values. *tests/unit/app/services/analytics/test_report.py:47*

#### `app/services/analytics/dashboard.py`

Functions/classes:

- `build_overview_payload`

Requirements:

- [X] Dashboard payloads must include chart/table data, finite numeric values, ISO-8601 timestamps, units, warnings, and metadata sufficient for UI/API consumers. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] If a required source section is missing, failed, skipped, or degraded, the dashboard payload must include section-status metadata and warnings rather than recomputing or fabricating chart/table values. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] Dashboard/UI consumers must not need to recalculate core metrics. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] Dashboard payload support must be classified by chart/table type as required, optional, or future before Builder implementation. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] Truncated payload metadata must include whether truncation occurred, original point count, returned point count, truncation method or algorithm, and truncation reason. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] `build_overview_payload` shall build the API/dashboard analytics overview payload. *app/services/analytics/dashboard.py:72*
- [X] Result payloads must be JSON-safe or convertible to JSON-safe structures for API and dashboard consumers. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] Dashboard payloads must obey configured size limits and deterministic truncation policies when limits are defined. *tests/unit/app/services/analytics/test_metrics.py:896*
- [X] The module must define concrete maximum response payload size and deterministic truncation behavior for dashboard and API payloads before production handoff. *tests/unit/app/services/analytics/test_catalogs.py:188*
- [X] Documentation must include required, optional, and future dashboard payload classes. *app/services/analytics/README.md:9*
- [X] Documentation must include dashboard truncation examples showing truncation metadata. *app/services/analytics/README.md:9*
- [X] Concrete input-size, runtime, memory, response-size, dashboard truncation, statistical iteration, and performance targets are approved with a hardware/profile context. *tests/unit/app/services/analytics/test_catalogs.py:188*
- [X] No file-specific non-functional requirements defined. *app/services/analytics/README.md:9*
- [X] No file-specific testing requirements defined. *app/services/analytics/README.md:9*


### Hardening Amendments

#### Canonical analytics inputs

Requirements:

- [X] Adopt Phase 1.5 contracts for TradeResult, ExecutionReport, Fill, PortfolioSnapshot, BacktestResult, RiskDecision, and AuditEvent analytics inputs. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Define analytics adapters that consume simulation journals and live trade journals through the same canonical event/result model. *tests/unit/app/services/analytics/test_metrics.py:314*
- [X] Prohibit Analytics from reading raw broker SDK payloads, UI DTOs, or conversation memory as primary metric sources. *tests/unit/app/services/analytics/test_catalogs.py:188*
- [X] Define metric provenance using run ID, strategy ID, dataset hash, cost model, fill model, risk policy version, and journal reference. *tests/unit/app/services/analytics/test_report.py:47*
- [X] Ensure Analytics can run before UI/API exists and can be consumed by UI/API later without changing metric definitions. *app/services/analytics/models.py:201*

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

- Done criterion: All 465 checkbox tasks are implemented or explicitly deferred with a documented reason.
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

- [X] Analytics output must not include secrets, credentials, broker tokens, authorization headers, or private raw provider payloads. *tests/unit/app/services/analytics/test_catalogs.py:170*
- [X] Analytics outputs used by UI/API must remain backward-compatible or be versioned when payload structure changes. *app/services/analytics/models.py:12*
