## Phase 1.5 Core Domain Contracts

### Goal

Define canonical cross-domain models and protocol contracts before Data, Indicators, Strategies, Risk, Trading, Simulation, Analytics, Optimization, Live, UI/API, Research, and Conversation implement incompatible duplicates.

Task inventory: 73 checkbox tasks (73 checked, 0 unchecked).

### Dependency Files and Functionality

Required files:

```text
app/utils/
```

Required functionality:

- Canonical data, signal, risk, execution, portfolio, analytics, optimization, live, and audit contracts.
- Protocol interfaces for providers and governed service boundaries.
- Serialization, versioning, hashing, and compatibility rules.
- Contract tests shared by every later phase.

### Files to Create

```text
app/contracts/__init__.py
app/contracts/base.py
app/contracts/market.py
app/contracts/indicators.py
app/contracts/strategies.py
app/contracts/risk.py
app/contracts/trading.py
app/contracts/portfolio.py
app/contracts/simulation.py
app/contracts/analytics.py
app/contracts/optimization.py
app/contracts/live.py
app/contracts/audit.py
app/contracts/providers.py
tests/unit/app/contracts/
tests/usage/01_5_core_contracts.py
```

### Functionality to Implement

#### Canonical base contracts

Requirements:

- [X] Create `app/contracts/` as the canonical model boundary shared by all domain phases. *app.contracts.base:1*
- [X] Define a side-effect-free public registry in `app/contracts/__init__.py`. *app.contracts:1*
- [X] Ensure contract modules do not import broker SDKs, database clients, UI frameworks, LLM clients, or optional provider packages. *tests.unit.app.contracts.test_contracts:1*
- [X] Define a common contract base carrying `schema_version`, `created_at`, optional `request_id`, optional `workflow_id`, and optional `correlation_id` where applicable. *app.contracts.base.Contract:20*
- [X] Define deterministic serialization helpers for contract objects using JSON-safe values. *app.contracts.base.Contract.to_json:84*
- [X] Define deterministic contract hashing for reproducibility, caching, audit records, and evidence packs. *app.contracts.base.Contract.contract_hash:95*
- [X] Define contract compatibility rules based on major/minor schema versions. *app.contracts.base.Contract.check_compatibility:103*
- [X] Define validation helpers that return deterministic errors through the Utils error model. *app.contracts.base.Contract.validate_metadata_structure:46*
- [X] Ensure all canonical contracts are typed, documented, and safe to import in test, CLI, API, and agent runtimes. *app.contracts:1*
- [X] During the first three approved sprint packs after Phase 1.5, canonical contracts shall be treated as stabilization-stage contracts that may accept owner-approved additive changes without forcing broad downstream rewrites. *docs/phase-implementation-plan/01_5-core-domain-contracts.md:60*
- [X] Every canonical contract that crosses service or provider boundaries shall include a JSON-safe `metadata: dict[str, Any]` escape hatch for broker-specific, provider-specific, phase-specific, or experimental fields that are not stable enough to become first-class contract fields. *app.contracts.base.Contract:40*
- [X] Contract metadata shall be namespaced by owning adapter, provider, phase, or feature area to prevent collisions and accidental promotion of ambiguous keys. *app.contracts.base.Contract.validate_metadata_structure:53*
- [X] Contract metadata shall preserve deterministic serialization, hashing policy, redaction policy, and schema-version compatibility behavior. *app.contracts.base.Contract.validate_metadata_structure:71*

#### Market data contracts

Requirements:

- [X] Define `Symbol` with canonical symbol, broker symbol, asset class, quote currency, base currency, precision, lot/tick metadata, and provider metadata where applicable. *app.contracts.market.Symbol:31*
- [X] Define `Timeframe` with deterministic parsing, canonical names, duration metadata, and unsupported-timeframe validation. *app.contracts.market.Timeframe:51*
- [X] Define `Bar` with timestamp, open, high, low, close, optional volume, optional spread, symbol, timeframe, and source metadata. *app.contracts.market.Bar:63*
- [X] Define `Tick` with timestamp, bid, ask, last, volume, symbol, and source metadata. *app.contracts.market.Tick:98*
- [X] Define `Spread` with bid, ask, spread points, spread price, timestamp, symbol, and source metadata. *app.contracts.market.Spread:118*
- [X] Define `DataSlice` for bounded batches of bars, ticks, or records with source, retrieval, transformation, and quality metadata. *app.contracts.market.DataSlice:140*
- [X] Define canonical market-data error codes for unavailable symbols, unsupported timeframes, stale data, provider errors, and malformed payloads. *app.contracts.market:17*
- [X] Define raw-provider-data lineage fields: provider, provider_request_id, retrieved_at, normalized_at, transformation_hash, and source_hash. *app.contracts.market.DataSlice:150*

#### Indicator and strategy contracts

Requirements:

- [X] Define `IndicatorResult` with name, version, parameters, warmup period, input hash, output metadata, and deterministic result serialization. *app.contracts.indicators.IndicatorResult:11*
- [X] Define `StrategyInput` with market data references, indicator references, portfolio context, configuration, and timestamp boundaries. *app.contracts.strategies.StrategyInput:11*
- [X] Define `StrategySignal` as the only allowed strategy-to-risk output contract. *app.contracts.strategies.StrategySignal:31*
- [X] Ensure `StrategySignal` includes strategy ID, strategy version, parameter hash, symbol, side, confidence, validity window, reason, evidence references, and source data hash. *app.contracts.strategies.StrategySignal:31*
- [X] Ensure strategy contracts cannot represent broker-specific order placement directly. *app.contracts.strategies.StrategySignal:33*
- [X] Define strategy contract validation that rejects signals with missing symbol, invalid side, expired validity window, missing evidence where required, or broker-specific mutation fields. *app.contracts.strategies.StrategySignal.validate_symbol_non_empty:48*

#### Risk and execution contracts

Requirements:

- [X] Define `RiskDecision` as the only allowed risk-to-execution approval or rejection contract. *app.contracts.risk.RiskDecision:36*
- [X] Define `RiskRejection` with deterministic code, severity, reason, violated limit, evidence, and remediation metadata. *app.contracts.risk.RiskRejection:11*
- [X] Define `PositionSizingResult` with requested size, approved size, sizing method, constraints applied, and risk contribution. *app.contracts.risk.PositionSizingResult:25*
- [X] Define `OrderIntent` as the canonical post-risk pre-execution request. *app.contracts.trading.OrderIntent:16*
- [X] Define `TradeRequest` as the canonical execution-layer request after all required risk and approval gates pass. *app.contracts.trading.TradeRequest:32*
- [X] Define `TradeResult` with accepted, rejected, pending, partially filled, filled, cancelled, expired, failed, and reconciled states. *app.contracts.trading.TradeResult:46*
- [X] Define `ExecutionReport` and `Fill` contracts with broker-neutral execution status, fill price, quantity, commission, slippage, latency, provider IDs, and timestamps. *app.contracts.trading.Fill:69*
- [X] Define `BrokerCapabilities` for supported order types, fill policies, asset classes, time-in-force options, margin mode, hedging/netting mode, and provider limits. *app.contracts.trading.BrokerCapabilities:120*
- [X] Define provider protocols: `MarketDataProvider`, `ExecutionProvider`, `AccountProvider`, `PositionProvider`, `OrderProvider`, `SymbolInfoProvider`, and `BrokerErrorMapper`. *app.contracts.providers:17*
- [X] Ensure provider protocols return canonical contracts and do not expose raw broker SDK objects outside integration boundaries. *app.contracts.providers:1*
- [X] Broker-specific reconciliation fields discovered by Trading, Simulation, Paper, Shadow, or Live providers shall use canonical contract `metadata` until repeated cross-provider use justifies a first-class contract field. *app.contracts.base.Contract:40*
- [X] `TradeResult`, `ExecutionReport`, and `Fill` metadata shall support provider reconciliation references, broker ticket aliases, venue execution hints, and diagnostic adapter fields without changing service-layer callers. *app.contracts.base.Contract:40*

#### Portfolio, simulation, analytics, optimization, live, and audit contracts

Requirements:

- [X] Define `AccountSnapshot` with equity, balance, margin, free margin, currency, leverage, timestamp, and provider metadata. *app.contracts.portfolio.AccountSnapshot:16*
- [X] Define `Position` with symbol, side, quantity, average price, unrealized PnL, realized PnL, margin, provider IDs, and timestamps. *app.contracts.portfolio.Position:35*
- [X] Define `PortfolioSnapshot` with account, positions, pending exposure, risk budget, correlation metadata, and freshness metadata. *app.contracts.portfolio.PortfolioSnapshot:59*
- [X] Define `BacktestConfig` with dataset references, strategy references, cost model, fill model, calendar, split policy, and reproducibility seed. *app.contracts.simulation.BacktestConfig:11*
- [X] Define `BacktestResult` with run ID, config hash, journal reference, equity curve reference, metrics reference, and evidence metadata. *app.contracts.simulation.BacktestResult:23*
- [X] Define `OptimizationCandidate` with strategy, parameters, score, robustness metrics, validation splits, overfitting checks, and evidence references. *app.contracts.optimization.OptimizationCandidate:11*
- [X] Define `LiveSessionState` with environment mode, provider status, risk status, kill-switch state, reconciliation status, and operator approval status. *app.contracts.live.LiveSessionState:25*
- [X] Define `AuditEvent` with event ID, event type, severity, actor, subject, action, evidence, redacted payload hash, and timestamp metadata. *app.contracts.audit.AuditEvent:16*
- [X] Define `KillSwitchState` and `RiskAuditEvent` contracts shared by Risk, Trading, Live, UI/API, and Conversation. *app.contracts.live.KillSwitchState:15*
- [X] Define `ExecutionJournal` and `TradeStore` protocol contracts for persisted orders, positions, executions, fills, idempotency keys, and reconciliation records. *app.contracts.providers.ExecutionJournal:88*

#### Contract governance

Requirements:

- [X] Add a rule that domain modules must import canonical contracts rather than redefining cross-domain models. *docs/phase-implementation-plan/01_5-core-domain-contracts.md:125*
- [X] Add a rule that raw broker SDK objects, raw exchange payloads, and UI DTOs must be adapted into canonical contracts before crossing service boundaries. *docs/phase-implementation-plan/01_5-core-domain-contracts.md:126*
- [X] Add a rule that API DTOs may wrap canonical contracts but may not replace domain contracts. *docs/phase-implementation-plan/01_5-core-domain-contracts.md:127*
- [X] Add a rule that conversation memory stores summaries and references, not raw sensitive canonical payloads. *docs/phase-implementation-plan/01_5-core-domain-contracts.md:128*
- [X] Add a compatibility review requirement before changing public contract names, fields, schema versions, or serialization behavior. *docs/phase-implementation-plan/01_5-core-domain-contracts.md:129*
- [X] Add a stabilization review rule for the first three sprint packs: metadata fields that become repeated, required, or cross-domain shall be reviewed for promotion into first-class contract fields with migration notes. *docs/phase-implementation-plan/01_5-core-domain-contracts.md:130*
- [X] Add a rule that metadata may not contain raw broker SDK objects, raw exchange payloads, credentials, unredacted account identifiers, or opaque objects that cannot serialize deterministically. *app.contracts.base.Contract.validate_metadata_structure:53*
- [X] Add a rule that downstream phases must tolerate unknown metadata keys by preserving or safely ignoring them unless a documented validation policy rejects the namespace. *docs/phase-implementation-plan/01_5-core-domain-contracts.md:132*
- [X] Add usage examples showing Data -> Indicator -> StrategySignal -> RiskDecision -> OrderIntent -> ExecutionProvider -> TradeResult -> Analytics flow. *tests.usage.01_5_core_contracts:1*
- [X] Add contract tests proving canonical contracts serialize deterministically and validate malformed inputs consistently. *tests.unit.app.contracts.test_contracts:1*
- [X] Add tests proving provider protocols can be implemented by simulator, MT5, cTrader, Binance, and paper/shadow adapters without changing service-layer callers. *tests.unit.app.contracts.test_contracts.test_provider_protocols_conformance:598*

### Unit Tests Required

```text
tests/unit/app/contracts/
```

Test coverage:

- [X] Tests verify every contract imports without optional provider dependencies installed. *tests.unit.app.contracts.test_contracts:1*
- [X] Tests verify deterministic serialization, hashing, equality where applicable, and schema-version compatibility. *tests.unit.app.contracts.test_contracts.test_base_contract_serialization_and_hashing:51*
- [X] Tests verify invalid required fields, unsupported states, invalid timestamps, invalid symbols, invalid sides, and malformed provider metadata fail deterministically. *tests.unit.app.contracts.test_contracts.test_bar_contract_validation:154*
- [X] Tests verify provider protocols can be satisfied by fake adapters for market data, execution, account, position, order, and symbol info. *tests.unit.app.contracts.test_contracts.test_provider_protocols_conformance:598*
- [X] Tests verify strategy contracts cannot encode direct broker mutation requests. *tests.unit.app.contracts.test_contracts.test_strategy_signal_rejections:239*
- [X] Tests verify risk and execution contracts preserve correlation, request, workflow, idempotency, and audit identifiers. *tests.unit.app.contracts.test_contracts.test_all_other_models_instantiation:335*
- [X] Tests verify namespaced metadata survives serialization, hashing, copying, and provider round-trips without exposing raw provider payloads. *tests.unit.app.contracts.test_contracts.test_metadata_namespacing_and_secrets_rejection:93*

### Usage Examples Required

```text
tests/usage/01_5_core_contracts.py
```

Usage examples must show:

- [X] Example demonstrates canonical Bar and DataSlice construction from provider-like data. *tests.usage.01_5_core_contracts.example_data_slice_construction:60*
- [X] Example demonstrates IndicatorResult and StrategySignal creation with reproducibility metadata. *tests.usage.01_5_core_contracts.example_indicator_and_strategy_signal:81*
- [X] Example demonstrates RiskDecision approving or rejecting an OrderIntent. *tests.usage.01_5_core_contracts.example_risk_decision:107*
- [X] Example demonstrates simulator and live providers sharing the same ExecutionProvider protocol. *tests.usage.01_5_core_contracts.example_provider_sharing:139*
- [X] Example demonstrates TradeResult, ExecutionReport, Fill, PortfolioSnapshot, and BacktestResult serialization. *tests.usage.01_5_core_contracts.example_serialization:193*
- [X] Example demonstrates using metadata for a broker-specific reconciliation field and later reading it without changing the canonical service flow. *tests.usage.01_5_core_contracts.example_metadata_reconciliation:167*

### Acceptance Checklist

- Done criterion: All Phase 1.5 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Later phases must depend on these contracts instead of duplicating cross-domain models.
- Done criterion: Contract tests and usage examples pass before Phase 2 implementation begins.
