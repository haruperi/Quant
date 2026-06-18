## Phase 7 Trading Service

### Goal

The Trader service layer provides the dedicated trading boundary for HaruQuantAI.

The module exposes a unified trading interface supporting MT5, cTrader, and Simulator providers through `app/routes/brokers.py`.

The Trader services own broker-compatible trading operations, validation, execution readiness checks, reconciliation support, and trading state retrieval while maintaining MQL5-compatible behavior where applicable.

Task inventory: 84 checkbox tasks (0 checked, all unchecked).

### Dependency Files and Functionality

Required files:

```text

app/utils/__init__.py

app/utils/errors.py

app/services/risk/__init__.py

app/services/risk/governor.py

app/services/analytics/__init__.py

```

Required functionality:

- Pre-trade risk governor limits check and sizing calculations are available.
- Analytics trade logging and equity reporting formats are accessible.
- Central errors, standard response wrapper, and trace identifiers exist.

### Files to Create

```text

app/services/trader/

app/routes/brokers.py

data/persistence

```

### Functionality to Implement

Tasks are grouped one source target at a time. Each requirement keeps its source line number from the phase requirements file for traceability.

#### `app/services/trader/executor.py`

Functions/classes:

- `TradeExecutor`
- `submit_market_order`
- `submit_pending_order`
- `modify_pending_order`
- `cancel_pending_order`
- `close_position`
- `modify_stops`

Requirements:

- [ ] Submit market orders.
- [ ] Submit pending orders.
- [ ] Modify pending orders.
- [ ] Cancel pending orders.
- [ ] Close positions fully or partially.
- [ ] Kill-Switch Behavior**: Under active kill-switch status, block all new trade requests, cancel all active pending orders immediately, and support a configurable option to flatten all open positions.
- [ ] Align order types precisely: Market, Limit, and Stop orders.
- [ ] Align trade request field naming to mirror MQL5 `MqlTradeRequest` structure.
- [ ] Implement fill policies (Fill or Kill, Immediate or Cancel, Return) mirroring MQL5's `CTrade` and `OrderSend` contracts.
- [ ] Correlation IDs**: All requests, responses, and events must propagate structural correlation, trace, and request IDs.
- [ ] Stop accepting new trade requests immediately.
- [ ] Cancel any locally tracked pending orders that have not been acknowledged by the broker.

#### `app/utils/validations.py`

Functions/classes:

- `TradeValidationResult`
- `validate_trade_request`
- `validate_symbol`
- `validate_volume`
- `validate_price`
- `validate_slippage`
- `validate_market_session`

Requirements:

- [ ] Modify stop-loss and take-profit levels.
- [ ] Return execution/fill details (filled volume, average price, remaining volume) in the result envelope.
- [ ] Validate slippage against a configurable tolerance, rejecting/warning if exceeded.
- [ ] Retrieve account dealing mode (Netting vs. Hedging) and cache it.
- [ ] Retrieve symbol information.
- [ ] Validate symbols.
- [ ] Validate trade volumes.
- [ ] Validate prices.
- [ ] Validate stop-loss and take-profit geometry.
- [ ] Validate margin requirements.
- [ ] Validate order requests against malicious payloads and out-of-bound arguments.
- [ ] Validate expiration values.
- [ ] Validate broker constraints.
- [ ] Dealing Mode Check**: Validate that position modification and closure requests are compatible with the cached account dealing mode (Netting vs. Hedging).
- [ ] Market Session Check**: Validate that the requested action is allowed during current active market sessions (e.g., prevent new positions during weekend rollover, even if connected).
- [ ] Decimal & Precision Normalization**: Ensure that all financial values (price, volume, SL/TP) are parsed into high-precision decimal objects and rounded/truncated according to the broker's specific digits and volume step parameters before routing.
- [ ] Validate broker connectivity.
- [ ] Validate market availability.
- [ ] Validate account permissions.
- [ ] Validate account readiness.
- [ ] Validate margin availability.
- [ ] Aggregate readiness checks before execution.
- [ ] Idempotency Key Scope**: Compute idempotency keys using a hash of specific request attributes: `(account_id, symbol, action_type, volume, price, slippage, timestamp_window)`.
- [ ] Verify rate limit health as part of the execution readiness checks.
- [ ] Fail-Closed**: Trading operations shall fail closed on invalid readiness conditions, active kill-switch status, or if the startup reconciliation gate is blocked.
- [ ] Serialized Execution**: Trading requests within the same `(account, symbol)` scope must be executed sequentially (e.g., serialized via an async lock or queue) to prevent interleaved state modification.
- [ ] Parameter Sanitization**: All broker-bound parameters must be strictly typed, sanitized, and validated before leaving the trading boundary.
- [ ] Contract Tests**: Validate the broker adapter interface against actual broker API behaviors to catch breaking upstream changes.

#### `app/services/trader/reporting.py`

Functions/classes:

- `ExecutionQualityReport`
- `TradingReport`
- `record_trading_metric`
- `emit_trading_alert`

Requirements:

- [ ] Partial Fill Strategy**: Return partial fill details directly to the Strategy/Risk caller rather than auto-chasing, with configurable behavior support.
- [ ] Generate trading reports.
- [ ] Include validation warnings.
- [ ] Alerting Rules**:
- [ ] Telemetry**: Propagate trace context through broker calls if supported by the provider SDK.
- [ ] Redaction**: Secrets, credentials, and API tokens must be redacted and never leaked to logs, error messages, or telemetry.

#### `app/services/trader/reconciliation.py`

Functions/classes:

- `ReconciliationResult`
- `compare_trade_state`
- `reconcile_orders`
- `reconcile_positions`
- `startup_reconciliation_gate`

Requirements:

- [ ] Retrieve account information.
- [ ] Retrieve position information.
- [ ] Retrieve pending order information.
- [ ] Retrieve historical order information.
- [ ] Retrieve historical deal information.
- [ ] Retrieve terminal information.
- [ ] Detect missing records.
- [ ] Detect mismatched records.
- [ ] Prevent unsafe retries after "unknown outcome" errors.
- [ ] Run scheduled reconciliation at configurable intervals (e.g., every N minutes).
- [ ] Trigger reconciliation on startup and immediately following any "unknown outcome" broker error.
- [ ] Support a flag that blocks trading execution until the initial reconciliation pass completes successfully.
- [ ] Include reconciliation summaries.
- [ ] Startup Reconciliation Gate**: Trading execution must be blocked at startup until the initial reconciliation pass completes successfully.
- [ ] Explicit Timeout Definition**: Synchronous broker calls must enforce explicit timeout thresholds (e.g., 5 seconds). Any request exceeding this threshold must be classified as an Unknown Outcome, disable automatic retries, and trigger forced reconciliation.
- [ ] Trigger a P1 critical alert if reconciliation drift exceeds a configurable monetary amount or a percentage of account equity.
- [ ] Chaos Engineering**: Inject random broker disconnections and delayed adapter responses during E2E testing to verify circuit breaker and reconciliation resilience.

#### `app/services/trader/throttling.py`

Functions/classes:

- `ProviderRateLimiter`
- `ConcurrencyQueue`
- `check_rate_limit_health`
- `shutdown_trade_queue`

Requirements:

- [ ] Verify that the provider rate-limiting threshold has not been exceeded.
- [ ] Configure and enforce a per-provider rate limiter (token bucket algorithm) for each broker instance.
- [ ] Apply rate limits to all outbound API calls to prevent bans or IP blocking.
- [ ] Trigger warning logs and flags if rate limit capacity utilization exceeds 80% for more than 5 consecutive minutes.
- [ ] Shutdown Sequence**: When the service is shutting down or redeploying, it must:
- [ ] Allow in-flight requests to resolve within a configurable timeout window.

#### `app/services/trader/store.py`

Functions/classes:

- `TradeStore`
- `IdempotencyRecord`
- `generate_trade_request_id`
- `compute_idempotency_key`
- `detect_duplicate_request`

Requirements:

- [ ] Generate deterministic request identifiers.
- [ ] Detect duplicate requests using idempotency records.
- [ ] Reject conflicting duplicate requests.
- [ ] Enforce TTL (Time-To-Live) and lifecycle stages on idempotency keys.
- [ ] Handle concurrency collisions with "already in progress" responses to avoid race conditions.
- [ ] Compare internal state (via `TradeStore`) against broker state.
- [ ] Collision Protection**: Attempts to submit duplicate request IDs before the original is finalized must be rejected immediately.
- [ ] Metrics**: Track latency, failure rates, reconciliation drift, rate limit utilization, and idempotency hits.
- [ ] Flush final reconciliation states and active idempotency logs to the `TradeStore`.
- [ ] E2E Reconciliation & Idempotency Testing**: Implement specific test suites that inject network drops, simulate unknown outcomes, and verify correct recovery, deduplication, and reconciliation.

#### `app/utils/errors.py`

Functions/classes:

- `TradingError`
- `TradingTimeoutError`
- `UnknownOutcomeError`
- `classify_broker_error`

Requirements:

- [ ] Map error codes to standard codes that match MQL5 retcode behaviors (e.g., `TRADE_RETCODE_REQUOTE`, `TRADE_RETCODE_PRICE_OFF`).
- [ ] Error Classification**: Errors must be classified into transient vs. permanent types, mapped from broker-specific codes to a common internal set.
- [ ] Retry Policy**: Idempotent operations shall use a retry policy with exponential backoff and randomized jitter.
- [ ] Circuit Breaker**: Connections to broker adapters must be protected by circuit breakers to prevent cascading failures.

#### `app/services/trader/README.md`

Functions/classes:

- No runtime functions/classes; documentation artifact only.

Requirements:

- [ ] Simulator Integration**: Maintain high-fidelity integration tests using the local simulator adapter for deterministic regression validation.


### Hardening Amendments

#### Broker routing and execution provider boundary

Requirements:

- [ ] Move broker routing ownership out of `app/routes/` and into a service or integration boundary such as `app/services/brokers/router.py` or `app/integrations/brokers/`.
- [ ] Ensure API routes call governed services and never own broker resolution, execution decisions, risk decisions, or adapter selection policy.
- [ ] Adopt Phase 1.5 contracts for `BrokerCapabilities`, `ExecutionProvider`, `AccountProvider`, `PositionProvider`, `OrderProvider`, `SymbolInfoProvider`, `BrokerErrorMapper`, `TradeStore`, and `ExecutionJournal`.
- [ ] Ensure MT5, cTrader, Binance, simulator, paper, and shadow providers implement the same execution provider boundary where applicable.
- [ ] Ensure broker-specific errors map to deterministic internal execution error codes before leaving the integration boundary.
- [ ] Ensure raw broker order IDs are stored as provider metadata and never replace canonical trade, order, execution, fill, or idempotency IDs.
- [ ] Add tests proving the same service-layer caller can place a simulated, paper, or live-routed request by changing provider configuration only.

### Unit Tests Required

```text

tests/unit/app/services/trader/

```

Test coverage:

- Cover every requirement in this phase with normal, edge, invalid-input, fail-closed, logging, schema, and regression tests as applicable.
- Preserve the project gate of at least 80% coverage for each affected file and package.
- Verify standard envelopes, deterministic error codes, import behavior, and ownership boundaries.

### Usage Examples Required

```text

tests/usage/app/services/07_trading.py

```

Usage examples must show:

- `example_01_order_intent_creation`: Demonstrate deterministic order-intent creation from approved risk decisions.
- `example_02_order_validation`: Demonstrate symbol, price, volume, stop, freeze-level, and MQL5 compatibility validation.
- `example_03_idempotency_and_store`: Demonstrate idempotency keys, request packaging, duplicate handling, and store persistence.
- `example_04_simulator_route`: Demonstrate paper/simulation route behavior without live broker mutation.
- `example_05_reconciliation`: Demonstrate order, position, and receipt reconciliation plus mismatch reporting.
- `example_06_rate_limits_and_shutdown`: Demonstrate throttling, ordered queues, graceful shutdown, and recoverable errors.
- `example_07_execution_quality_reporting`: Demonstrate fill quality, slippage, partial-fill metadata, and structured receipts.
- `example_08_live_boundary`: Demonstrate that live mutation is blocked unless Live phase gates approve it.
- The single usage file must be runnable as a script and organize separate examples as focused functions.
- Examples must extensively cover the phase's official public capabilities, important edge cases, fail-closed paths, and standard envelope fields where applicable.

### Documentation and Logging Requirements

- Every created or changed Python module must have a file-level docstring describing purpose, exports, and side effects.
- Every public function/class must have a Google-style docstring with args, returns, and raised or structured errors.
- Log calls, validation failures, success, exception paths, and governed/fail-closed decisions with redacted metadata only.
- Update module README or active docs when architecture, API, data models, security, testing, or observability meaning changes.

### Acceptance Checklist

- Done criterion: All 84 checkbox tasks are implemented or explicitly deferred with a documented reason.
- Done criterion: Scope stayed within this phase and approved dependency surfaces.
- Done criterion: Public exports match the phase registry rules and do not expose unapproved helpers.
- Done criterion: Standard envelopes, metadata, request IDs, error codes, logging, and redaction rules are satisfied where applicable.
- Done criterion: Unit tests, usage examples, static typing, linting, formatting, and coverage gates pass.
- Done criterion: Active docs and changelog are updated for any implemented project meaning changes.
- Done criterion: Rollback path and implementation report are recorded before handoff.

### Commit Message

```text

feat(trading-service): implement trader service layer and order validation



- Integrate TradeStore for order, deal, and position persistence

- Build stop, freeze, pegged, stop-limit, and trailing stop order validators

- Setup Startup Reconciliation Gate and position state synchronizer

- Support netting/hedging compatibility and MQL5 execution model mapping

```
