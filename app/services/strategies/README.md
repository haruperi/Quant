# Strategy Service

The Strategy Service implements side-effect-free decision generation for both vectorized (batch) and event-driven (ticks/bars) quantitative trading strategies.

## Retention Periods for Regulatory Inquiries
All strategy definitions, version manifests, configuration parameter hashes, run audits, and generated trade intents are stored in the audit journal and retained for **5 years** to satisfy compliance and regulatory inquiry requirements.

## Approved Input Modes for `run_backtest`
The following strategy input modes are approved:
1. **Vectorized Batch Mode**: Accepting a `pandas.DataFrame` of historical price bars and aligned calculated indicator matrices.
2. **Event-Driven Stateful Mode**: Triggered sequentially on individual `on_bar`, `on_tick`, and `on_fill_update` hook callback events.

## Rationales for Non-Implemented Requirements
All complex system capabilities that are out-of-scope for the Phase 4 core runtime carry the following rationales:
- **Multiprocessing Isolation (`MULTIPROCESS_ISOLATED`)**: *Future* - To be implemented during the scaling and parallel processing optimization phase.
- **Concept & Feature Drift Detection**: *Future* - Machine learning drift analysis is planned for subsequent Phase 11 ML integration.
- **Alternative Venue Routing (Dark Pools / VWAP / TWAP)**: *Future* - Execution algorithms and venue routing are deferred to Phase 10 execution and broker gateway integration.
- **Multiprocess Strategy Execution**: *Future* - Process isolation and serialization are deferred to later optimization stages.
- **Real-Time Spread & Book Participation**: *Future* - Order book Level 2/3 participation models are deferred to Phase 8 live execution integrations.
- **Automatic Regime Switch Calibration**: *Future* - Strategy parameters regime calibration is deferred to Phase 11 optimization.
- **Regulatory Jurisdiction Enforcement**: *Documentation Only / Future* - Compliance reporting constraints are deferred to regulatory reporting phase.
- **Market Closure Gap Safety**: *Future* - Market closure state handling is deferred to Phase 7 trading engine.
- **Canary A/B Testing Framework**: *Future* - Parallel deployment comparison is deferred to subsequent analytics integrations.
