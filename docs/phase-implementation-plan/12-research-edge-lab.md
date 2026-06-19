## Phase 12 Research Edge Lab

### Goal

Implement the Research Edge Lab requirements under `app/services/research/` while preserving the phase module boundaries and governance rules.

Task inventory: 290 checkbox tasks (290 checked, 0 unchecked).

### Dependency Files and Functionality

Required files:

```text

app/utils/__init__.py

app/utils/dataframe_tools.py

app/services/data/__init__.py

api/main.py

```

Required functionality:

- Data gateway retrieves cleaned historical bars for studies.
- Dataframe alignment and comparison operations execute.
- Gateway routes support API requests for feature extraction.

### Files to Create

```text

app/services/research/

app/services/research/__init__.py

app/utils/settings.py

app/services/research/data.py

app/services/research/features.py

app/services/research/leakage.py

app/services/research/metrics.py

app/services/research/studies/__init__.py

app/services/research/studies/eds.py

app/services/research/studies/null_models.py

app/services/research/studies/structure.py

app/services/research/studies/unsupervised.py

app/services/research/helpers.py

app/services/research/reporting.py

app/utils/errors.py

app/utils/errors.py

```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `app/services/research/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [x] Importing `app.services.research` shall not perform network calls, disk writes, provider initialization, credential reads, live trading state access, or heavy model execution.
- [x] No file-specific non-functional requirements defined.
- [x] No file-specific testing requirements defined.

#### `app/utils/settings.py`

Functions/classes:

- `CleaningConfig`

Requirements:

- [x] `create_config` shall create an Edge Lab configuration object with common defaults for research workflows.
- [x] `DataConfig` shall describe source, symbol, timeframe, and date-range data inputs for research workflows.
- [x] `SessionConfig` shall describe trading-session windows and related session settings.
- [x] `BootstrapConfig` shall describe bootstrap resampling settings.
- [x] `PermutationConfig` shall describe permutation-test settings.
- [x] `NullModelsConfig` shall describe null-model settings and acceptance criteria.
- [x] `MeanReversionConfig` shall describe mean-reversion edge-discovery settings.
- [x] `TrendPersistenceConfig` shall describe trend-persistence edge-discovery settings.
- [x] `MarketStructureConfig` shall describe market-structure research settings.
- [x] `SessionEdgeConfig` shall describe session-edge research settings.
- [x] `EdgeLabConfig` shall aggregate the module's research configuration sections into one workflow-level configuration.
- [x] `TradeSample` shall represent a normalized trade sample for edge-result reporting.
- [x] `EdgeStats` shall represent summary statistics for an edge result.
- [x] `EdgeResult` shall represent a complete edge-study result suitable for summaries and reports.
- [x] `research_modeling_module` shall return the research modeling service module through the shared lazy-resolution utility.
- [x] Each public export in `app.services.research.__all__` shall have a documented contract specifying API status, input types, required fields, output type, error behavior, side effects, determinism guarantees, network/heavy dependency status, and stability level.
- [x] Core model contracts shall define required fields, optional fields, schema versions, validation behavior, serialization behavior, and example payloads for `PreparedDataset`, `DataQualityReportModel`, `EdgeResult`, `CoreMetricProfile`, `MarketStructureProfile`, `UnsupervisedResearchResult`, `UnsupervisedInsightReport`, and report payloads.
- [x] The module shall define a canonical research error taxonomy covering validation errors, configuration errors, insufficient-data errors, statistical-invalidity errors, external-provider errors, serialization errors, resource-limit errors, and permission errors.
- [x] Public library functions shall either raise typed research exceptions or return structured result objects with warnings according to their documented contract; standard research tools shall return errors through the standard HaruQuant envelope.
- [x] Each public callable contract shall explicitly choose one failure pattern: typed exception, structured result with warnings/errors, or standard research envelope. Mixed behavior is not allowed unless every branch is documented.
- [x] The standard research envelope shall define at least `status`, `data`, `errors`, `warnings`, `audit`, `side_effect`, `approval_required`, `dry_run`, `environment`, `risk_level`, and `timing`.
- [x] Standard research envelope `errors` and `warnings` shall use machine-readable codes, human-readable messages, optional field paths, severity, retryability, and bounded details.
- [x] Standard research envelope `audit` shall include request ID, correlation ID where available, tool/capability name, schema version, source references where applicable, created-at timestamp, and redaction/provenance metadata.
- [x] Standard research envelope schema must be frozen for the approved first implementation slice before any network-backed, standard helper, evidence-pack, or agent-facing research helper is implemented.
- [x] Each public callable in the approved implementation slice shall have a behavior/error table that maps invalid input, insufficient data, unsupported config, provider unavailable, rate limit, serialization failure, resource limit, and permission failure to one exact typed exception, structured result warning/error, or standard envelope error.
- [x] Provisional insufficient-sample behavior: research calculations should fail with a typed validation error or standard-envelope error code such as `ERR_INSUFFICIENT_SAMPLES` when the approved minimum sample size is not met; final code names and thresholds remain pending owner/architect approval.
- [x] The first implementation slice shall be explicitly approved before Builder handoff; proposed initial slice is data preparation plus core metrics unless the owner approves a different slice.
- [x] A contract-first checklist shall block coding until every public callable in the approved slice has input/output types, error model, determinism guarantee, side-effect classification, envelope/result shape, examples, and mapped tests.
- [x] The module glossary shall define `Edge Lab`, `null baseline`, `profile snapshot`, `research envelope`, `advisory evidence`, `leakage report`, and `research artifact`.
- [x] `CleaningConfig` shall describe data-cleaning behavior for timezone normalization, missing bars, non-trading periods, and spread anomalies.
- [x] `CleaningConfig` shall define `missing_bar_strategy` with approved values such as `drop`, `forward_fill`, `interpolate`, and `none`, with deterministic behavior documented for each value.
- [x] `CleaningConfig.missing_bar_strategy` default must be owner-approved before implementation. No Builder may infer a default or silently fill/drop bars without an approved default and explicit quality-report action.
- [x] `CleaningConfig` shall define `non_trading_period_strategy` with approved values and shall document weekend, holiday, synthetic-bar, and provider-gap behavior.
- [x] `clean_dataset` shall normalize timestamps to the configured timezone, resolve duplicate or non-monotonic timestamps according to `CleaningConfig`, apply configured missing-bar and non-trading-period handling, detect spread anomalies, and return both cleaned data and a `DataQualityReportModel` containing machine-readable cleaning actions and unresolved warnings.
- [x] `EnrichmentConfig` shall describe enrichment settings for pip metadata, bar geometry, returns, labels, calendar fields, and sessions.
- [x] `prepare_research_dataset` shall accept either in-memory raw OHLCV/OHLCVS data or a configured research data source, apply cleaning, validation, and enrichment in deterministic order, and return a `PreparedDataset` containing prepared data, metadata, and a quality report. It shall fail with a typed validation or configuration error when fatal issues prevent safe research use.
- [x] `sma` shall compute simple moving averages over a configured window.
- [x] `ema` shall compute exponential moving averages over a configured span.
- [x] `std` shall compute rolling standard deviation over a configured window.
- [x] `validate_no_lookahead_features` shall inspect declared feature metadata, column naming conventions, target/horizon columns, and configured allowed-forward columns, then return a structured leakage report identifying suspected lookahead fields, severity, evidence, and recommended action without mutating the input frame.
- [x] `compute_session_statistics` shall calculate detailed statistics for a configured trading session.
- [x] `run_eds_session` shall run session-edge discovery across configured session studies.
- [x] Edge-discovery results shall include sample size, evaluated rule/config, source dataset identity, split identifiers, uncertainty metadata, warnings, and an advisory-only disclaimer.
- [x] `exceeds_null_threshold` shall determine whether an observed value exceeds a configured null-distribution threshold.
- [x] Bootstrap, permutation, and null-generation functions shall accept an explicit `seed` parameter or source one from a documented configuration object; returned results shall record the effective seed.
- [x] `build_market_structure_research_profile` shall build a `MarketStructureProfile` plus configured research-only validation layers, including calibration evidence, stability summary, robustness summary, warnings, runtime metadata, and quality-adjusted confidence fields.
- [x] `UnsupervisedResearchConfig` shall describe unsupervised research settings.
- [x] `UnsupervisedResearchConfig` shall include a `seed` field used by non-deterministic algorithms.
- [x] `cluster_feature_space` shall consume `UnsupervisedResearchConfig.seed` or an explicit seed parameter so K-Means output is reproducible for fixed inputs and dependency versions.
- [x] `session_hours_payload` shall return a machine-readable payload describing configured session hours.
- [x] `fetch_forexfactory_news` shall retrieve ForexFactory news data through an isolated provider adapter using configured timeout, retry, rate-limit, cache, and offline-test behavior, then return a standard research envelope containing status, normalized data, provider metadata, source timestamp, warnings, errors, and audit metadata.
- [x] `fetch_forexfactory_calendar` shall retrieve ForexFactory economic calendar data through an isolated provider adapter using configured timeout, retry, rate-limit, cache, stale-data, and offline-test behavior, then return it through the standard research envelope.
- [x] `fetch_forexfactory_sentiment` shall retrieve ForexFactory sentiment data through an isolated provider adapter using configured timeout, retry, rate-limit, cache, stale-data, and offline-test behavior, then return it through the standard research envelope.
- [x] `fetch_forexfactory_instrument_page` shall retrieve a symbol-specific ForexFactory page through an isolated provider adapter using configured timeout, retry, rate-limit, cache, stale-data, and offline-test behavior, then return it through the standard research envelope.
- [x] ForexFactory and other external-feed helpers shall be optional-provider capabilities. Missing provider adapters shall return a deterministic provider-unavailable envelope or documented typed configuration error without breaking import or unrelated research workflows.
- [x] Persisted research artifacts shall include artifact schema version, module version, config hash, dataset identity or data hash, random seed, generated-at timestamp, timezone, source references, and dependency/version metadata required to reproduce the result.
- [x] Persisted research artifacts shall include SHA-256 hashes of the input dataset identity or canonical data snapshot and the effective configuration used to generate the artifact.
- [x] Network-backed research helpers shall enforce configured timeout, retry, rate-limit, cache, stale-data, and provider-layout-change behavior and shall return partial or failed results only through the standard research envelope with warnings and audit metadata.
- [x] Seeded research workflows shall produce equivalent outputs for fixed input data, configuration, random seed, dependency versions, and artifact schema version.
- [x] Report and artifact serialization shall prevent path traversal, accidental overwrite unless configured, and leakage of masked fields.
- [x] Long-running workflows shall expose duration metadata and shall support configured resource limits or fail with a typed resource-limit error.
- [x] No file-specific non-functional requirements defined.

#### `app/services/research/data.py`

Functions/classes:

- `CanonicalOHLCVSSchema`
- `validate_dataset`
- `OHLCVSchema`
- `LeakageReport`
- `MetricContext`
- `build_core_metric_profile`
- `build_market_structure_profile`
- `run_seasonality`

Requirements:

- [x] `CanonicalOHLCVSSchema` shall define the canonical research dataset schema for OHLCV data with spread support.
- [x] `DatasetIssue` shall represent a detected dataset quality issue.
- [x] `CleaningAction` shall represent a cleaning action applied to research data.
- [x] `DataQualityReportModel` shall summarize validation issues and cleaning actions for a dataset.
- [x] `PreparedDataset` shall carry cleaned, validated, enriched data with its quality report and metadata.
- [x] `enrich_dataset` shall add research features such as pip metadata, bar geometry, return labels, calendar fields, and session fields.
- [x] `validate_dataset` shall validate schema, continuity, OHLC consistency, duplicate timestamps, spread quality, and volume fields while distinguishing fatal validation errors from warnings through machine-readable issue codes.
- [x] `DataSource` shall represent the shared data-source descriptor used by research dataset validation.
- [x] `OHLCVSchema` shall represent the shared OHLCV schema descriptor used by research dataset validation.
- [x] `LeakageReport` shall define `suspected_columns`, `severity`, `evidence`, `recommendation`, `allowed_forward_columns`, `target_column`, and request/source metadata.
- [x] `MetricValue` shall represent one normalized metric value with metadata.
- [x] `MetricContext` shall provide the dataset and metadata needed by metric calculators.
- [x] `CoreMetricProfile` shall represent a normalized profile of core dataset metrics.
- [x] `build_core_metric_profile` shall build a normalized core metric profile from a prepared dataset.
- [x] Metric profile output shall define units, sample size, source dataset identity, warnings, undefined-value behavior, and reproducibility metadata.
- [x] `build_market_structure_profile` shall build a directional market-structure profile from a prepared dataset.
- [x] `build_market_structure_robustness_report` shall report robustness of market-structure behavior across parameter or data variations.
- [x] `ClusterModelResult` shall represent clustering labels and cluster metadata.
- [x] `InvestmentDataSummary` shall represent descriptive statistics for investment data.
- [x] `summarize_investment_data` shall return key descriptive statistics for investment data.
- [x] Unsupervised modeling outputs shall include preprocessing metadata, selected feature columns, dropped columns, scaler behavior, seed, model parameters, and cluster/component diagnostics.
- [x] `tag_sessions` shall tag each market-data row with its trading session.
- [x] `run_seasonality` shall calculate seasonality statistics for the provided dataset and filters.
- [x] External-feed helpers shall handle HTTP 429 responses, including missing or invalid `Retry-After` headers, through deterministic rate-limit errors or warnings with bounded retry metadata.
- [x] `check_data_snooping_risk` shall assess data-snooping risk.
- [x] Report persistence functions shall write to a temporary file and atomically rename where the platform supports it; unsupported atomic behavior shall be disclosed in the result metadata or typed error.
- [x] Research artifacts shall preserve source references, assumptions, warnings, and enough metadata to reproduce the result.
- [x] Data preparation and feature pipelines shall avoid lookahead bias and shall support explicit chronological split validation.
- [x] Statistical results shall expose uncertainty where applicable, including p-values, confidence intervals, null percentiles, or comparable validation metadata.
- [x] Public standard tools shall return the standard HaruQuant envelope containing status, tool metadata, request metadata, data, errors, warnings, and audit metadata.
- [x] The module shall avoid storing real secrets, credentials, private broker data, or unredacted private artifacts.
- [x] Proposed benchmark placeholder: `prepare_research_dataset` should process up to 1,000,000 rows in no more than 30 seconds on approved reference hardware; this remains pending until owner approval.
- [x] No file-specific non-functional requirements defined.

#### `app/services/research/features.py`

Functions/classes:

- `build_market_regime_feature_frame`
- `calculate_regime_features`

Requirements:

- [x] `log_returns` shall compute log returns from close prices.
- [x] `simple_returns` shall compute arithmetic returns from close prices.
- [x] `zscore` shall compute a close-price z-score relative to a moving average and standard deviation.
- [x] `percent_rank` shall compute rolling percentile rank values.
- [x] `atr` shall compute Average True Range.
- [x] `atr_percent` shall compute ATR as a percentage of close price.
- [x] `bollinger_bands` shall compute Bollinger-style upper, middle, and lower bands.
- [x] `bb_width` shall compute Bollinger Band width.
- [x] `bb_percent_b` shall compute Bollinger Band percent-B.
- [x] `rolling_percentile_rank` shall compute rolling percentile rank for a supplied series.
- [x] `rsi` shall compute Relative Strength Index.
- [x] `rate_of_change` shall compute rate of change as a momentum measure.
- [x] `momentum` shall compute simple price-difference momentum.
- [x] `donchian_channel` shall compute Donchian breakout levels.
- [x] `hurst_exponent` shall estimate Hurst exponent for mean-reversion versus trend detection.
- [x] `rolling_hurst` shall compute Hurst exponent over rolling windows.
- [x] `pivot_points` shall compute pivot, support, and resistance levels.
- [x] `adr` shall compute Average Daily Range.
- [x] `forward_returns` shall compute horizon-aligned forward log returns.
- [x] `forward_max_favorable_excursion` shall compute maximum favorable price excursion over a forward horizon.
- [x] `forward_max_adverse_excursion` shall compute maximum adverse price excursion over a forward horizon.
- [x] `detect_volatility_regime` shall classify volatility regime using ATR percentile or equivalent volatility evidence.
- [x] `detect_trend_regime` shall classify trend regime from moving-average relationships.
- [x] `build_market_regime_feature_frame` shall build timestamp-aligned feature rows for PCA and clustering regime research.
- [x] Feature functions shall define warm-up-period behavior, NaN handling, minimum window behavior, numeric precision expectations, and input mutation behavior.
- [x] Forward-looking feature functions shall clearly label forward columns as research-only and shall be detectable by leakage checks.
- [x] `FeatureSetFrame` shall represent the feature frame used by unsupervised modeling.
- [x] `calculate_regime_features` shall calculate regime feature rows.
- [x] `detect_market_regime` shall classify market regime from supplied research features.
- [x] No file-specific non-functional requirements defined.
- [x] `active_sessions_for_hour` shall return the active trading sessions for a given hour.
- [x] `session_label_for_hour` shall return the session label for a given hour.

#### `app/services/research/leakage.py`

Functions/classes:

- `LeakageCheckResult`
- `validate_no_lookahead`
- `detect_feature_leakage`
- `mask_forward_columns`

Requirements:

- [x] `TimeSplitResult` shall represent deterministic chronological train, validation, and test partitions.
- [x] `enforce_time_split` shall enforce deterministic chronological train, validation, and test splits.
- [x] `mask_research_artifact` shall remove or redact sensitive fields from research artifacts before persistence or sharing.
- [x] `dump_masked_research_json` shall serialize a masked research artifact to JSON.
- [x] No file-specific non-functional requirements defined.
- [x] No file-specific testing requirements defined.

#### `app/services/research/metrics.py`

Functions/classes:

- `MetricCalculator`
- `MetricRegistry`
- `ReturnsCalculator`
- `RocCalculator`
- `CandlesCalculator`
- `RangesCalculator`
- `VolatilityCalculator`
- `SpreadCalculator`
- `VolumeActivityCalculator`
- `build_default_registry`

Requirements:

- [x] `MetricCalculator` shall define the calculator interface for research core metrics.
- [x] `MetricRegistry` shall register and resolve named metric calculators.
- [x] `ReturnsCalculator` shall calculate return-related core metrics.
- [x] `RocCalculator` shall calculate rate-of-change core metrics.
- [x] `CandlesCalculator` shall calculate candle-geometry core metrics.
- [x] `RangesCalculator` shall calculate range-related core metrics.
- [x] `VolatilityCalculator` shall calculate volatility core metrics.
- [x] `SpreadCalculator` shall calculate spread-quality core metrics.
- [x] `VolumeActivityCalculator` shall calculate volume or activity core metrics.
- [x] `build_default_registry` shall build the default registry of research metric calculators.
- [x] No file-specific non-functional requirements defined.
- [x] No file-specific testing requirements defined.

#### `app/services/research/studies/__init__.py`

Functions/classes:

- `__all__`

Requirements:

- [x] No file-specific functional requirements defined. Foundation properties apply.
- [x] No file-specific non-functional requirements defined.
- [x] No file-specific testing requirements defined.

#### `app/services/research/studies/eds.py`

Functions/classes:

- `run_eds_null_baseline`
- `run_eds_mean_reversion`
- `run_eds_trend_persistence`

Requirements:

- [x] `run_eds_null_baseline` shall establish null-model baselines for edge-discovery studies.
- [x] `run_eds_mean_reversion` shall evaluate a mean-reversion detector based on compression and z-score fade behavior.
- [x] `run_eds_trend_persistence` shall evaluate a trend-persistence detector based on high-ATR breakout follow-through behavior.
- [x] Null-model functions shall define behavior for invalid sample sizes, non-finite statistics, empty distributions, random seeds, replacement/block settings, and multiple-comparison correction applicability.
- [x] Null-model behavior/error tables shall dictate exact outcomes for invalid sample sizes, non-finite statistics, empty distributions, invalid random seeds, invalid replacement/block settings, and inapplicable multiple-comparison corrections; these cases may not be left to Builder interpretation.
- [x] No file-specific non-functional requirements defined.
- [x] No file-specific testing requirements defined.

#### `app/services/research/studies/null_models.py`

Functions/classes:

- `compute_null_percentile`

Requirements:

- [x] `compare_to_null` shall compare observed expectancy or performance against a null distribution.
- [x] `get_acceptance_criteria` shall extract acceptance criteria from a null baseline.
- [x] `block_bootstrap_ci` shall compute a confidence interval using block bootstrap resampling.
- [x] `block_bootstrap_distribution` shall generate a bootstrap distribution for a statistic.
- [x] `permutation_test` shall compute a permutation-test p-value.
- [x] `random_entry_null` shall generate a null distribution from random entries in log-return space.
- [x] `r_space_null` shall generate a null distribution in R-multiple space.
- [x] `session_randomized_null` shall generate a null distribution by shuffling entries within the same session.
- [x] `shuffle_returns_null` shall generate a null distribution by shuffling return blocks.
- [x] `benjamini_hochberg` shall apply Benjamini-Hochberg false-discovery-rate correction.
- [x] `holm_bonferroni` shall apply Holm-Bonferroni multiple-comparison correction.
- [x] `compute_null_percentile` shall compute the percentile of an observed value within a null distribution.
- [x] `null_distribution_stats` shall compute summary statistics for a null distribution.
- [x] No file-specific non-functional requirements defined.
- [x] No file-specific testing requirements defined.
- [x] Multiple-comparison checks shall be available when evaluating many hypotheses or candidates.

#### `app/services/research/studies/structure.py`

Functions/classes:

- `build_calibration_grid`
- `build_metric_calibration_grid`
- `resolve_market_structure_profile`
- `resolve_market_structure_profile_overrides`
- `parse_news_items`
- `generate_research_hypothesis`
- `build_research_evidence_pack`

Requirements:

- [x] `TrendSwingPoint` shall represent a detected swing point used in market-structure analysis.
- [x] `TrendLeg` shall represent a directional leg between swing points.
- [x] `TrendScoreRow` shall represent one market-structure score row.
- [x] `MarketStructureProfile` shall represent a reproducible directional structure profile.
- [x] `MarketStructureCalibrationCandidate` shall represent one calibration candidate for market-structure classification.
- [x] `classify_with_candidate` shall classify market structure using one calibration candidate.
- [x] `build_calibration_grid` shall build candidate parameter grids for market-structure calibration.
- [x] `evaluate_calibration_candidates` shall evaluate market-structure calibration candidates against realized evidence.
- [x] `MarketStructureMetricCalibrationCandidate` shall represent one metric-calibration candidate.
- [x] `build_metric_calibration_grid` shall build candidate grids for market-structure metric calibration.
- [x] `evaluate_metric_calibration_candidates` shall evaluate metric-calibration candidates against target behavior.
- [x] `evaluate_profile_calibration` shall evaluate profile-level calibration behavior.
- [x] `timeframe_bucket` shall map a timeframe into a market-structure profile bucket.
- [x] `symbol_class` shall map a symbol into a market-structure symbol class.
- [x] `resolve_market_structure_profile` shall resolve the applicable market-structure profile for a symbol and timeframe.
- [x] `resolve_market_structure_profile_overrides` shall resolve profile overrides for a symbol, timeframe, or profile class.
- [x] `confidence_bucket` shall convert validation evidence into a confidence bucket.
- [x] `label_realized_market_behavior` shall classify realized future behavior as trend, reversion, or mixed.
- [x] `build_validation_summary` shall summarize market-structure validation evidence.
- [x] `build_market_structure_stability_report` shall report stability of market-structure behavior across samples or windows.
- [x] `build_strategy_fit` shall assess advisory strategy-fit evidence from market-structure research and shall not approve strategy promotion, mutate strategy runtime state, or authorize execution changes.
- [x] Market-structure calibration outputs shall include candidate parameters, ranking criteria, validation window, stability evidence, and warnings for unstable rankings.
- [x] `parse_news_items` shall normalize raw news items into structured research records.
- [x] `generate_research_hypothesis` shall generate a structured research hypothesis from inputs and evidence.
- [x] `build_research_evidence_pack` shall build a structured research evidence pack containing source references, assumptions, warnings, and validation notes.
- [x] The module shall emit structured warnings or logs for validation failures, dropped rows, masking actions, provider failures, statistical insufficiency, and partial report generation.
- [x] No file-specific non-functional requirements defined.
- [x] No file-specific testing requirements defined.
- [x] `ClassificationResult` shall represent the result of classifying a symbol's edge profile.

#### `app/services/research/studies/unsupervised.py`

Functions/classes:

- `UnsupervisedResearchRequest`
- `UnsupervisedResearchResult`
- `run_pca`
- `compute_forward_returns`
- `build_unsupervised_insight_report`

Requirements:

- [x] `UnsupervisedResearchRequest` shall represent one unsupervised research request.
- [x] `UnsupervisedResearchResult` shall represent a complete unsupervised research result.
- [x] `UnsupervisedResearchService` shall orchestrate unsupervised research workflows.
- [x] `PcaModelResult` shall represent PCA scores, loadings, and explained variance.
- [x] `run_pca` shall run PCA on numeric feature columns and return component scores and loadings.
- [x] `cluster_feature_space` shall cluster numeric feature rows using deterministic K-Means labels.
- [x] `attach_cluster_labels` shall attach cluster labels to a feature frame without mutating the input.
- [x] `PcaRiskFactor` shall represent an interpreted PCA loading or risk factor.
- [x] `ClusterOutperformance` shall represent forward-return evidence by cluster.
- [x] `SignalAdaptationResult` shall represent signal-suppression or signal-adaptation recommendations by cluster.
- [x] `UnsupervisedInsightReport` shall represent a complete unsupervised insight report for trading workflows.
- [x] `identify_pca_risk_factors` shall extract the largest PCA loadings as interpretable risk factors.
- [x] `compute_forward_returns` shall compute horizon-aligned forward returns from a price column.
- [x] `analyze_cluster_outperformance` shall score clusters by future returns and assign semantic regime names.
- [x] `adapt_signals_by_cluster` shall produce advisory signal-adaptation recommendations identifying clusters where forward-return evidence is weak; it shall not mutate strategy runtime state, block live entries, or authorize execution changes.
- [x] `build_unsupervised_insight_report` shall build a complete unsupervised insight report for trading workflows.
- [x] No file-specific non-functional requirements defined.

#### `app/services/research/helpers.py`

Functions/classes:

- `parse_calendar_events`
- `parse_sentiment_snapshot`
- `create_news_blackout_windows`
- `calculate_returns`
- `calculate_volatility`
- `calculate_atr`
- `calculate_adr`
- `calculate_spread_statistics`
- `calculate_session_statistics`
- `calculate_seasonality_statistics`
- `calculate_correlation_matrix`
- `check_sample_size`

Requirements:

- [x] `parse_calendar_events` shall normalize economic calendar events.
- [x] `parse_sentiment_snapshot` shall normalize sentiment-positioning snapshots.
- [x] `filter_events_by_symbol` shall filter calendar events by the currencies or instruments relevant to a symbol.
- [x] `classify_news_impact` shall classify the impact level of economic news.
- [x] `create_news_blackout_windows` shall create advisory research blackout-window recommendations around news events and shall not create live no-trade controls or mutate risk/execution policy.
- [x] `calculate_returns` shall calculate price returns for standard research tooling.
- [x] `calculate_volatility` shall calculate rolling annualized volatility.
- [x] `calculate_atr` shall calculate Average True Range.
- [x] `calculate_adr` shall calculate Average Daily Range.
- [x] `calculate_spread_statistics` shall calculate spread distribution statistics.
- [x] `calculate_session_statistics` shall calculate session return statistics.
- [x] `calculate_seasonality_statistics` shall calculate calendar seasonality statistics.
- [x] `calculate_correlation_matrix` shall calculate a correlation matrix for research inputs.
- [x] `detect_trend_strength` shall detect trend strength from moving-average evidence.
- [x] `detect_mean_reversion_conditions` shall detect mean-reversion conditions.
- [x] `detect_breakout_conditions` shall detect breakout conditions.
- [x] `score_research_hypothesis` shall score research evidence quality.
- [x] `check_sample_size` shall validate whether a sample is large enough for the intended research claim.
- [x] `check_lookahead_bias_risk` shall assess lookahead-bias risk.
- [x] `check_hypothesis_testability` shall assess whether a hypothesis is testable.
- [x] `check_contradictory_evidence` shall assess whether evidence contradicts the proposed hypothesis.
- [x] Network-backed research helpers shall be isolated from core deterministic calculations and shall be skippable in offline or heavy-environment tests.
- [x] Serialization helpers shall support masked JSON or Markdown output without leaking sensitive source details.
- [x] No file-specific non-functional requirements defined.
- [x] No file-specific testing requirements defined.
- [x] The module shall be sandboxed and shall not place, modify, cancel, or route live orders.
- [x] Research outputs shall clearly distinguish observations, assumptions, warnings, and validation evidence from approved trading decisions.
- [x] Standard tool envelopes shall include side-effect, approval-required, dry-run, environment, risk-level, and timing audit fields.
- [x] The standard research envelope schema shall be versioned and referenced by every network-backed helper, standard helper, evidence-pack helper, and future agent-facing research tool.
- [x] Public exports shall remain unique and resolvable through the lazy namespace.
- [x] The module shall remain interoperable with analytics, optimization, risk, and execution modules only through documented public contracts.
- [x] `ResearchResourceLimits` shall define `max_duration_seconds`, `max_memory_mb`, `max_rows`, and behavior when a limit is exceeded.
- [x] Before production Builder handoff, the owner shall approve measurable resource targets for the first implementation slice, including maximum rows, runtime budget, memory budget, and reference hardware.
- [x] `run_session_breakout_strategy` shall evaluate an opening-range breakout strategy for a session.
- [x] `run_session_fade_strategy` shall evaluate a mean-reversion fade strategy within a session.
- [x] `EdgeClass` shall represent the classification category assigned to an edge.
- [x] `EdgeSummary` shall summarize mean-reversion and trend-persistence evidence for a symbol.
- [x] `classify_symbol` shall classify a symbol based on mean-reversion and trend-persistence evidence.
- [x] `SeasonalityFilters` shall describe calendar, session, or symbol filters for seasonality analysis.
- [x] `calmar_ratio` shall expose the analytics Calmar ratio for research workflows.
- [x] `expectancy` shall expose the analytics expectancy calculation for research workflows.
- [x] `max_drawdown` shall expose the analytics maximum drawdown calculation for research workflows.
- [x] `median_mae_mfe` shall expose the analytics median MAE/MFE calculation for research workflows.
- [x] `profit_factor` shall expose the analytics profit-factor calculation for research workflows.
- [x] `sharpe_ratio` shall expose the analytics Sharpe ratio calculation for research workflows.
- [x] `sortino_ratio` shall expose the analytics Sortino ratio calculation for research workflows.
- [x] `win_rate` shall expose the analytics win-rate calculation for research workflows.

#### `app/services/research/reporting.py`

Functions/classes:

- `save_markdown`
- `save_json`
- `generate_multi_symbol_report`
- `build_edge_profile_snapshot`
- `build_profile_summary`
- `build_dashboard_summary`
- `save_json_report`
- `save_markdown_report`
- `build_edge_lab_scorecard_report`

Requirements:

- [x] `result_to_markdown` shall convert an edge result into a Markdown report.
- [x] `result_to_summary` shall generate a concise summary dictionary from an edge result.
- [x] `save_markdown` shall persist an edge result report as Markdown and shall expose an `overwrite: bool` contract.
- [x] `save_json` shall persist an edge result report as JSON and shall expose an `overwrite: bool` contract.
- [x] `generate_multi_symbol_report` shall generate a combined report for multiple symbols.
- [x] `print_result_summary` shall print a concise result summary to console.
- [x] `build_edge_profile_snapshot` shall build a normalized snapshot payload from progressive Edge Lab tab results.
- [x] `build_profile_summary` shall build a concise dashboard-ready summary from one profile snapshot.
- [x] `build_dashboard_summary` shall build a UI or dashboard summary block from one profile snapshot.
- [x] `snapshot_report_json` shall build a machine-readable profile snapshot report.
- [x] `snapshot_report_markdown` shall render a human-readable profile snapshot report.
- [x] `comparison_report_markdown` shall render a Markdown comparison report from two profile snapshots.
- [x] `save_json_report` shall save one complete JSON profile report.
- [x] `save_markdown_report` shall save one complete Markdown profile report.
- [x] `build_edge_lab_scorecard_report` shall build a deterministic backend scorecard report from progressive Edge Lab outputs.
- [x] Report persistence functions shall define allowed output paths, overwrite behavior, atomic write behavior, encoding, masking behavior, permission-failure behavior, and return value.
- [x] No file-specific non-functional requirements defined.
- [x] No file-specific testing requirements defined.

#### `app/utils/errors.py`

Functions/classes:

- `Error`
- `ValidationError`
- `ConfigurationError`

Requirements:

- [x] All standard system exceptions and error codes shall be imported and reused from `app.utils.errors` to prevent duplicate declaration. Custom research exceptions must inherit from `app.utils.errors.Error` or `HaruQuantError`.
- [x] No file-specific non-functional requirements defined.
- [x] No file-specific testing requirements defined.


### Hardening Amendments

#### Lightweight Research Core dependency

Requirements:

- [x] Split Research into an earlier lightweight Research Core and the later full Research Edge Lab when implementation begins.
- [x] Implement Research Core before Strategy/Optimization promotion workflows depend on research evidence.
- [x] Research Core must include leakage checks, chronological split helpers, null baselines, simple feature studies, and statistical evidence summaries.
- [x] Research Core must produce evidence packs that Strategy, Analytics, and Optimization can consume without requiring the full Research Edge Lab UI/workbench.
- [x] Research Core must use canonical DataSlice, IndicatorResult, StrategySignal, BacktestResult, OptimizationCandidate, and AuditEvent contracts where applicable.
- [x] Full Research Edge Lab must remain read-only with respect to broker accounts, live trading, risk limit mutation, and execution activation.
- [x] Add tests proving research evidence cannot promote strategies, approve risk, or activate live trading without governed lifecycle approvals.

### Unit Tests Required

```text

tests/unit/app/services/research/

```

Test coverage:

- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text

tests/usage/app/services/12_research.py

```

Usage examples must show:

- `example_01_research_config_and_data_prep`: Demonstrate research config validation, data preparation, cleaning, and quality reports.
- `example_02_feature_engineering`: Demonstrate returns, volatility, range, momentum, Bollinger-style stats, Hurst, pivots, and regimes.
- `example_03_leakage_controls`: Demonstrate chronological splits, no-lookahead checks, forward-column masking, and leakage failures.
- `example_04_edge_studies`: Demonstrate mean reversion, trend persistence, session behavior, and null baseline studies.
- `example_05_statistical_validation`: Demonstrate bootstrap, permutation tests, null models, multiple-comparison correction, and thresholds.
- `example_06_market_structure`: Demonstrate market-structure profiles, calibration candidates, overrides, and stability summaries.
- `example_07_unsupervised_analysis`: Demonstrate PCA, clustering, labels, outperformance analysis, and risk-factor summaries.
- `example_08_research_reports`: Demonstrate markdown/json reports, profile snapshots, dashboard summaries, and advisory-only boundaries.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 290 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text

feat(research-edge-lab): implement Research Edge Lab feature pipelines and null models



- Build feature engineering pipelines and data leakage detectors

- Implement Exploratory Data Analysis (EDA) helpers and structural data validators

- Build statistical null-model testers and unsupervised learning studies

```

- [x] The module shall fail closed when a workflow attempts to mutate live trading state or bypass governance.
- [x] Until resource limits and reference hardware are approved, Research may not claim production-grade performance; oversized or long-running workflows must fail with a typed resource-limit error or standard-envelope resource-limit error instead of attempting unbounded work.
