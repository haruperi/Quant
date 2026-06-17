# 12_research.md - Requirements

## 1. Purpose

The research module provides sandboxed market-research, edge-discovery, feature-engineering, statistical-validation, market-structure, and report-generation capabilities for HaruQuant. It converts OHLCV/OHLCVS market data and research inputs into reproducible evidence artifacts, hypotheses, profiles, scorecards, summaries, and model-insight outputs without mutating live trading state or bypassing governance.

The module exists to help developers and analysts explore whether observed market behavior is statistically meaningful, reproducible, free from obvious leakage, and suitable for later promotion into strategy, risk, optimization, or execution workflows. Research outputs are advisory evidence only and cannot be consumed as execution authorization, risk approval, or live signal-control policy.

**Handoff Status**

Status: revision required before Builder handoff.

The requirements inventory is strong enough to describe the intended research domain, but implementation is blocked until public API overlaps are resolved, public API contracts, model schemas, standard envelope schema, exact behavior/error tables, reproducibility metadata, network-helper behavior, artifact persistence rules, measurable resource limits, usage failure paths, and requirement-to-test traceability are defined for the first approved implementation slice.

### 1.1 Assumptions and resolved decisions


### 1.2 Open Questions



## 2. Ownership

### 2.1 Owns

### 2.2 Does Not Own

## 3. Global API Contracts and Configuration

### 3.1 Public Capabilities Summary
- Each public export must be classified as stable public API, internal-support contract, compatibility re-export, experimental capability, or network-backed helper before Builder implementation.
- Each item in `app.services.research.__all__` must carry a documented classification label such as `stable`, `internal-support`, `compatibility-re-export`, `experimental`, `network-backed`, or `optional-provider`.
- `internal-support` and `compatibility-re-export` items must be excluded from agent-facing stable tool catalogs by default and must be documented as subject to breaking changes unless explicitly promoted through a versioned contract.
- Network-backed exports must be marked as `network-backed` and `optional-provider` in the lazy registry and must define provider-missing behavior.
- Each public callable must document input type, required fields, optional fields, output type, error behavior, side effects, determinism behavior, dependency behavior, and whether it may perform disk or network I/O.
- Re-exported analytics functions must preserve upstream analytics contracts and must be covered by research compatibility tests.

### 3.3 Configuration Defaults

## 4. Module Architecture

### 4.1 Target Folder Structure

```text
app/
  services/
    services/
        research/
          __init__.py          # Lazy export definitions
          config.py            # Configuration schemas (EdgeLabConfig, DataConfig)
          data.py              # Data cleaning, normalization, enrichment
          features.py          # Technical indicators and returns calculations
          leakage.py           # Lookahead validators and time partitions
          metrics.py           # MetricRegistry and metric calculators
          studies/
            __init__.py
            eds.py             # Mean reversion and trend persistence EDS
            null_models.py     # Resampling, bootstraps, and permutations
            structure.py       # Directional swing legs and market structures
            unsupervised.py    # PCA and clustering algorithms
          helpers.py           # Standard news/sentiment/calendar evidence helpers
          reporting.py         # Markdown reports and scorecards persistence
          errors.py            # Mapped error codes and exception classes```

### 4.2 Class Diagrams

```mermaid
classDiagram
    class MetricCalculator {
        <<interface>>
        +calculate(context) MetricValue
    }
    class MetricRegistry {
        +register(name, calculator)
        +resolve(name) MetricCalculator
        +calculate_all(context) CoreMetricProfile
    }
    class VolatilityCalculator {
        +calculate(context) MetricValue
    }
    class ReturnsCalculator {
        +calculate(context) MetricValue
    }
    MetricCalculator <|.. VolatilityCalculator
    MetricCalculator <|.. ReturnsCalculator
    MetricRegistry --> MetricCalculator
```

## 5. General / Cross-Cutting Non-Functional Requirements

- [ ] The module shall be sandboxed and shall not place, modify, cancel, or route live orders.
- [ ] The module shall fail closed when a workflow attempts to mutate live trading state or bypass governance.
- [ ] Research outputs shall clearly distinguish observations, assumptions, warnings, and validation evidence from approved trading decisions.
- [ ] Multiple-comparison checks shall be available when evaluating many hypotheses or candidates.
- [ ] Standard tool envelopes shall include side-effect, approval-required, dry-run, environment, risk-level, and timing audit fields.
- [ ] The standard research envelope schema shall be versioned and referenced by every network-backed helper, standard helper, evidence-pack helper, and future agent-facing research tool.
- [ ] Public exports shall remain unique and resolvable through the lazy namespace.
- [ ] The module shall remain interoperable with analytics, optimization, risk, and execution modules only through documented public contracts.
- [ ] `ResearchResourceLimits` shall define `max_duration_seconds`, `max_memory_mb`, `max_rows`, and behavior when a limit is exceeded.
- [ ] Before production Builder handoff, the owner shall approve measurable resource targets for the first implementation slice, including maximum rows, runtime budget, memory budget, and reference hardware.
- [ ] Until resource limits and reference hardware are approved, Research may not claim production-grade performance; oversized or long-running workflows must fail with a typed resource-limit error or standard-envelope resource-limit error instead of attempting unbounded work.

### 5.1 Other Global and Cross-Cutting Requirements

- Optional external-feed helper contracts. External-feed helper exports may be absent or disabled when the corresponding provider adapter is not installed; importing `app.services.research` must not fail because of a missing optional adapter.
- [ ] `run_session_breakout_strategy` shall evaluate an opening-range breakout strategy for a session.
- [ ] `run_session_fade_strategy` shall evaluate a mean-reversion fade strategy within a session.
- [ ] `EdgeClass` shall represent the classification category assigned to an edge.
- [ ] `EdgeSummary` shall summarize mean-reversion and trend-persistence evidence for a symbol.
- [ ] `ClassificationResult` shall represent the result of classifying a symbol's edge profile.
- [ ] `classify_symbol` shall classify a symbol based on mean-reversion and trend-persistence evidence.
- [ ] `active_sessions_for_hour` shall return the active trading sessions for a given hour.
- [ ] `session_label_for_hour` shall return the session label for a given hour.
- [ ] `SeasonalityFilters` shall describe calendar, session, or symbol filters for seasonality analysis.
- [ ] `calmar_ratio` shall expose the analytics Calmar ratio for research workflows.
- [ ] `expectancy` shall expose the analytics expectancy calculation for research workflows.
- [ ] `max_drawdown` shall expose the analytics maximum drawdown calculation for research workflows.
- [ ] `median_mae_mfe` shall expose the analytics median MAE/MFE calculation for research workflows.
- [ ] `profit_factor` shall expose the analytics profit-factor calculation for research workflows.
- [ ] `sharpe_ratio` shall expose the analytics Sharpe ratio calculation for research workflows.
- [ ] `sortino_ratio` shall expose the analytics Sortino ratio calculation for research workflows.
- [ ] `win_rate` shall expose the analytics win-rate calculation for research workflows.
- Research artifacts containing sensitive fields that must be masked before persistence.
- Import-time safety tests proving `app.services.research` does not read secrets, access live trading state, call providers, write files, or perform heavy model execution at import time.
- The overlap resolutions above must be moved into Functional Requirements before Builder handoff; this section cannot remain the only record of API responsibility.
- Standard research envelope schema, canonical error taxonomy, and audit fields must be frozen before any network-backed or agent-facing research helper is implemented.
- Measurable resource targets and reference hardware must be approved before claiming production-grade performance.
- The public namespace exposes both the active `__all__` contract and additional local research classes that may be used internally; rebuild planning should treat `__all__` as the externally visible minimum and local public classes as important implementation-support contracts.
- Research outputs should continue to be treated as evidence, not approval to trade.
- Statistical evidence can be sensitive to sample size, market regime, timeframe, and multiple testing; reports should keep uncertainty and caveats visible.

## 6. Detailed Requirements by File

### File: app/services/research/__init__.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/research/__init__.py`.

#### Functional Requirements
- [ ] Importing `app.services.research` shall not perform network calls, disk writes, provider initialization, credential reads, live trading state access, or heavy model execution.

#### Non-Functional & Security Requirements
- [ ] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [ ] No file-specific testing requirements defined.

### File: app/services/research/config.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/research/config.py`.

#### Functional Requirements
- [ ] `create_config` shall create an Edge Lab configuration object with common defaults for research workflows.
- [ ] `DataConfig` shall describe source, symbol, timeframe, and date-range data inputs for research workflows.
- [ ] `SessionConfig` shall describe trading-session windows and related session settings.
- [ ] `BootstrapConfig` shall describe bootstrap resampling settings.
- [ ] `PermutationConfig` shall describe permutation-test settings.
- [ ] `NullModelsConfig` shall describe null-model settings and acceptance criteria.
- [ ] `MeanReversionConfig` shall describe mean-reversion edge-discovery settings.
- [ ] `TrendPersistenceConfig` shall describe trend-persistence edge-discovery settings.
- [ ] `MarketStructureConfig` shall describe market-structure research settings.
- [ ] `SessionEdgeConfig` shall describe session-edge research settings.
- [ ] `EdgeLabConfig` shall aggregate the module's research configuration sections into one workflow-level configuration.
- [ ] `TradeSample` shall represent a normalized trade sample for edge-result reporting.
- [ ] `EdgeStats` shall represent summary statistics for an edge result.
- [ ] `EdgeResult` shall represent a complete edge-study result suitable for summaries and reports.
- [ ] `research_modeling_module` shall return the research modeling service module through the shared lazy-resolution utility.
- [ ] Each public export in `app.services.research.__all__` shall have a documented contract specifying API status, input types, required fields, output type, error behavior, side effects, determinism guarantees, network/heavy dependency status, and stability level.
- [ ] Core model contracts shall define required fields, optional fields, schema versions, validation behavior, serialization behavior, and example payloads for `PreparedDataset`, `DataQualityReportModel`, `EdgeResult`, `CoreMetricProfile`, `MarketStructureProfile`, `UnsupervisedResearchResult`, `UnsupervisedInsightReport`, and report payloads.
- [ ] The module shall define a canonical research error taxonomy covering validation errors, configuration errors, insufficient-data errors, statistical-invalidity errors, external-provider errors, serialization errors, resource-limit errors, and permission errors.
- [ ] Public library functions shall either raise typed research exceptions or return structured result objects with warnings according to their documented contract; standard research tools shall return errors through the standard HaruQuant envelope.
- [ ] Each public callable contract shall explicitly choose one failure pattern: typed exception, structured result with warnings/errors, or standard research envelope. Mixed behavior is not allowed unless every branch is documented.
- [ ] The standard research envelope shall define at least `status`, `data`, `errors`, `warnings`, `audit`, `side_effect`, `approval_required`, `dry_run`, `environment`, `risk_level`, and `timing`.
- [ ] Standard research envelope `errors` and `warnings` shall use machine-readable codes, human-readable messages, optional field paths, severity, retryability, and bounded details.
- [ ] Standard research envelope `audit` shall include request ID, correlation ID where available, tool/capability name, schema version, source references where applicable, created-at timestamp, and redaction/provenance metadata.
- [ ] Standard research envelope schema must be frozen for the approved first implementation slice before any network-backed, standard helper, evidence-pack, or agent-facing research helper is implemented.
- [ ] Each public callable in the approved implementation slice shall have a behavior/error table that maps invalid input, insufficient data, unsupported config, provider unavailable, rate limit, serialization failure, resource limit, and permission failure to one exact typed exception, structured result warning/error, or standard envelope error.
- [ ] Provisional insufficient-sample behavior: research calculations should fail with a typed validation error or standard-envelope error code such as `ERR_INSUFFICIENT_SAMPLES` when the approved minimum sample size is not met; final code names and thresholds remain pending owner/architect approval.
- [ ] The first implementation slice shall be explicitly approved before Builder handoff; proposed initial slice is data preparation plus core metrics unless the owner approves a different slice.
- [ ] A contract-first checklist shall block coding until every public callable in the approved slice has input/output types, error model, determinism guarantee, side-effect classification, envelope/result shape, examples, and mapped tests.
- [ ] The module glossary shall define `Edge Lab`, `null baseline`, `profile snapshot`, `research envelope`, `advisory evidence`, `leakage report`, and `research artifact`.
- [ ] `CleaningConfig` shall describe data-cleaning behavior for timezone normalization, missing bars, non-trading periods, and spread anomalies.
- [ ] `CleaningConfig` shall define `missing_bar_strategy` with approved values such as `drop`, `forward_fill`, `interpolate`, and `none`, with deterministic behavior documented for each value.
- [ ] `CleaningConfig.missing_bar_strategy` default must be owner-approved before implementation. No Builder may infer a default or silently fill/drop bars without an approved default and explicit quality-report action.
- [ ] `CleaningConfig` shall define `non_trading_period_strategy` with approved values and shall document weekend, holiday, synthetic-bar, and provider-gap behavior.
- [ ] `clean_dataset` shall normalize timestamps to the configured timezone, resolve duplicate or non-monotonic timestamps according to `CleaningConfig`, apply configured missing-bar and non-trading-period handling, detect spread anomalies, and return both cleaned data and a `DataQualityReportModel` containing machine-readable cleaning actions and unresolved warnings.
- [ ] `EnrichmentConfig` shall describe enrichment settings for pip metadata, bar geometry, returns, labels, calendar fields, and sessions.
- [ ] `prepare_research_dataset` shall accept either in-memory raw OHLCV/OHLCVS data or a configured research data source, apply cleaning, validation, and enrichment in deterministic order, and return a `PreparedDataset` containing prepared data, metadata, and a quality report. It shall fail with a typed validation or configuration error when fatal issues prevent safe research use.
- [ ] `sma` shall compute simple moving averages over a configured window.
- [ ] `ema` shall compute exponential moving averages over a configured span.
- [ ] `std` shall compute rolling standard deviation over a configured window.
- [ ] `validate_no_lookahead_features` shall inspect declared feature metadata, column naming conventions, target/horizon columns, and configured allowed-forward columns, then return a structured leakage report identifying suspected lookahead fields, severity, evidence, and recommended action without mutating the input frame.
- [ ] `compute_session_statistics` shall calculate detailed statistics for a configured trading session.
- [ ] `run_eds_session` shall run session-edge discovery across configured session studies.
- [ ] Edge-discovery results shall include sample size, evaluated rule/config, source dataset identity, split identifiers, uncertainty metadata, warnings, and an advisory-only disclaimer.
- [ ] `exceeds_null_threshold` shall determine whether an observed value exceeds a configured null-distribution threshold.
- [ ] Bootstrap, permutation, and null-generation functions shall accept an explicit `seed` parameter or source one from a documented configuration object; returned results shall record the effective seed.
- [ ] `build_market_structure_research_profile` shall build a `MarketStructureProfile` plus configured research-only validation layers, including calibration evidence, stability summary, robustness summary, warnings, runtime metadata, and quality-adjusted confidence fields.
- [ ] `UnsupervisedResearchConfig` shall describe unsupervised research settings.
- [ ] `UnsupervisedResearchConfig` shall include a `seed` field used by non-deterministic algorithms.
- [ ] `cluster_feature_space` shall consume `UnsupervisedResearchConfig.seed` or an explicit seed parameter so K-Means output is reproducible for fixed inputs and dependency versions.
- [ ] `session_hours_payload` shall return a machine-readable payload describing configured session hours.
- [ ] `fetch_forexfactory_news` shall retrieve ForexFactory news data through an isolated provider adapter using configured timeout, retry, rate-limit, cache, and offline-test behavior, then return a standard research envelope containing status, normalized data, provider metadata, source timestamp, warnings, errors, and audit metadata.
- [ ] `fetch_forexfactory_calendar` shall retrieve ForexFactory economic calendar data through an isolated provider adapter using configured timeout, retry, rate-limit, cache, stale-data, and offline-test behavior, then return it through the standard research envelope.
- [ ] `fetch_forexfactory_sentiment` shall retrieve ForexFactory sentiment data through an isolated provider adapter using configured timeout, retry, rate-limit, cache, stale-data, and offline-test behavior, then return it through the standard research envelope.
- [ ] `fetch_forexfactory_instrument_page` shall retrieve a symbol-specific ForexFactory page through an isolated provider adapter using configured timeout, retry, rate-limit, cache, stale-data, and offline-test behavior, then return it through the standard research envelope.
- [ ] ForexFactory and other external-feed helpers shall be optional-provider capabilities. Missing provider adapters shall return a deterministic provider-unavailable envelope or documented typed configuration error without breaking import or unrelated research workflows.
- [ ] Persisted research artifacts shall include artifact schema version, module version, config hash, dataset identity or data hash, random seed, generated-at timestamp, timezone, source references, and dependency/version metadata required to reproduce the result.
- [ ] Persisted research artifacts shall include SHA-256 hashes of the input dataset identity or canonical data snapshot and the effective configuration used to generate the artifact.
- [ ] Network-backed research helpers shall enforce configured timeout, retry, rate-limit, cache, stale-data, and provider-layout-change behavior and shall return partial or failed results only through the standard research envelope with warnings and audit metadata.
- [ ] Seeded research workflows shall produce equivalent outputs for fixed input data, configuration, random seed, dependency versions, and artifact schema version.
- [ ] Report and artifact serialization shall prevent path traversal, accidental overwrite unless configured, and leakage of masked fields.
- [ ] Long-running workflows shall expose duration metadata and shall support configured resource limits or fail with a typed resource-limit error.

#### Non-Functional & Security Requirements
- [ ] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- `CleaningConfig` strategy enums and exact cleaning actions must be approved before data-preparation implementation.
- `CleaningConfig` defaults, including `missing_bar_strategy`, must be approved before implementation.

### File: app/services/research/data.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/research/data.py`.

#### Functional Requirements
- DataFrame-returning functions must document required input columns, output columns, index behavior, timezone expectations, row alignment, NaN behavior, and whether the input is mutated.
- [ ] `CanonicalOHLCVSSchema` shall define the canonical research dataset schema for OHLCV data with spread support.
- [ ] `DatasetIssue` shall represent a detected dataset quality issue.
- [ ] `CleaningAction` shall represent a cleaning action applied to research data.
- [ ] `DataQualityReportModel` shall summarize validation issues and cleaning actions for a dataset.
- [ ] `PreparedDataset` shall carry cleaned, validated, enriched data with its quality report and metadata.
- [ ] `enrich_dataset` shall add research features such as pip metadata, bar geometry, return labels, calendar fields, and session fields.
- [ ] `validate_dataset` shall validate schema, continuity, OHLC consistency, duplicate timestamps, spread quality, and volume fields while distinguishing fatal validation errors from warnings through machine-readable issue codes.
- [ ] `DataSource` shall represent the shared data-source descriptor used by research dataset validation.
- [ ] `OHLCVSchema` shall represent the shared OHLCV schema descriptor used by research dataset validation.
- [ ] `LeakageReport` shall define `suspected_columns`, `severity`, `evidence`, `recommendation`, `allowed_forward_columns`, `target_column`, and request/source metadata.
- [ ] `MetricValue` shall represent one normalized metric value with metadata.
- [ ] `MetricContext` shall provide the dataset and metadata needed by metric calculators.
- [ ] `CoreMetricProfile` shall represent a normalized profile of core dataset metrics.
- [ ] `build_core_metric_profile` shall build a normalized core metric profile from a prepared dataset.
- [ ] Metric profile output shall define units, sample size, source dataset identity, warnings, undefined-value behavior, and reproducibility metadata.
- [ ] `build_market_structure_profile` shall build a directional market-structure profile from a prepared dataset.
- [ ] `build_market_structure_robustness_report` shall report robustness of market-structure behavior across parameter or data variations.
- [ ] `ClusterModelResult` shall represent clustering labels and cluster metadata.
- [ ] `InvestmentDataSummary` shall represent descriptive statistics for investment data.
- [ ] `summarize_investment_data` shall return key descriptive statistics for investment data.
- [ ] Unsupervised modeling outputs shall include preprocessing metadata, selected feature columns, dropped columns, scaler behavior, seed, model parameters, and cluster/component diagnostics.
- [ ] `tag_sessions` shall tag each market-data row with its trading session.
- [ ] `run_seasonality` shall calculate seasonality statistics for the provided dataset and filters.
- [ ] External-feed helpers shall handle HTTP 429 responses, including missing or invalid `Retry-After` headers, through deterministic rate-limit errors or warnings with bounded retry metadata.
- [ ] `check_data_snooping_risk` shall assess data-snooping risk.
- [ ] Report persistence functions shall write to a temporary file and atomically rename where the platform supports it; unsupported atomic behavior shall be disclosed in the result metadata or typed error.
- [ ] Research artifacts shall preserve source references, assumptions, warnings, and enough metadata to reproduce the result.
- [ ] Data preparation and feature pipelines shall avoid lookahead bias and shall support explicit chronological split validation.
- [ ] Statistical results shall expose uncertainty where applicable, including p-values, confidence intervals, null percentiles, or comparable validation metadata.
- [ ] Public standard tools shall return the standard HaruQuant envelope containing status, tool metadata, request metadata, data, errors, warnings, and audit metadata.
- [ ] The module shall avoid storing real secrets, credentials, private broker data, or unredacted private artifacts.
- [ ] Proposed benchmark placeholder: `prepare_research_dataset` should process up to 1,000,000 rows in no more than 30 seconds on approved reference hardware; this remains pending until owner approval.

#### Non-Functional & Security Requirements
- [ ] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- ForexFactory helper ownership must be explicitly scoped as optional external research-feed helper behavior, not broad market-data provider ownership.

### File: app/services/research/features.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/research/features.py`.

#### Functional Requirements
- [ ] `log_returns` shall compute log returns from close prices.
- [ ] `simple_returns` shall compute arithmetic returns from close prices.
- [ ] `zscore` shall compute a close-price z-score relative to a moving average and standard deviation.
- [ ] `percent_rank` shall compute rolling percentile rank values.
- [ ] `atr` shall compute Average True Range.
- [ ] `atr_percent` shall compute ATR as a percentage of close price.
- [ ] `bollinger_bands` shall compute Bollinger-style upper, middle, and lower bands.
- [ ] `bb_width` shall compute Bollinger Band width.
- [ ] `bb_percent_b` shall compute Bollinger Band percent-B.
- [ ] `rolling_percentile_rank` shall compute rolling percentile rank for a supplied series.
- [ ] `rsi` shall compute Relative Strength Index.
- [ ] `rate_of_change` shall compute rate of change as a momentum measure.
- [ ] `momentum` shall compute simple price-difference momentum.
- [ ] `donchian_channel` shall compute Donchian breakout levels.
- [ ] `hurst_exponent` shall estimate Hurst exponent for mean-reversion versus trend detection.
- [ ] `rolling_hurst` shall compute Hurst exponent over rolling windows.
- [ ] `pivot_points` shall compute pivot, support, and resistance levels.
- [ ] `adr` shall compute Average Daily Range.
- [ ] `forward_returns` shall compute horizon-aligned forward log returns.
- [ ] `forward_max_favorable_excursion` shall compute maximum favorable price excursion over a forward horizon.
- [ ] `forward_max_adverse_excursion` shall compute maximum adverse price excursion over a forward horizon.
- [ ] `detect_volatility_regime` shall classify volatility regime using ATR percentile or equivalent volatility evidence.
- [ ] `detect_trend_regime` shall classify trend regime from moving-average relationships.
- [ ] `build_market_regime_feature_frame` shall build timestamp-aligned feature rows for PCA and clustering regime research.
- [ ] Feature functions shall define warm-up-period behavior, NaN handling, minimum window behavior, numeric precision expectations, and input mutation behavior.
- [ ] Forward-looking feature functions shall clearly label forward columns as research-only and shall be detectable by leakage checks.
- [ ] `FeatureSetFrame` shall represent the feature frame used by unsupervised modeling.
- [ ] `calculate_regime_features` shall calculate regime feature rows.
- [ ] `detect_market_regime` shall classify market regime from supplied research features.

#### Non-Functional & Security Requirements
- [ ] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- `detect_volatility_regime`, `detect_trend_regime`, `detect_market_regime`, `calculate_regime_features`, and `build_market_regime_feature_frame` must have documented boundaries.

### File: app/services/research/leakage.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/research/leakage.py`.

#### Functional Requirements
- [ ] `TimeSplitResult` shall represent deterministic chronological train, validation, and test partitions.
- [ ] `enforce_time_split` shall enforce deterministic chronological train, validation, and test splits.
- [ ] `mask_research_artifact` shall remove or redact sensitive fields from research artifacts before persistence or sharing.
- [ ] `dump_masked_research_json` shall serialize a masked research artifact to JSON.

#### Non-Functional & Security Requirements
- [ ] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [ ] No file-specific testing requirements defined.

### File: app/services/research/metrics.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/research/metrics.py`.

#### Functional Requirements
- [ ] `MetricCalculator` shall define the calculator interface for research core metrics.
- [ ] `MetricRegistry` shall register and resolve named metric calculators.
- [ ] `ReturnsCalculator` shall calculate return-related core metrics.
- [ ] `RocCalculator` shall calculate rate-of-change core metrics.
- [ ] `CandlesCalculator` shall calculate candle-geometry core metrics.
- [ ] `RangesCalculator` shall calculate range-related core metrics.
- [ ] `VolatilityCalculator` shall calculate volatility core metrics.
- [ ] `SpreadCalculator` shall calculate spread-quality core metrics.
- [ ] `VolumeActivityCalculator` shall calculate volume or activity core metrics.
- [ ] `build_default_registry` shall build the default registry of research metric calculators.

#### Non-Functional & Security Requirements
- [ ] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [ ] No file-specific testing requirements defined.

### File: app/services/research/studies/__init__.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/research/studies/__init__.py`.

#### Functional Requirements
- [ ] No file-specific functional requirements defined. Foundation properties apply.

#### Non-Functional & Security Requirements
- [ ] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [ ] No file-specific testing requirements defined.

### File: app/services/research/studies/eds.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/research/studies/eds.py`.

#### Functional Requirements
- [ ] `run_eds_null_baseline` shall establish null-model baselines for edge-discovery studies.
- [ ] `run_eds_mean_reversion` shall evaluate a mean-reversion detector based on compression and z-score fade behavior.
- [ ] `run_eds_trend_persistence` shall evaluate a trend-persistence detector based on high-ATR breakout follow-through behavior.
- [ ] Null-model functions shall define behavior for invalid sample sizes, non-finite statistics, empty distributions, random seeds, replacement/block settings, and multiple-comparison correction applicability.
- [ ] Null-model behavior/error tables shall dictate exact outcomes for invalid sample sizes, non-finite statistics, empty distributions, invalid random seeds, invalid replacement/block settings, and inapplicable multiple-comparison corrections; these cases may not be left to Builder interpretation.

#### Non-Functional & Security Requirements
- [ ] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [ ] No file-specific testing requirements defined.

### File: app/services/research/studies/null_models.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/research/studies/null_models.py`.

#### Functional Requirements
- [ ] `compare_to_null` shall compare observed expectancy or performance against a null distribution.
- [ ] `get_acceptance_criteria` shall extract acceptance criteria from a null baseline.
- [ ] `block_bootstrap_ci` shall compute a confidence interval using block bootstrap resampling.
- [ ] `block_bootstrap_distribution` shall generate a bootstrap distribution for a statistic.
- [ ] `permutation_test` shall compute a permutation-test p-value.
- [ ] `random_entry_null` shall generate a null distribution from random entries in log-return space.
- [ ] `r_space_null` shall generate a null distribution in R-multiple space.
- [ ] `session_randomized_null` shall generate a null distribution by shuffling entries within the same session.
- [ ] `shuffle_returns_null` shall generate a null distribution by shuffling return blocks.
- [ ] `benjamini_hochberg` shall apply Benjamini-Hochberg false-discovery-rate correction.
- [ ] `holm_bonferroni` shall apply Holm-Bonferroni multiple-comparison correction.
- [ ] `compute_null_percentile` shall compute the percentile of an observed value within a null distribution.
- [ ] `null_distribution_stats` shall compute summary statistics for a null distribution.

#### Non-Functional & Security Requirements
- [ ] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [ ] No file-specific testing requirements defined.

### File: app/services/research/studies/structure.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/research/studies/structure.py`.

#### Functional Requirements
- [ ] `TrendSwingPoint` shall represent a detected swing point used in market-structure analysis.
- [ ] `TrendLeg` shall represent a directional leg between swing points.
- [ ] `TrendScoreRow` shall represent one market-structure score row.
- [ ] `MarketStructureProfile` shall represent a reproducible directional structure profile.
- [ ] `MarketStructureCalibrationCandidate` shall represent one calibration candidate for market-structure classification.
- [ ] `classify_with_candidate` shall classify market structure using one calibration candidate.
- [ ] `build_calibration_grid` shall build candidate parameter grids for market-structure calibration.
- [ ] `evaluate_calibration_candidates` shall evaluate market-structure calibration candidates against realized evidence.
- [ ] `MarketStructureMetricCalibrationCandidate` shall represent one metric-calibration candidate.
- [ ] `build_metric_calibration_grid` shall build candidate grids for market-structure metric calibration.
- [ ] `evaluate_metric_calibration_candidates` shall evaluate metric-calibration candidates against target behavior.
- [ ] `evaluate_profile_calibration` shall evaluate profile-level calibration behavior.
- [ ] `timeframe_bucket` shall map a timeframe into a market-structure profile bucket.
- [ ] `symbol_class` shall map a symbol into a market-structure symbol class.
- [ ] `resolve_market_structure_profile` shall resolve the applicable market-structure profile for a symbol and timeframe.
- [ ] `resolve_market_structure_profile_overrides` shall resolve profile overrides for a symbol, timeframe, or profile class.
- [ ] `confidence_bucket` shall convert validation evidence into a confidence bucket.
- [ ] `label_realized_market_behavior` shall classify realized future behavior as trend, reversion, or mixed.
- [ ] `build_validation_summary` shall summarize market-structure validation evidence.
- [ ] `build_market_structure_stability_report` shall report stability of market-structure behavior across samples or windows.
- [ ] `build_strategy_fit` shall assess advisory strategy-fit evidence from market-structure research and shall not approve strategy promotion, mutate strategy runtime state, or authorize execution changes.
- [ ] Market-structure calibration outputs shall include candidate parameters, ranking criteria, validation window, stability evidence, and warnings for unstable rankings.
- [ ] `parse_news_items` shall normalize raw news items into structured research records.
- [ ] `generate_research_hypothesis` shall generate a structured research hypothesis from inputs and evidence.
- [ ] `build_research_evidence_pack` shall build a structured research evidence pack containing source references, assumptions, warnings, and validation notes.
- [ ] The module shall emit structured warnings or logs for validation failures, dropped rows, masking actions, provider failures, statistical insufficiency, and partial report generation.

#### Non-Functional & Security Requirements
- [ ] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [ ] No file-specific testing requirements defined.

### File: app/services/research/studies/unsupervised.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/research/studies/unsupervised.py`.

#### Functional Requirements
- [ ] `UnsupervisedResearchRequest` shall represent one unsupervised research request.
- [ ] `UnsupervisedResearchResult` shall represent a complete unsupervised research result.
- [ ] `UnsupervisedResearchService` shall orchestrate unsupervised research workflows.
- [ ] `PcaModelResult` shall represent PCA scores, loadings, and explained variance.
- [ ] `run_pca` shall run PCA on numeric feature columns and return component scores and loadings.
- [ ] `cluster_feature_space` shall cluster numeric feature rows using deterministic K-Means labels.
- [ ] `attach_cluster_labels` shall attach cluster labels to a feature frame without mutating the input.
- [ ] `PcaRiskFactor` shall represent an interpreted PCA loading or risk factor.
- [ ] `ClusterOutperformance` shall represent forward-return evidence by cluster.
- [ ] `SignalAdaptationResult` shall represent signal-suppression or signal-adaptation recommendations by cluster.
- [ ] `UnsupervisedInsightReport` shall represent a complete unsupervised insight report for trading workflows.
- [ ] `identify_pca_risk_factors` shall extract the largest PCA loadings as interpretable risk factors.
- [ ] `compute_forward_returns` shall compute horizon-aligned forward returns from a price column.
- [ ] `analyze_cluster_outperformance` shall score clusters by future returns and assign semantic regime names.
- [ ] `adapt_signals_by_cluster` shall produce advisory signal-adaptation recommendations identifying clusters where forward-return evidence is weak; it shall not mutate strategy runtime state, block live entries, or authorize execution changes.
- [ ] `build_unsupervised_insight_report` shall build a complete unsupervised insight report for trading workflows.

#### Non-Functional & Security Requirements
- [ ] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- Seed source and propagation rules must be approved for bootstrap, permutation, null-model, clustering, and unsupervised workflows.

### File: app/services/research/helpers.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/research/helpers.py`.

#### Functional Requirements
- [ ] `parse_calendar_events` shall normalize economic calendar events.
- [ ] `parse_sentiment_snapshot` shall normalize sentiment-positioning snapshots.
- [ ] `filter_events_by_symbol` shall filter calendar events by the currencies or instruments relevant to a symbol.
- [ ] `classify_news_impact` shall classify the impact level of economic news.
- [ ] `create_news_blackout_windows` shall create advisory research blackout-window recommendations around news events and shall not create live no-trade controls or mutate risk/execution policy.
- [ ] `calculate_returns` shall calculate price returns for standard research tooling.
- [ ] `calculate_volatility` shall calculate rolling annualized volatility.
- [ ] `calculate_atr` shall calculate Average True Range.
- [ ] `calculate_adr` shall calculate Average Daily Range.
- [ ] `calculate_spread_statistics` shall calculate spread distribution statistics.
- [ ] `calculate_session_statistics` shall calculate session return statistics.
- [ ] `calculate_seasonality_statistics` shall calculate calendar seasonality statistics.
- [ ] `calculate_correlation_matrix` shall calculate a correlation matrix for research inputs.
- [ ] `detect_trend_strength` shall detect trend strength from moving-average evidence.
- [ ] `detect_mean_reversion_conditions` shall detect mean-reversion conditions.
- [ ] `detect_breakout_conditions` shall detect breakout conditions.
- [ ] `score_research_hypothesis` shall score research evidence quality.
- [ ] `check_sample_size` shall validate whether a sample is large enough for the intended research claim.
- [ ] `check_lookahead_bias_risk` shall assess lookahead-bias risk.
- [ ] `check_hypothesis_testability` shall assess whether a hypothesis is testable.
- [ ] `check_contradictory_evidence` shall assess whether evidence contradicts the proposed hypothesis.
- [ ] Network-backed research helpers shall be isolated from core deterministic calculations and shall be skippable in offline or heavy-environment tests.
- [ ] Serialization helpers shall support masked JSON or Markdown output without leaking sensitive source details.

#### Non-Functional & Security Requirements
- [ ] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [ ] No file-specific testing requirements defined.

### File: app/services/research/reporting.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/research/reporting.py`.

#### Functional Requirements
- [ ] `result_to_markdown` shall convert an edge result into a Markdown report.
- [ ] `result_to_summary` shall generate a concise summary dictionary from an edge result.
- [ ] `save_markdown` shall persist an edge result report as Markdown and shall expose an `overwrite: bool` contract.
- [ ] `save_json` shall persist an edge result report as JSON and shall expose an `overwrite: bool` contract.
- [ ] `generate_multi_symbol_report` shall generate a combined report for multiple symbols.
- [ ] `print_result_summary` shall print a concise result summary to console.
- [ ] `build_edge_profile_snapshot` shall build a normalized snapshot payload from progressive Edge Lab tab results.
- [ ] `build_profile_summary` shall build a concise dashboard-ready summary from one profile snapshot.
- [ ] `build_dashboard_summary` shall build a UI or dashboard summary block from one profile snapshot.
- [ ] `snapshot_report_json` shall build a machine-readable profile snapshot report.
- [ ] `snapshot_report_markdown` shall render a human-readable profile snapshot report.
- [ ] `comparison_report_markdown` shall render a Markdown comparison report from two profile snapshots.
- [ ] `save_json_report` shall save one complete JSON profile report.
- [ ] `save_markdown_report` shall save one complete Markdown profile report.
- [ ] `build_edge_lab_scorecard_report` shall build a deterministic backend scorecard report from progressive Edge Lab outputs.
- [ ] Report persistence functions shall define allowed output paths, overwrite behavior, atomic write behavior, encoding, masking behavior, permission-failure behavior, and return value.

#### Non-Functional & Security Requirements
- [ ] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [ ] No file-specific testing requirements defined.

### File: app/services/research/errors.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/research/errors.py` (which must inherit from `app/utils/errors.py` and reuse standard exception types).

#### Functional Requirements
- [ ] All standard system exceptions and error codes shall be imported and reused from `app.utils.errors` to prevent duplicate declaration. Custom research exceptions must inherit from `app.utils.errors.Error` or `HaruQuantError`.

#### Non-Functional & Security Requirements
- [ ] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [ ] No file-specific testing requirements defined.

## 7. Global Testing, Quality Gates, and Usage Examples


### 7.3 Usage Examples

#### Example 1
```python
from app.services.research import prepare_research_dataset, build_core_metric_profile

prepared = prepare_research_dataset(raw_data, config=config.data)
if getattr(prepared, "errors", None):
    raise RuntimeError("Research dataset preparation failed.")
profile = build_core_metric_profile(prepared)
```

#### Example 2
```python
from app.services.research import validate_no_lookahead_features, enforce_time_split

split = enforce_time_split(feature_frame, train_fraction=0.6, validation_fraction=0.2)
leakage_report = validate_no_lookahead_features(feature_frame, target_column="future_return")
if leakage_report.severity in {"high", "critical"}:
    raise RuntimeError("Lookahead risk must be resolved before research continues.")
```

#### Example 3
```python
from app.services.research import run_eds_mean_reversion, run_eds_null_baseline, compare_to_null

observed = run_eds_mean_reversion(prepared_dataset, config=config.mean_reversion)
baseline = run_eds_null_baseline(prepared_dataset, config=config.null_models)
comparison = compare_to_null(observed, baseline)
if comparison.warnings:
    review_warnings(comparison.warnings)
```

#### Example 4
```python
from app.services.research import build_market_structure_profile, build_validation_summary

structure = build_market_structure_profile(prepared_dataset, config=config.market_structure)
validation = build_validation_summary(structure, realized_behavior)
```

#### Example 5
```python
from app.services.research import build_research_evidence_pack, score_research_hypothesis

evidence_pack = build_research_evidence_pack(hypothesis=hypothesis, datasets=[prepared_dataset])
score = score_research_hypothesis(evidence_pack)
```

#### Example 6
```python
from app.services.research import fetch_forexfactory_calendar

calendar_response = fetch_forexfactory_calendar(symbol="EURUSD", request_id="req_example")
if calendar_response.get("status") == "error" or calendar_response.get("errors"):
    handle_provider_error(calendar_response.get("errors", []))
```

## 8. Acceptance
