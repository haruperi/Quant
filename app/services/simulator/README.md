# Simulator Service

The simulator service is the local-only execution foundation for Phase 8. The
current implementation is Sprint Pack 08A: models, request validation, journal
persistence, a deterministic engine shell, report builders, and an in-memory
execution-provider-compatible adapter. It does not produce official live broker
fills and does not call live trader execution code.

## Public Boundary

Use `run_backtest(payload, request_id=None)` as the official user-facing tool
boundary. It returns the standard HaruQuant tool envelope with `status`,
`message`, `data`, `error`, and `metadata`.

Raw arbitrary Python strategy code is rejected before execution. Strategy
requests must use a registered strategy reference and JSON-compatible
configuration. Code strings containing `def`, `class`, `import`, `exec`, `eval`,
or `__import__` return `SIM_ARBITRARY_CODE_REJECTED`.

## Configuration Reference

`SimulatorBacktestRequestV1` fields:

- `schema_version`: request schema, default `1.0.0`.
- `request_id`: trace id propagated to logs and envelopes.
- `actor_context`: `actor_id`, `roles`, and `auth_source`.
- `strategy_ref`: registered strategy identifier.
- `strategy_config`: JSON-compatible strategy parameters.
- `symbols`: non-empty symbol list.
- `timeframe`: bar timeframe label.
- `start`, `end`: UTC ISO date range; `start` must be before `end`.
- `initial_balance`: positive starting balance.
- `account_currency`: account reporting currency.
- `tick_model`, `spread_model`, `slippage_model`, `commission_model`,
  `swap_model`: selected model ids.
- `broker_profile_ref`: default `mt5_demo_reference_fx_v1`.
- `market_data_authority_ref`: data authority reference.
- `journal_persistence`: `memory` or `jsonl`.
- `artifact_root_ref`: optional allowlisted artifact root reference for later
  sprint packs.
- `realism_profile`: `research_approximation`, `mt5_parity_oriented`, or
  `production_realistic`.
- `metadata`: JSON-compatible namespaced metadata.

Core model classes:

- `FixedSpreadModel`: builds bid/ask ticks from a mid price and fixed points.
- `FixedSlippageModel`: applies adverse fixed-point slippage only to filled
  volume.
- `FixedLiquidityModel`: caps fillable volume and emits
  `SIM_IOC_REMAINDER_CANCELLED` for IOC remainders.
- `CommissionModel`: linear commission per filled lot.
- `SwapModel`: daily side-specific swap per lot.
- `MarginModel`: FX-style notional margin by leverage.

## Realism Labels

`research_approximation` means the result is suitable for local development and
contract validation only. 08A results intentionally disclose that no official
fills are produced.

`mt5_parity_oriented` is reserved for later sprint packs that implement tick
matching, order lifecycle, costs, and MT5 comparison tests.

`production_realistic` is reserved for owner-approved production-candidate runs.
A run cannot receive this label until required data quality, broker profile,
market-data authority, cost models, journal persistence, replayability,
currency conversion, and report disclosures are implemented and verified.

FX `production_realistic` V1 non-goals currently include broker last-look
behavior, broker bias, asymmetric slippage manipulation, news-event volatility
surface expansion, counterparty default risk, and broker solvency modelling.

## Journals And Reports

`DeterministicJournal` creates an append-only hash chain in memory.
`JsonlJournal` writes `journal.jsonl` and `journal_manifest.json` only when a
caller explicitly constructs it with an artifact directory. Importing the module
never writes files.

Every journal manifest records `run_id`, `config_hash`, `data_manifest_hash`,
`engine_version`, `schema_version`, artifact checksums, retention tier, last
sequence, and last record hash.

The journal exposes an async `append_async` boundary for later non-blocking
writer integration. Sprint packs 08B-08F must preserve deterministic state
transition order while moving durable I/O behind approved batching or writer
boundaries.

JSON reports are canonical machine-readable artifacts. Markdown reports are the
human-review format. 08A report helpers return strings and do not write files.

## Run Lifecycle And Control Statuses

`run_backtest` preserves the standard HaruQuant tool envelope at the top level:
`success` for accepted simulator lifecycle payloads and `error` for validation
or fail-closed boundary failures. Simulator-specific lifecycle state is reported
inside `data.status`.

Supported simulator lifecycle statuses are `success`, `failed`, `queued`,
`cancelled`, and `diagnostic_failed`. The local foundation currently returns:

- `success` after validation, registry checks, engine execution, metrics, and
  report-ready artifact metadata are complete.
- `queued` when local service-mode metadata indicates worker saturation. The
  payload includes a deterministic run id, queue position, bounded queue
  metadata, retry metadata, warnings, and no completed result.
- `cancelled` when cancellation is requested before execution. The payload
  includes a deterministic run id, cancellation diagnostics, and no completed
  result.
- `diagnostic_failed` when diagnostic mode stops before promotable execution.
  The payload includes bounded warnings and a non-promotable `SIM_*` error.

Checkpoint resume is not enabled yet. If a request attempts to resume from an
incompatible checkpoint, the orchestrator fails closed with
`SIM_CHECKPOINT_INCOMPATIBLE`.

## Data, Cache, And Vendor Governance

08A does not implement warm data cache, TTL handling, `DataManifestHash` cache
keys, feature-store retrieval, alternative-data as-of alignment, publication
lag, ingestion lag, or no-lookahead joins. Later sprint packs must implement
these before production promotion.

FX cross-rate synthesis is not implemented in 08A. Later work must reject
invalid or skewed cross-rate paths with `SIM_FX_CROSS_RATE_REJECTED` and enforce
`max_cross_rate_skew_bps`.

Third-party data and vendor governance must record source inventory ids,
license limitations, point-in-time snapshot ids, restatement policies, and
retention conflicts before external report export.

## Memory And Optimization Safety

Optimization, walk-forward, and Monte Carlo runs must stream journals rather
than materialize all events in memory. 08A defines the journal boundary but does
not enable those workloads. Later sprint packs must enforce bounded buffers,
backpressure, checkpointing, retry limits, poison-pill quarantine, and
recoverable failure artifacts.

## Migration Notes

Earlier repo tests referenced an in-memory `SimulatorClient` broker facade. 08A
preserves that compatibility while introducing `SimulatorExecutionProvider`,
which implements the canonical provider shape without calling live broker
execution code.

## Error And Diagnostic Codes

Implemented or surfaced in 08A:

- `SIM_ARBITRARY_CODE_REJECTED`
- `SIM_INVALID_DATE_RANGE`
- `SIM_INVALID_VOLUME`
- `SIM_DATA_EMPTY`
- `SIM_DATA_MISSING_COLUMN`
- `SIM_INVALID_PRICE`
- `SIM_DATA_NEGATIVE_SPREAD`
- `SIM_IOC_REMAINDER_CANCELLED`
- `SIM_CHECKPOINT_INCOMPATIBLE`
- `SIM_DATA_QUALITY_FAILED`
- `SIM_INVALID_CONFIG`
- `SIM_PERSISTENCE_FAILED`

## Executable Documentation

Run:

```powershell
python tests\usage\app\services\08_simulator.py
```

The usage script validates success and failure envelope shape, deterministic run
ids, model edge behavior, journal metadata, arbitrary-code rejection, report
generation, and fail-closed invalid input behavior.
