## Phase 7 Trading Service

### Goal

The Trader service layer provides the dedicated trading boundary for HaruQuantAI.

The module exposes a unified trading interface supporting MT5, cTrader, and Simulator providers through `app/routes/brokers.py`.

The Trader services own broker-compatible trading operations, validation, execution readiness checks, reconciliation support, and trading state retrieval while maintaining MQL5-compatible behavior where applicable.

Task inventory: 91 checkbox tasks (75 checked, 16 unchecked).

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

- [X] Submit market orders. *app.services.trader.trade.Trade.buy:455*
- [X] Submit pending orders. *app.services.trader.trade.Trade.buy_limit:569*
- [X] Modify pending orders. *app.services.trader.trade.Trade.order_modify:916*
- [X] Cancel pending orders. *app.services.trader.trade.Trade.order_delete:945*
- [ ] Close positions fully or partially. *Pending: `Trade.position_close` supports full close only; no partial close volume parameter is implemented.*
- [X] Kill-Switch Behavior**: Under active kill-switch status, block all new trade requests, cancel all active pending orders immediately, and support a configurable option to flatten all open positions. *tests/unit/app/services/trader/test_trader.py:577*
- [X] Align order types precisely: Market, Limit, and Stop orders. *tests/unit/app/services/trader/test_trader.py:485*
- [X] Align trade request field naming to mirror MQL5 `MqlTradeRequest` structure. *app.services.trader.trade.Trade.buy:455*
- [X] Implement fill policies (Fill or Kill, Immediate or Cancel, Return) mirroring MQL5's `CTrade` and `OrderSend` contracts. *app.services.trader.trade.Trade.set_order_filling:63*
- [X] Correlation IDs**: All requests, responses, and events must propagate structural correlation, trace, and request IDs. *tests/unit/app/services/trader/test_trader.py:485*
- [X] Stop accepting new trade requests immediately. *tests/unit/app/services/trader/test_trader.py:564*
- [ ] Cancel any locally tracked pending orders that have not been acknowledged by the broker. *Pending: `TradeStore` has no active order delete/acknowledgement lifecycle API.*

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

- [X] Modify stop-loss and take-profit levels. *app.services.trader.trade.Trade.position_modify:876*
- [X] Return execution/fill details (filled volume, average price, remaining volume) in the result envelope. *app.services.trader.result.NormalizedTradeResult:13*
- [X] Validate slippage against a configurable tolerance, rejecting/warning if exceeded. *app.services.trader.validation.ValidationService.validate_slippage:202*
- [ ] Retrieve account dealing mode (Netting vs. Hedging) and cache it. *Pending: `AccountInfo.margin_mode()` retrieves the mode, but no cache/lifecycle invalidation is implemented.*
- [X] Retrieve symbol information. *app.services.trader.symbol_info.SymbolInfo:12*
- [X] Validate symbols. *app.services.trader.validation.ValidationService.validate_order_request:262*
- [X] Validate trade volumes. *app.services.trader.validation.ValidationService.validate_volume:42*
- [X] Validate prices. *app.services.trader.validation.ValidationService.validate_price:90*
- [X] Validate stop-loss and take-profit geometry. *app.services.trader.validation.ValidationService.validate_stops:116*
- [X] Validate margin requirements. *app.services.trader.validation.ValidationService.validate_margin:171*
- [X] Validate order requests against malicious payloads and out-of-bound arguments. *app.services.trader.validation.ValidationService.validate_order_request:262*
- [ ] Validate expiration values. *Pending: pending-order expiration is passed through without dedicated validation.*
- [X] Validate broker constraints. *app.services.trader.validation.ValidationService.validate_order_request:262*
- [ ] Dealing Mode Check**: Validate that position modification and closure requests are compatible with the cached account dealing mode (Netting vs. Hedging). *Pending: `ValidationService.validate_dealing_mode_compatibility` is present but does not enforce compatibility rules.*
- [X] Market Session Check**: Validate that the requested action is allowed during current active market sessions (e.g., prevent new positions during weekend rollover, even if connected). *app.services.trader.validation.ValidationService.validate_market_session:242*
- [X] Decimal & Precision Normalization**: Ensure that all financial values (price, volume, SL/TP) are parsed into high-precision decimal objects and rounded/truncated according to the broker's specific digits and volume step parameters before routing. *app.services.trader.validation.ValidationService.normalize_precision:21*
- [X] Validate broker connectivity. *app.services.trader.readiness.ReadinessService.run_execution_readiness_check:18*
- [X] Validate market availability. *app.services.trader.readiness.ReadinessService.run_execution_readiness_check:18*
- [X] Validate account permissions. *app.services.trader.readiness.ReadinessService.run_execution_readiness_check:18*
- [X] Validate account readiness. *app.services.trader.readiness.ReadinessService.run_execution_readiness_check:18*
- [X] Validate margin availability. *app.services.trader.validation.ValidationService.validate_margin:171*
- [X] Aggregate readiness checks before execution. *app.services.trader.readiness.ReadinessService.run_execution_readiness_check:18*
- [X] Idempotency Key Scope**: Compute idempotency keys using a hash of specific request attributes: `(account_id, symbol, action_type, volume, price, slippage, timestamp_window)`. *app.services.trader.idempotency.IdempotencyService.generate_key:27*
- [X] Verify rate limit health as part of the execution readiness checks. *app.services.trader.readiness.ReadinessService.run_execution_readiness_check:18*
- [X] Fail-Closed**: Trading operations shall fail closed on invalid readiness conditions, active kill-switch status, or if the startup reconciliation gate is blocked. *tests/unit/app/services/trader/test_trader.py:551*
- [X] Serialized Execution**: Trading requests within the same `(account, symbol)` scope must be executed sequentially (e.g., serialized via an async lock or queue) to prevent interleaved state modification. *app.services.trader.concurrency.ConcurrencyQueue.lock_sync:94*
- [X] Parameter Sanitization**: All broker-bound parameters must be strictly typed, sanitized, and validated before leaving the trading boundary. *app.services.trader.validation.ValidationService.validate_order_request:262*
- [ ] Contract Tests**: Validate the broker adapter interface against actual broker API behaviors to catch breaking upstream changes. *Pending: focused unit tests mock broker behavior; no provider contract test suite exercises actual adapter API behavior.*

#### `app/services/trader/reporting.py`

Functions/classes:

- `ExecutionQualityReport`
- `TradingReport`
- `record_trading_metric`
- `emit_trading_alert`

Requirements:

- [X] Partial Fill Strategy**: Return partial fill details directly to the Strategy/Risk caller rather than auto-chasing, with configurable behavior support. *app.services.trader.result.BrokerResponseNormalizer.normalize_response:74*
- [X] Generate trading reports. *app.services.trader.reporting.ReportingService.build_report:17*
- [X] Include validation warnings. *app.services.trader.reporting.ReportingService.build_report:17*
- [X] Alerting Rules**: *app.services.trader.reconciliation.ReconciliationService.reconcile:38*
- [X] Telemetry**: Propagate trace context through broker calls if supported by the provider SDK. *app.services.trader.trade.Trade._attach_trace_context:157*
- [X] Redaction**: Secrets, credentials, and API tokens must be redacted and never leaked to logs, error messages, or telemetry. *app.utils.errors.classify_broker_error:620*

#### `app/services/trader/reconciliation.py`

Functions/classes:

- `ReconciliationResult`
- `compare_trade_state`
- `reconcile_orders`
- `reconcile_positions`
- `startup_reconciliation_gate`

Requirements:

- [X] Retrieve account information. *app.services.trader.account_info.AccountInfo:12*
- [X] Retrieve position information. *app.services.trader.position_info.PositionInfo:11*
- [X] Retrieve pending order information. *app.services.trader.order_info.OrderInfo:11*
- [X] Retrieve historical order information. *app.services.trader.history_order_info.HistoryOrderInfo:11*
- [X] Retrieve historical deal information. *app.services.trader.deal_info.DealInfo:11*
- [X] Retrieve terminal information. *app.services.trader.terminal_info.TerminalInfo:11*
- [X] Detect missing records. *app.services.trader.reconciliation.ReconciliationService.reconcile:38*
- [X] Detect mismatched records. *app.services.trader.reconciliation.ReconciliationService.reconcile:38*
- [X] Prevent unsafe retries after "unknown outcome" errors. *app.services.trader.trade.Trade._send_request:174*
- [ ] Run scheduled reconciliation at configurable intervals (e.g., every N minutes). *Pending: reconciliation is invoked on startup/unknown outcome paths, but no scheduler integration exists.*
- [X] Trigger reconciliation on startup and immediately following any "unknown outcome" broker error. *app.services.trader.trade.Trade._send_request:174*
- [X] Support a flag that blocks trading execution until the initial reconciliation pass completes successfully. *app.services.trader.reconciliation.ReconciliationService.set_block_trading_on_startup:30*
- [X] Include reconciliation summaries. *app.services.trader.reconciliation.ReconciliationService.reconcile:38*
- [X] Startup Reconciliation Gate**: Trading execution must be blocked at startup until the initial reconciliation pass completes successfully. *app.services.trader.trade.Trade._send_request:174*
- [X] Explicit Timeout Definition**: Synchronous broker calls must enforce explicit timeout thresholds (e.g., 5 seconds). Any request exceeding this threshold must be classified as an Unknown Outcome, disable automatic retries, and trigger forced reconciliation. *app.services.trader.trade.Trade._send_request:174*
- [X] Trigger a P1 critical alert if reconciliation drift exceeds a configurable monetary amount or a percentage of account equity. *app.services.trader.reconciliation.ReconciliationService.reconcile:38*
- [ ] Chaos Engineering**: Inject random broker disconnections and delayed adapter responses during E2E testing to verify circuit breaker and reconciliation resilience. *Pending: no E2E chaos test suite exists for trader broker disconnections or delayed responses.*

#### `app/services/trader/throttling.py`

Functions/classes:

- `ProviderRateLimiter`
- `ConcurrencyQueue`
- `check_rate_limit_health`
- `shutdown_trade_queue`

Requirements:

- [X] Verify that the provider rate-limiting threshold has not been exceeded. *tests/unit/app/services/trader/test_trader.py:614*
- [X] Configure and enforce a per-provider rate limiter (token bucket algorithm) for each broker instance. *app.services.trader.rate_limiter.get_rate_limiter:99*
- [X] Apply rate limits to all outbound API calls to prevent bans or IP blocking. *app.services.trader.trade.Trade._send_request:174*
- [X] Trigger warning logs and flags if rate limit capacity utilization exceeds 80% for more than 5 consecutive minutes. *app.services.trader.rate_limiter.RateLimiter.acquire:48*
- [X] Shutdown Sequence**: When the service is shutting down or redeploying, it must: *tests/unit/app/services/trader/test_trader.py:564*
- [X] Allow in-flight requests to resolve within a configurable timeout window. *app.services.trader.trade.Trade.shutdown:1023*

#### `app/services/trader/store.py`

Functions/classes:

- `TradeStore`
- `IdempotencyRecord`
- `generate_trade_request_id`
- `compute_idempotency_key`
- `detect_duplicate_request`

Requirements:

- [X] Generate deterministic request identifiers. *app.services.trader.idempotency.IdempotencyService.generate_key:27*
- [X] Detect duplicate requests using idempotency records. *app.services.trader.idempotency.IdempotencyService.check_duplicate:57*
- [ ] Reject conflicting duplicate requests. *Pending: duplicate keys are blocked/cached, but conflicting payload comparison for the same explicit request ID is not implemented.*
- [X] Enforce TTL (Time-To-Live) and lifecycle stages on idempotency keys. *app.services.trader.idempotency.IdempotencyService.register_in_progress:68*
- [X] Handle concurrency collisions with "already in progress" responses to avoid race conditions. *app.services.trader.trade.Trade._send_request:174*
- [X] Compare internal state (via `TradeStore`) against broker state. *app.services.trader.reconciliation.ReconciliationService.reconcile:38*
- [X] Collision Protection**: Attempts to submit duplicate request IDs before the original is finalized must be rejected immediately. *app.services.trader.trade.Trade._send_request:174*
- [ ] Metrics**: Track latency, failure rates, reconciliation drift, rate limit utilization, and idempotency hits. *Pending: services expose some status fields/logs, but no unified trader metrics collector exists.*
- [X] Flush final reconciliation states and active idempotency logs to the `TradeStore`. *app.services.trader.trade.Trade.shutdown:1023*
- [ ] E2E Reconciliation & Idempotency Testing**: Implement specific test suites that inject network drops, simulate unknown outcomes, and verify correct recovery, deduplication, and reconciliation. *Pending: no E2E network-drop/unknown-outcome recovery suite exists.*

#### `app/utils/errors.py`

Functions/classes:

- `TradingError`
- `TradingTimeoutError`
- `UnknownOutcomeError`
- `classify_broker_error`

Requirements:

- [X] Map error codes to standard codes that match MQL5 retcode behaviors (e.g., `TRADE_RETCODE_REQUOTE`, `TRADE_RETCODE_PRICE_OFF`). *app.utils.errors.TRADING_RETCODE_ERROR_MAP:605*
- [X] Error Classification**: Errors must be classified into transient vs. permanent types, mapped from broker-specific codes to a common internal set. *tests/unit/app/services/trader/test_trader.py:633*
- [X] Retry Policy**: Idempotent operations shall use a retry policy with exponential backoff and randomized jitter. *app.utils.errors.trading_retry_delay:654*
- [ ] Circuit Breaker**: Connections to broker adapters must be protected by circuit breakers to prevent cascading failures. *Pending: data service has circuit-breaker utilities, but trader broker execution is not protected by a broker circuit breaker.*

#### `app/services/trader/README.md`

Functions/classes:

- No runtime functions/classes; documentation artifact only.

Requirements:

- [ ] Simulator Integration**: Maintain high-fidelity integration tests using the local simulator adapter for deterministic regression validation. *Pending: simulator routing has unit coverage, but no high-fidelity trader simulator integration test is present.*


### Hardening Amendments

#### Broker routing and execution provider boundary

Requirements:

- [X] Move broker routing ownership out of `app/routes/` and into a service or integration boundary such as `app/services/brokers/router.py` or `app/integrations/brokers/`. *app.services.brokers.router.get_broker_module:13*
- [X] Ensure API routes call governed services and never own broker resolution, execution decisions, risk decisions, or adapter selection policy. *app.routes.brokers.get_broker_module:13*
- [X] Adopt Phase 1.5 contracts for `BrokerCapabilities`, `ExecutionProvider`, `AccountProvider`, `PositionProvider`, `OrderProvider`, `SymbolInfoProvider`, `BrokerErrorMapper`, `TradeStore`, and `ExecutionJournal`. *app.contracts.providers.ExecutionProvider:31*
- [ ] Ensure MT5, cTrader, Binance, simulator, paper, and shadow providers implement the same execution provider boundary where applicable. *Pending: Phase 1.5 protocols exist, but these adapters are not all conformed to a shared execution provider boundary.*
- [X] Ensure broker-specific errors map to deterministic internal execution error codes before leaving the integration boundary. *app.utils.errors.classify_broker_error:620*
- [ ] Ensure raw broker order IDs are stored as provider metadata and never replace canonical trade, order, execution, fill, or idempotency IDs. *Pending: `TradeStore` currently keys orders/executions by raw broker tickets.*
- [ ] Add tests proving the same service-layer caller can place a simulated, paper, or live-routed request by changing provider configuration only. *Pending: tests cover mt5/simulator resolver behavior, but not paper/live-routed execution parity by configuration only.*

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
