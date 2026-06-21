# Contract Governance Rules

This document defines the mandatory rules for all code that touches `app/contracts/`.
All domain modules, service layers, adapters, API handlers, and agent runtimes must
comply. Violations are blocking during code review.

---

## Rule 1 — Import canonical contracts; do not redefine cross-domain models

Domain modules (risk, trading, portfolio, simulation, live, analytics, research) must
import the shared canonical contracts from `app.contracts`. They must not define local
dataclasses, TypedDicts, or Pydantic models that duplicate fields already defined in a
canonical contract.

**Correct:**
```python
from app.contracts import StrategySignal, RiskDecision
```

**Violation:**
```python
# In risk/engine.py — forbidden
class LocalSignal(BaseModel):
    symbol: str
    side: str
    confidence: float
```

---

## Rule 2 — Adapt raw broker/exchange payloads before crossing service boundaries

Raw objects returned by broker SDKs (MT5, cTrader, Binance), exchange REST clients,
or WebSocket feeds must be adapted into canonical contracts at the integration boundary.
No raw SDK object may be passed to or returned from any service-layer function.

**Correct:**
```python
# In adapters/mt5/adapter.py
def execute_trade(self, request: TradeRequest) -> TradeResult:
    raw = mt5.order_send(...)         # raw MT5 object — stays inside adapter
    return _map_to_trade_result(raw)  # canonical contract crosses the boundary
```

**Violation:**
```python
# Forbidden — raw SDK object escapes the adapter
def execute_trade(self, request: TradeRequest) -> mt5.OrderSendResult:
    return mt5.order_send(...)
```

---

## Rule 3 — API DTOs wrap canonical contracts; they do not replace them

REST and GraphQL response schemas (FastAPI response models, Pydantic serializers) may
add presentation fields (pagination, hypermedia links, display labels) but must embed
the canonical contract as a nested field, not flatten or redefine its structure.

**Correct:**
```python
class TradeResultResponse(BaseModel):
    result: TradeResult   # canonical contract embedded
    _links: dict[str, str]
```

**Violation:**
```python
# Forbidden — fields copied and renamed
class TradeResultResponse(BaseModel):
    id: str           # was trade_id
    state: str        # was status
    broker_ref: str   # was execution_request_id
```

---

## Rule 4 — Conversation memory stores summaries and references, not raw payloads

Agent and LLM runtimes must not store full canonical contract payloads in conversation
memory or vector stores. They may store:
- The `content_hash()` of a contract for reference.
- A human-readable summary string.
- A URI or database key pointing to the persisted contract.

**Violation:**
```python
# Forbidden — full TradeResult stored in agent memory
memory.save(key="last_trade", value=trade_result.model_dump())
```

**Correct:**
```python
memory.save(key="last_trade_ref", value=trade_result.content_hash())
```

---

## Rule 5 — Compatibility review required before changing public contract fields

Any change to a canonical contract that modifies: a field name, a field type, a
`Literal` value set, a validator rule, a `schema_version` default, or the serialization
output of `to_json()` or `content_hash()` requires:

1. A bump to `schema_version` (patch for additive-only, minor for new required fields,
   major for removals or breaking type changes).
2. An entry in `CHANGELOG.md` under the new version.
3. A migration note if any persisted data or cached hashes must be invalidated.
4. Sign-off from the technical lead before merge.

---

## Rule 6 — Provider protocol implementations must not expose raw SDK types

Classes that implement `MarketDataProvider`, `ExecutionProvider`, `AccountProvider`,
`PositionProvider`, `OrderProvider`, `SymbolInfoProvider`, or `BrokerErrorMapper` must:
- Accept only canonical contract types as parameters.
- Return only canonical contract types from all public methods.
- Never expose raw broker SDK types, raw exchange payloads, or internal DB row objects
  in their public interface.

---

## Full Pipeline Flow Reference

The canonical data flow through the system is:

```
DataSlice  →  IndicatorResult  →  StrategySignal
    →  RiskDecision  →  OrderIntent  →  TradeRequest
    →  ExecutionProvider  →  TradeResult
    →  ExecutionJournal / TradeStore
    →  PortfolioSnapshot  →  AnalyticsReport
```

Each arrow represents a canonical contract boundary. No raw data may cross an arrow.
