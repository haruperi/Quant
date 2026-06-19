# Live Runtime Safety Gateway (`app/services/live/`)

The **Live Runtime Safety Gateway** module acts as a strict middleware gateway for live-route execution. It is responsible for live readiness checks, deterministic safety gates, session lifecycle management, active monitoring, state reconciliation against broker truth, and error mapping before order intent reaches the broker adapters.

---

## 1. Module Ownership Boundaries

* **OWNS**:
  * Live readiness validation, session lifecycle status, and active monitoring.
  * Evaluation of the 11-stage deterministic safety gate chain.
  * Internal-to-broker state reconciliation authority.
  * Live error taxonomy mapping and side-effect mode classification.
* **DOES NOT OWN**:
  * Broker adapter implementation or connection client credentials storage.
  * Market-data ingestion, feeds, or providers.
  * Strategy signal generation or lifecycle promotion rules.
  * Risk policy configuration or approval-policy rules.
  * WebSockets transport or user interface rendering.

---

## 2. End-to-End Workflow: Strategy to Live Execution

The pathway of an order is strictly governed, fail-closed, and traceable:

```mermaid
graph TD
    A["[Strategy] BaseStrategy"] -->|1. Emits Signal| B["[Risk] RiskGovernor"]
    B -->|2. Validates Limits & Signs Token| C["[Trading] Trade Service"]
    C -->|3. Packages OrderIntent & Token| D["[Live] Safety Gateway"]
    D -->|4. Runs 11-stage Gates & Reconciles| E["[Live] executor.py"]
    E -->|5. Calls Adapter (if mutation enabled)| F["[Brokers] MT5 / cTrader Adapter"]
    F -->|6. Receipt / Execution Result| G["[Live] Post-Event Audit & Reconciliation"]
```

### Step 1: Strategy Signal Generation
* Strategies (inheriting from `BaseStrategy`) run calculations and generate a standardized `Signal` payload.
* **Safety Gate**: Strategies are *decision-only* and are prohibited from directly placing broker orders.

### Step 2: Risk Governor Validation & Token Signing
* The signal is packaged as a `Proposal` and reviewed by the `RiskGovernor` via `run_risk_governor_checks`.
* The governor evaluates limits, correlation risk, margins, drawdown steps, and VaR/ES.
* If successful, it constructs a `RiskDecisionPackage` containing a cryptographically signed `RiskDecisionToken` (`policy_hash` bound).

### Step 3: Trading Order Intent Packaging
* The approved proposal is converted by the trading service into an idempotent `OrderIntent` payload.
* The intent carries mandatory audit metadata, including `request_id`, `correlation_id`, and the signed `approval_token`.

### Step 4: Live Safety Gates Check
* The order is received by `LiveTradeExecutor` (`executor.py`), which initiates the **11-Stage Gate Chain** in `gates.py`:
  1. **Live Enablement**: Checks if live mutations are configured and enabled (`live_enabled=True`).
  2. **Schema Validation**: Validates the structure and data types of the execution envelope.
  3. **Session Active**: Verifies a single active session exists and is not paused/stopped.
  4. **Approval Validation**: Checks the signature, expiration, and scope limits of the `RiskDecisionToken`.
  5. **Risk Decision Validation**: Verifies matching risk parameters.
  6. **Broker Readiness**: Verifies broker connectivity status and latency constraints.
  7. **Stale-Context Check**: Checks that symbol quote prices and account states are within staleness limits.
  8. **Idempotency Validation**: Ensures the request is not a duplicate.
  9. **Reconciliation Authority**: Asserts there are no unresolved position mismatches.
  10. **Kill Switch Validation**: Checks if global, strategy, or symbol kill switches are triggered.
  11. **Audit Pre-Recording**: Persists an audit record before sending to the broker (fails closed if persistence fails).

### Step 5: Live Execution
* If all gates pass and `live_mode` allows mutation, the request is dispatched to the active broker adapter via the broker connection client.
* If mutation is disabled (`live_mode="package_only"`), it returns a `packaged_only` envelope without touching the broker.

### Step 6: Post-Execution Reconciliation & Auditing
* Once the execution receipt is returned, `reconciliation.py` compares the internal position ledger against broker snapshots.
* If a mismatch is detected, the session is transitioned to `paused` and an incident is raised.

---

## 3. Platform Configuration & Setup

Configure broker parameters inside `app/utils/settings.py` (via environment variables or settings overrides):

```toml
# Main settings
active_broker = "mt5" # "mt5" | "ctrader" | "simulator"
live_enabled = false  # Must be explicitly true for live execution
live_mode = "package_only"  # "package_only" | "read_only" | "paper" | "shadow" | "micro_live" | "full_live"
```

### A. MetaTrader 5 (MT5) Integration

MT5 execution utilizes the MetaTrader5 SDK (native on Windows environments).

* **Configuration Settings**:
  * `mt5_enabled`: Set to `true`.
  * `mt5_login`: The integer login account ID (scrubbed on logs).
  * `mt5_password`: Secret reference to your MT5 account password (scanned and redacted).
  * `mt5_server`: The broker server address (e.g. `MetaQuotes-Demo`).
  * `mt5_terminal_path`: Optional path to the `terminal64.exe` executable.
  * `mt5_environment`: `"demo"` or `"live"`.

* **Execution Process**:
  * During startup reconciliation, the `MT5Client` initializes, establishes a socket connection, and selects the symbols configured in the system.
  * Price quote feeds are continuously checked; if clock drift or quote staleness exceeds `live_max_staleness_seconds`, execution gates block order placement.

---

### B. cTrader Integration

cTrader execution utilizes the Open API (FIX protocol or REST/WebSockets connection endpoints).

* **Configuration Settings**:
  * `ctrader_enabled`: Set to `true`.
  * `ctrader_client_id`: App Client ID registered in the Spotware Developer portal.
  * `ctrader_client_secret`: App Client Secret key.
  * `ctrader_access_token`: Access token generated during OAuth authentication.
  * `ctrader_refresh_token`: Refresh token used to keep the session alive.
  * `ctrader_redirect_url`: Redirect callback URL configured in Spotware.
  * `ctrader_environment`: `"demo"` or `"live"`.
  * `ctrader_account_id`: Integer trading account ID.

* **Execution Process**:
  * The cTrader connection adapter validates OAuth credentials and establishes a secure TLS connection.
  * Prior to any order mutation, the adapter verifies capabilities and checks symbol parameters (e.g., minimum lot size, step, slippage thresholds).

---

## 4. Usage Snippets

### Starting a Live Session
```python
from app.services.live import start_live_session
from app.utils.settings import Settings

settings = Settings(
    live_enabled=True,
    live_mode="micro_live",
    active_broker="mt5"
)

# Starts session and triggers startup reconciliation
session_status = start_live_session(config=settings)
print(f"Session state: {session_status.status}") # "active"
```

### Submitting a Governed Order
```python
from app.services.live import execute_live_order_intent

order_request = {
    "action": "submit_order",
    "symbol": "EURUSD",
    "volume": 0.1,
    "direction": "buy",
    "order_type": "market",
    "approval_token": "valid_signed_risk_decision_token", # signed by RiskGovernor
    "request_id": "req-101",
    "correlation_id": "corr-101"
}

result = execute_live_order_intent(order_request)
print(f"Status: {result['status']}") # "success"
print(f"Side Effect Mode: {result['side_effect_mode']}") # "broker_mutation_confirmed" / "packaged_only"
```

### Checking Monitoring & Health
```python
from app.services.live import check_live_readiness

health_snapshot = check_live_readiness()
print(f"Is Live Service Ready: {health_snapshot.is_ready}")
print(f"Active Blocks: {health_snapshot.readiness_blocks}") # e.g. ["COST_BUDGET_EXCEEDED"]
```

### Reconciliation State Run
```python
from app.services.live import reconcile_state

# Forces reconciliation of internal model positions against broker snapshot
recon_result = reconcile_state()
if recon_result.status == "mismatch":
    print(f"Mismatches detected: {recon_result.mismatched_items}")
```

---

## 5. Verification & Testing

* **Unit Tests**:
  Verify the full gate matrix, session lifecycle, and validation logic using target scope:
  ```bash
  pytest -o addopts="" tests/unit/app/services/live/ --cov=app/services/live --cov-report=term-missing --cov-fail-under=80
  ```
* **Executable Usage Examples**:
  Run the usage examples script to trace all 8 examples:
  ```bash
  $env:PYTHONUTF8=1; $env:PYTHONPATH="."; python tests/usage/app/services/10_live.py
  ```
