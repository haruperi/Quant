# 07 Trading Requirements (Revised)

## Purpose

The Trader service layer provides the dedicated trading boundary for HaruQuantAI.

The module exposes a unified trading interface supporting MT5, cTrader, and Simulator providers through `app/routes/brokers.py`.

The Trader services own broker-compatible trading operations, validation, execution readiness checks, reconciliation support, and trading state retrieval while maintaining MQL5-compatible behavior where applicable.

---

## State Management & Persistence Strategy

The trader layer owns reconciliation, idempotency, and internal trade state. While the trader layer **does not** own database schema ownership (which resides in the core data/persistence layer), it defines and relies on an explicit repository contract interface: **`TradeStore`**.

- **TradeStore Contract**: The services inside the trader layer interact exclusively with the `TradeStore` interface to persist and query:
  - Idempotency keys (along with their TTL and lifecycle states).
  - Local copy of active orders, open positions, and historical executions (deals) required for reconciliation.
  - Historical trading records for analytics and audit reporting.
- **Reconciliation Comparison**: The reconciliation service compares this local stored state (obtained via `TradeStore`) against the broker's live terminal/account state to identify and resolve discrepancies.

---

## Architecture Overview

``` text
app/
├── routes/
│   └── brokers.py
└── services/
    └── trader/
        ├── account_info.py
        ├── deal_info.py
        ├── history_order_info.py
        ├── order_info.py
        ├── position_info.py
        ├── symbol_info.py
        ├── terminal_info.py
        ├── trade.py
        ├── validation.py
        ├── readiness.py
        ├── result.py           # Includes BrokerResponseNormalizer
        ├── idempotency.py
        ├── reconciliation.py
        ├── reporting.py
        ├── store.py            # TradeStore interface
        ├── rate_limiter.py     # Rate limiter logic
        └── concurrency.py      # Concurrency and locking logic
```

## Class Diagram

``` mermaid
classDiagram

class BrokerRouter {
    +resolve_provider()
    +get_active_provider()
}

class TradeService {
    +submit_order()
    +modify_order()
    +cancel_order()
    +close_position()
    +modify_position()
}

class AccountInfoService {
    +get_account_info()
    +check_free_margin()
    +get_dealing_mode()
}

class SymbolInfoService {
    +get_symbol_info()
    +validate_symbol()
    +check_lot_rules()
}

class PositionInfoService {
    +get_positions()
}

class OrderInfoService {
    +get_orders()
}

class DealInfoService {
    +get_deals()
}

class TerminalInfoService {
    +check_connection()
    +check_market_open()
    +get_broker_time()
}

class ValidationService {
    +validate_order_request()
    +validate_volume()
    +validate_price()
    +validate_stops()
    +validate_margin()
    +validate_slippage()
    +validate_dealing_mode_compatibility()
    +validate_market_session()
}

class ReadinessService {
    +run_execution_readiness_check()
}

class ResultBuilder {
    +success()
    +failure()
}

class BrokerResponseNormalizer {
    +normalize_response()
}

class IdempotencyService {
    +generate_key()
    +detect_duplicates()
}

class ReconciliationService {
    +reconcile()
}

class ReportingService {
    +build_report()
}

class TradeStore {
    <<interface>>
    +get_order()
    +save_order()
    +get_position()
    +save_position()
    +get_execution()
    +save_execution()
    +get_idempotency_record()
    +save_idempotency_record()
}

class RateLimiter {
    +check_rate_limit()
    +acquire()
}

class ConcurrencyQueue {
    +acquire_lock()
    +release_lock()
}

class CircuitBreaker {
    +execute()
    +record_success()
    +record_failure()
}

TradeService --> BrokerRouter
TradeService --> ValidationService
TradeService --> ReadinessService
TradeService --> ResultBuilder
TradeService --> IdempotencyService
TradeService --> ReconciliationService
TradeService --> TradeStore
TradeService --> RateLimiter
TradeService --> ConcurrencyQueue
TradeService --> CircuitBreaker
TradeService --> BrokerResponseNormalizer

ValidationService --> SymbolInfoService
ReadinessService --> TerminalInfoService
ReadinessService --> AccountInfoService
IdempotencyService --> TradeStore
ReconciliationService --> TradeStore
ResultBuilder --> BrokerResponseNormalizer
```

---

## Owns

- Broker-agnostic trading operations through provider routing.
- MQL5-compatible trading interfaces and information retrieval.
- Account, symbol, position, order, deal, and terminal information services.
- Trade execution operations.
- Shared trading validation rules (including slippage, market session, and Netting/Hedging mode validation).
- Shared execution readiness checks (including rate-limiting and connection status checks).
- Standard trading result envelopes (containing partial fill and execution details).
- Broker response normalization (`BrokerResponseNormalizer`) to mask provider-specific quirks from the core service.
- Trading request packaging and sanitization.
- Trading idempotency support (via `TradeStore` tracking).
- Trading reconciliation support (using local `TradeStore` vs. broker state).
- Trading reporting support.
- Definition of the `TradeStore` interface.
- Concurrency ordering and locking logic (via `ConcurrencyQueue`).

## Does Not Own

- Strategy generation or approval workflows.
- Risk policy ownership.
- Portfolio allocation decisions.
- Kill-switch ownership (though it respects, queries, and acts upon the kill-switch state).
- Market data ingestion pipelines.
- Live runtime enablement.
- Secret management.
- Authentication and authorization.
- Database schema ownership or database engine implementations.
- Financial advice.

---

## Functional Requirements

### Trade Execution

- [x] Submit market orders.
- [x] Submit pending orders.
- [x] Modify pending orders.
- [x] Cancel pending orders.
- [x] Close positions fully or partially.
- [x] Modify stop-loss and take-profit levels.
- [x] Return execution/fill details (filled volume, average price, remaining volume) in the result envelope.
- [x] Validate slippage against a configurable tolerance, rejecting/warning if exceeded.
- [x] **Partial Fill Strategy**: Return partial fill details directly to the Strategy/Risk caller rather than auto-chasing, with configurable behavior support.
- [x] **Kill-Switch Behavior**: Under active kill-switch status, block all new trade requests, cancel all active pending orders immediately, and support a configurable option to flatten all open positions.

### Information Retrieval

- [x] Retrieve account information.
- [x] Retrieve account dealing mode (Netting vs. Hedging) and cache it.
- [x] Retrieve symbol information.
- [x] Retrieve position information.
- [x] Retrieve pending order information.
- [x] Retrieve historical order information.
- [x] Retrieve historical deal information.
- [x] Retrieve terminal information.

### Validation

- [x] Validate symbols.
- [x] Validate trade volumes.
- [x] Validate prices.
- [x] Validate stop-loss and take-profit geometry.
- [x] Validate margin requirements.
- [x] Validate order requests against malicious payloads and out-of-bound arguments.
- [x] Validate expiration values.
- [x] Validate broker constraints.
- [x] **Dealing Mode Check**: Validate that position modification and closure requests are compatible with the cached account dealing mode (Netting vs. Hedging).
- [x] **Market Session Check**: Validate that the requested action is allowed during current active market sessions (e.g., prevent new positions during weekend rollover, even if connected).
- [x] **Decimal & Precision Normalization**: Ensure that all financial values (price, volume, SL/TP) are parsed into high-precision decimal objects and rounded/truncated according to the broker's specific digits and volume step parameters before routing.

### Readiness

- [x] Validate broker connectivity.
- [x] Validate market availability.
- [x] Validate account permissions.
- [x] Validate account readiness.
- [x] Validate margin availability.
- [x] Verify that the provider rate-limiting threshold has not been exceeded.
- [x] Aggregate readiness checks before execution.

### Idempotency

- [x] Generate deterministic request identifiers.
- [x] **Idempotency Key Scope**: Compute idempotency keys using a hash of specific request attributes: `(account_id, symbol, action_type, volume, price, slippage, timestamp_window)`.
- [x] Detect duplicate requests using idempotency records.
- [x] Reject conflicting duplicate requests.
- [x] Enforce TTL (Time-To-Live) and lifecycle stages on idempotency keys.
- [x] Handle concurrency collisions with "already in progress" responses to avoid race conditions.

### Reconciliation

- [x] Compare internal state (via `TradeStore`) against broker state.
- [x] Detect missing records.
- [x] Detect mismatched records.
- [x] Prevent unsafe retries after "unknown outcome" errors.
- [x] Run scheduled reconciliation at configurable intervals (e.g., every N minutes).
- [x] Trigger reconciliation on startup and immediately following any "unknown outcome" broker error.
- [x] Support a flag that blocks trading execution until the initial reconciliation pass completes successfully.

### Rate Limiting & Throttling

- [x] Configure and enforce a per-provider rate limiter (token bucket algorithm) for each broker instance.
- [x] Apply rate limits to all outbound API calls to prevent bans or IP blocking.
- [x] Verify rate limit health as part of the execution readiness checks.

### MQL5-Compatibility Specifics

- [x] Align order types precisely: Market, Limit, and Stop orders.
- [x] Align trade request field naming to mirror MQL5 `MqlTradeRequest` structure.
- [x] Map error codes to standard codes that match MQL5 retcode behaviors (e.g., `TRADE_RETCODE_REQUOTE`, `TRADE_RETCODE_PRICE_OFF`).
- [x] Implement fill policies (Fill or Kill, Immediate or Cancel, Return) mirroring MQL5's `CTrade` and `OrderSend` contracts.

### Reporting

- [x] Generate trading reports.
- [x] Include reconciliation summaries.
- [x] Include validation warnings.

---

## Non-Functional Requirements

### Resilience & Error Handling
- [x] **Fail-Closed**: Trading operations shall fail closed on invalid readiness conditions, active kill-switch status, or if the startup reconciliation gate is blocked.
- [x] **Startup Reconciliation Gate**: Trading execution must be blocked at startup until the initial reconciliation pass completes successfully.
- [x] **Error Classification**: Errors must be classified into transient vs. permanent types, mapped from broker-specific codes to a common internal set.
- [x] **Retry Policy**: Idempotent operations shall use a retry policy with exponential backoff and randomized jitter.
- [x] **Circuit Breaker**: Connections to broker adapters must be protected by circuit breakers to prevent cascading failures.
- [x] **Explicit Timeout Definition**: Synchronous broker calls must enforce explicit timeout thresholds (e.g., 5 seconds). Any request exceeding this threshold must be classified as an Unknown Outcome, disable automatic retries, and trigger forced reconciliation.

### Concurrency & Ordering Guarantees
- [x] **Serialized Execution**: Trading requests within the same `(account, symbol)` scope must be executed sequentially (e.g., serialized via an async lock or queue) to prevent interleaved state modification.
- [x] **Collision Protection**: Attempts to submit duplicate request IDs before the original is finalized must be rejected immediately.

### Observability & Alerting Thresholds
- [x] **Correlation IDs**: All requests, responses, and events must propagate structural correlation, trace, and request IDs.
- [x] **Metrics**: Track latency, failure rates, reconciliation drift, rate limit utilization, and idempotency hits.
- [x] **Alerting Rules**:
  - [x] Trigger a P1 critical alert if reconciliation drift exceeds a configurable monetary amount or a percentage of account equity.
  - [x] Trigger warning logs and flags if rate limit capacity utilization exceeds 80% for more than 5 consecutive minutes.
- [x] **Telemetry**: Propagate trace context through broker calls if supported by the provider SDK.

### Graceful Shutdown Protocol
- [x] **Shutdown Sequence**: When the service is shutting down or redeploying, it must:
  1. [x] Stop accepting new trade requests immediately.
  2. [x] Allow in-flight requests to resolve within a configurable timeout window.
  3. [x] Cancel any locally tracked pending orders that have not been acknowledged by the broker.
  4. [x] Flush final reconciliation states and active idempotency logs to the `TradeStore`.

### Security
- [x] **Parameter Sanitization**: All broker-bound parameters must be strictly typed, sanitized, and validated before leaving the trading boundary.
- [x] **Redaction**: Secrets, credentials, and API tokens must be redacted and never leaked to logs, error messages, or telemetry.

### Testing Boundary & Chaos Engineering
- [x] **Simulator Integration**: Maintain high-fidelity integration tests using the local simulator adapter for deterministic regression validation.
- [x] **Contract Tests**: Validate the broker adapter interface against actual broker API behaviors to catch breaking upstream changes.
- [x] **E2E Reconciliation & Idempotency Testing**: Implement specific test suites that inject network drops, simulate unknown outcomes, and verify correct recovery, deduplication, and reconciliation.
- [x] **Chaos Engineering**: Inject random broker disconnections and delayed adapter responses during E2E testing to verify circuit breaker and reconciliation resilience.
