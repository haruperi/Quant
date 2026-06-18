## Phase 1.5 Core Domain Contracts

### Goal

Define canonical cross-domain models and protocol contracts before Data, Indicators, Strategies, Risk, Trading, Simulation, Analytics, Optimization, Live, UI/API, Research, and Conversation implement incompatible duplicates.

Task inventory: calculated from the checkbox tasks in this section.

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

- [ ] Create `app/contracts/` as the canonical model boundary shared by all domain phases.
- [ ] Define a side-effect-free public registry in `app/contracts/__init__.py`.
- [ ] Ensure contract modules do not import broker SDKs, database clients, UI frameworks, LLM clients, or optional provider packages.
- [ ] Define a common contract base carrying `schema_version`, `created_at`, optional `request_id`, optional `workflow_id`, and optional `correlation_id` where applicable.
- [ ] Define deterministic serialization helpers for contract objects using JSON-safe values.
- [ ] Define deterministic contract hashing for reproducibility, caching, audit records, and evidence packs.
- [ ] Define contract compatibility rules based on major/minor schema versions.
- [ ] Define validation helpers that return deterministic errors through the Utils error model.
- [ ] Ensure all canonical contracts are typed, documented, and safe to import in test, CLI, API, and agent runtimes.
- [ ] During the first three approved sprint packs after Phase 1.5, canonical contracts shall be treated as stabilization-stage contracts that may accept owner-approved additive changes without forcing broad downstream rewrites.
- [ ] Every canonical contract that crosses service or provider boundaries shall include a JSON-safe `metadata: dict[str, Any]` escape hatch for broker-specific, provider-specific, phase-specific, or experimental fields that are not stable enough to become first-class contract fields.
- [ ] Contract metadata shall be namespaced by owning adapter, provider, phase, or feature area to prevent collisions and accidental promotion of ambiguous keys.
- [ ] Contract metadata shall preserve deterministic serialization, hashing policy, redaction policy, and schema-version compatibility behavior.

#### Market data contracts

Requirements:

- [ ] Define `Symbol` with canonical symbol, broker symbol, asset class, quote currency, base currency, precision, lot/tick metadata, and provider metadata where applicable.
- [ ] Define `Timeframe` with deterministic parsing, canonical names, duration metadata, and unsupported-timeframe validation.
- [ ] Define `Bar` with timestamp, open, high, low, close, optional volume, optional spread, symbol, timeframe, and source metadata.
- [ ] Define `Tick` with timestamp, bid, ask, last, volume, symbol, and source metadata.
- [ ] Define `Spread` with bid, ask, spread points, spread price, timestamp, symbol, and source metadata.
- [ ] Define `DataSlice` for bounded batches of bars, ticks, or records with source, retrieval, transformation, and quality metadata.
- [ ] Define canonical market-data error codes for unavailable symbols, unsupported timeframes, stale data, provider errors, and malformed payloads.
- [ ] Define raw-provider-data lineage fields: provider, provider_request_id, retrieved_at, normalized_at, transformation_hash, and source_hash.

#### Indicator and strategy contracts

Requirements:

- [ ] Define `IndicatorResult` with name, version, parameters, warmup period, input hash, output metadata, and deterministic result serialization.
- [ ] Define `StrategyInput` with market data references, indicator references, portfolio context, configuration, and timestamp boundaries.
- [ ] Define `StrategySignal` as the only allowed strategy-to-risk output contract.
- [ ] Ensure `StrategySignal` includes strategy ID, strategy version, parameter hash, symbol, side, confidence, validity window, reason, evidence references, and source data hash.
- [ ] Ensure strategy contracts cannot represent broker-specific order placement directly.
- [ ] Define strategy contract validation that rejects signals with missing symbol, invalid side, expired validity window, missing evidence where required, or broker-specific mutation fields.

#### Risk and execution contracts

Requirements:

- [ ] Define `RiskDecision` as the only allowed risk-to-execution approval or rejection contract.
- [ ] Define `RiskRejection` with deterministic code, severity, reason, violated limit, evidence, and remediation metadata.
- [ ] Define `PositionSizingResult` with requested size, approved size, sizing method, constraints applied, and risk contribution.
- [ ] Define `OrderIntent` as the canonical post-risk pre-execution request.
- [ ] Define `TradeRequest` as the canonical execution-layer request after all required risk and approval gates pass.
- [ ] Define `TradeResult` with accepted, rejected, pending, partially filled, filled, cancelled, expired, failed, and reconciled states.
- [ ] Define `ExecutionReport` and `Fill` contracts with broker-neutral execution status, fill price, quantity, commission, slippage, latency, provider IDs, and timestamps.
- [ ] Define `BrokerCapabilities` for supported order types, fill policies, asset classes, time-in-force options, margin mode, hedging/netting mode, and provider limits.
- [ ] Define provider protocols: `MarketDataProvider`, `ExecutionProvider`, `AccountProvider`, `PositionProvider`, `OrderProvider`, `SymbolInfoProvider`, and `BrokerErrorMapper`.
- [ ] Ensure provider protocols return canonical contracts and do not expose raw broker SDK objects outside integration boundaries.
- [ ] Broker-specific reconciliation fields discovered by Trading, Simulation, Paper, Shadow, or Live providers shall use canonical contract `metadata` until repeated cross-provider use justifies a first-class contract field.
- [ ] `TradeResult`, `ExecutionReport`, and `Fill` metadata shall support provider reconciliation references, broker ticket aliases, venue execution hints, and diagnostic adapter fields without changing service-layer callers.

#### Portfolio, simulation, analytics, optimization, live, and audit contracts

Requirements:

- [ ] Define `AccountSnapshot` with equity, balance, margin, free margin, currency, leverage, timestamp, and provider metadata.
- [ ] Define `Position` with symbol, side, quantity, average price, unrealized PnL, realized PnL, margin, provider IDs, and timestamps.
- [ ] Define `PortfolioSnapshot` with account, positions, pending exposure, risk budget, correlation metadata, and freshness metadata.
- [ ] Define `BacktestConfig` with dataset references, strategy references, cost model, fill model, calendar, split policy, and reproducibility seed.
- [ ] Define `BacktestResult` with run ID, config hash, journal reference, equity curve reference, metrics reference, and evidence metadata.
- [ ] Define `OptimizationCandidate` with strategy, parameters, score, robustness metrics, validation splits, overfitting checks, and evidence references.
- [ ] Define `LiveSessionState` with environment mode, provider status, risk status, kill-switch state, reconciliation status, and operator approval status.
- [ ] Define `AuditEvent` with event ID, event type, severity, actor, subject, action, evidence, redacted payload hash, and timestamp metadata.
- [ ] Define `KillSwitchState` and `RiskAuditEvent` contracts shared by Risk, Trading, Live, UI/API, and Conversation.
- [ ] Define `ExecutionJournal` and `TradeStore` protocol contracts for persisted orders, positions, executions, fills, idempotency keys, and reconciliation records.

#### Contract governance

Requirements:

- [ ] Add a rule that domain modules must import canonical contracts rather than redefining cross-domain models.
- [ ] Add a rule that raw broker SDK objects, raw exchange payloads, and UI DTOs must be adapted into canonical contracts before crossing service boundaries.
- [ ] Add a rule that API DTOs may wrap canonical contracts but may not replace domain contracts.
- [ ] Add a rule that conversation memory stores summaries and references, not raw sensitive canonical payloads.
- [ ] Add a compatibility review requirement before changing public contract names, fields, schema versions, or serialization behavior.
- [ ] Add a stabilization review rule for the first three sprint packs: metadata fields that become repeated, required, or cross-domain shall be reviewed for promotion into first-class contract fields with migration notes.
- [ ] Add a rule that metadata may not contain raw broker SDK objects, raw exchange payloads, credentials, unredacted account identifiers, or opaque objects that cannot serialize deterministically.
- [ ] Add a rule that downstream phases must tolerate unknown metadata keys by preserving or safely ignoring them unless a documented validation policy rejects the namespace.
- [ ] Add usage examples showing Data -> Indicator -> StrategySignal -> RiskDecision -> OrderIntent -> ExecutionProvider -> TradeResult -> Analytics flow.
- [ ] Add contract tests proving canonical contracts serialize deterministically and validate malformed inputs consistently.
- [ ] Add tests proving provider protocols can be implemented by simulator, MT5, cTrader, Binance, and paper/shadow adapters without changing service-layer callers.

### Unit Tests Required

```text
tests/unit/app/contracts/
```

Test coverage:

- [ ] Tests verify every contract imports without optional provider dependencies installed.
- [ ] Tests verify deterministic serialization, hashing, equality where applicable, and schema-version compatibility.
- [ ] Tests verify invalid required fields, unsupported states, invalid timestamps, invalid symbols, invalid sides, and malformed provider metadata fail deterministically.
- [ ] Tests verify provider protocols can be satisfied by fake adapters for market data, execution, account, position, order, and symbol info.
- [ ] Tests verify strategy contracts cannot encode direct broker mutation requests.
- [ ] Tests verify risk and execution contracts preserve correlation, request, workflow, idempotency, and audit identifiers.
- [ ] Tests verify namespaced metadata survives serialization, hashing, copying, and provider round-trips without exposing raw provider payloads.

### Usage Examples Required

```text
tests/usage/01_5_core_contracts.py
```

Usage examples must show:

- [ ] Example demonstrates canonical Bar and DataSlice construction from provider-like data.
- [ ] Example demonstrates IndicatorResult and StrategySignal creation with reproducibility metadata.
- [ ] Example demonstrates RiskDecision approving or rejecting an OrderIntent.
- [ ] Example demonstrates simulator and live providers sharing the same ExecutionProvider protocol.
- [ ] Example demonstrates TradeResult, ExecutionReport, Fill, PortfolioSnapshot, and BacktestResult serialization.
- [ ] Example demonstrates using metadata for a broker-specific reconciliation field and later reading it without changing the canonical service flow.

### Acceptance Checklist

- Done criterion: All Phase 1.5 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Later phases must depend on these contracts instead of duplicating cross-domain models.
- Done criterion: Contract tests and usage examples pass before Phase 2 implementation begins.
