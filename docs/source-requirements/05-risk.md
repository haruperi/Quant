# 05-risk.md - Requirements

## 1. Purpose

The `app/services/risk/` module exists to provide deterministic, production-grade risk governance for HaruQuant.

It converts portfolio, market, strategy, approval, and policy evidence into reproducible risk snapshots, sizing outputs, admission reviews, allocation reviews, scenario analyses, approval-token checks, kill-switch checks, and canonical `RiskDecisionPackage` results.

Its core purpose is to act as the safety gate between strategy intent and execution-sensitive workflows. It can approve, reject, block, request more evidence, or require approval according to deterministic policy, but it never places trades or mutates broker state.

The risk module is a deterministic policy engine with no trading authority.

Architectural axiom: In HaruQuant Risk, ambiguity is treated as a hard failure. If the system cannot prove an action is safe, it must block it.

Out of scope summary: Risk does not fetch market data, own long-term historical market data, place trades, mutate broker or execution state, render UI, or own portfolio, cost, incident, lifecycle, or broad reporting workflows.

### 1.1 Assumptions and resolved decisions

- [X] The target module path is `app/services/risk/`.
- [X] The source document is the production requirements baseline v8.0.
- [X] The implementation language is Python.
- [X] The module targets Python 3.12 or newer.
- [X] Public contracts use Pydantic V2; frozen dataclasses are limited to internal immutable calculation helpers.
- [X] Risk thresholds and profiles are config-driven and stored under `configs/risk/*.yaml`.
- [X] Integration dependencies are accessed through stable public interfaces.
- [X] Market data, portfolio state, execution state, governance state, and utility services are external domains.
- [X] `app.services.execution` may provide read-only open orders/positions but shall not be mutated by risk.
- [X] JSONL storage is permitted for local development and deterministic tests.
- [X] PostgreSQL is required for production live audit chains, approval-token state, token revocation state, and token consumption state.
- [X] Performance targets are measured in local deterministic mode with no remote broker/network calls unless otherwise specified.
- [X] Risk module production readiness is requirement-first: requirement -> contract -> deterministic implementation -> unit test -> workflow test -> audit evidence -> acceptance gate.
- [X] Governance remains externally owned by `app/services/governance` or an equivalent governance service exposed through stable public interfaces.
- [X] The production benchmark environment is `RISK_BENCHMARK_PROFILE_V1`.
- [X] If `RISK-PEND-001` is unresolved, live-sensitive pre-trade approval shall fail closed with `PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED` unless refreshed `PortfolioState` evidence includes pending orders or pending approvals.
- [X] If `RISK-PEND-003` is unresolved, live-sensitive `high_volatility` or `crisis` regime decisions that require stressed correlation, VaR, or CVaR shall return `needs_more_evidence` or `block` rather than falling back to ordinary lookbacks.
- [X] If `RISK-PEND-004` is unresolved, crisis-reference-dependent live decisions shall fail closed as missing evidence.
- [X] If `RISK-PEND-005` is unresolved, historical VaR shall remain the only production-live default and non-historical parametric VaR shall require explicit profile configuration plus approval.
- [X] If `RISK-PEND-006` is unresolved, Gaussian parametric VaR in production-live workflows shall return `needs_approval` or `block` according to profile and shall emit `PARAMETRIC_VAR_GAUSSIAN_WARNING`.
- [X] No safe fallback for a `RISK-PEND-*` item shall remain the permanent default for more than two sprint cycles without owner/architect review and a roadmap entry.
- [X] Source-confirmed production requirements are captured in this document unless explicitly marked Pending or Recommendation.
- [X] Recommendations remain non-mandatory until promoted by owner or architecture decision.
- [X] Future ambiguity shall be added as a new requirements decision item with owner, target section, and production-readiness impact instead of as an open-ended question.
- [X] Pending: confirm whether double-spend prevention is implemented inside Risk through a pending-approvals cache or enforced externally by Execution/Governance serialization.
- [X] Pending: confirm the exact default fractional Kelly multiplier value.
- [X] Pending: confirm the exact stressed-lookback policy for crisis correlation, VaR, and CVaR calculations.
- [X] Pending: confirm whether crisis-period references are configured profiles, evidence-pack inputs, or implementation fixtures.
- [X] Pending: confirm which heavy-tailed parametric VaR distribution is supported first.
- [X] Pending: confirm whether Gaussian parametric VaR is allowed in production-live workflows after warning or requires explicit waiver.
- [X] Recommendation: approval tokens should include a cryptographic nonce or single-use flag for all governed workflows, not only live-sensitive workflows.
- [X] Recommendation: token validation should record approval tokens as consumed in audit storage and reject consumed tokens on replay.
- [X] Recommendation: scenario analysis should include broker margin-call and stop-out stress tests using adverse price moves of two to three standard deviations.

### 1.2 Open Questions



## 2. Ownership

### 2.1 Owns

### 2.2 Does Not Own

## 3. Global API Contracts and Configuration

### 3.1 Public Capabilities Summary
- [X] Every exported symbol shall be classified as one of `official_ai_tool`, `public_python_contract`, `deterministic_service`, `internal_helper`, or `legacy_compatibility_export`.
- [X] Symbols not listed in `app.services.risk.__all__` shall be private implementation details and may change without compatibility guarantees.
- [X] Only symbols classified as `official_ai_tool` shall be agent-callable official risk tools.
- [X] Internal helpers shall not be agent-callable and shall not be included in the official AI tool registry.
- [X] Legacy compatibility exports shall document replacement guidance, stability, and deprecation status when they differ from canonical tool names.
- [X] Every official AI tool shall follow the HaruQuant AI Tool Function Standard.
- [X] Every official AI tool shall accept `request_id: Optional[str] = None`.
- [X] Every official AI tool shall return the standard HaruQuant tool response schema.
- [X] No official risk tool shall place trades, close trades, mutate broker state, or override execution controls.
- [X] Official AI tools shall call deterministic services rather than implementing risk logic inline.
- [X] Required official tool surface shall include:
- [X] `build_portfolio_risk_snapshot`
- [X] `review_trade_risk`
- [X] `calculate_position_size`
- [X] `assess_risk_regime`
- [X] `review_strategy_admission`
- [X] `review_allocation_proposal`
- [X] `create_risk_decision_package`
- [X] `validate_risk_approval_token`
- [X] `run_risk_scenario_analysis`
- [X] `generate_risk_report`
- [X] Current implementation traceability shall map the canonical official tool groups above to the present `app.services.risk.__all__` export surface without treating differently named but equivalent legacy requirements as separate behavior.
- [X] Current portfolio-state and portfolio-risk exports shall include `get_open_positions`, `get_open_orders`, `get_strategy_allocations`, `get_portfolio_equity_curve`, `calculate_portfolio_returns`, `calculate_portfolio_volatility`, `calculate_portfolio_correlation`, `calculate_portfolio_var`, `calculate_portfolio_cvar`, `calculate_risk_contribution`, `calculate_margin_usage`, `calculate_currency_exposure`, `detect_strategy_overlap`, `detect_symbol_cluster_risk`, and `build_portfolio_risk_snapshot`.
- [X] Current shared risk tool helpers shall include `risk_tool_result`, `risk_tool_context`, `risk_business_payload`, `risk_limit_check`, `risk_policy_module`, `risk_portfolio_module`, `risk_safety_module`, and `risk_live_module`, and shall remain support helpers rather than independent trading authority.
- [X] The current implementation support surface shall include risk request assembly through `RiskRequestAssemblyContext` and `assemble_risk_assessment_request`.
- [X] The current implementation support surface shall include threshold/config helpers through `load_risk_thresholds`, `config_version_hash`, `validate_threshold_schema`, and `validate_config_hash`.
- [X] The current implementation support surface shall include metric and scorecard contracts through `MetricRow`, `MetricContext`, `MetricFamily`, `RiskSnapshot`, `MetricRegistry`, `ScoreRow`, `ScoreContext`, `ScoreFamily`, `RiskScorecard`, `ScoreRegistry`, `RiskSnapshotEngine`, `RiskScorecardEngine`, and `RecommendationEngine`.
- [X] The current implementation support surface shall include decision, signature, approval, validity, and audit helpers through `compose_risk_decision`, `pack_risk_decision_rationale_and_provenance`, `create_approval_token`, `validate_approval_token`, `stable_hash`, `sign_payload`, `invalidate_for_material_proposal_change`, `enforce_risk_decision_expiry`, and `write_risk_audit`.
- [X] The current implementation support surface shall include reporting and persistence contracts for risk snapshots, scenario results, replay outputs, Markdown reports, JSON reports, decisions, snapshot bundles, and scenario stores.
- [X] Portfolio-under-risk compatibility shall treat `app.services.portfolio` and the `portfolio` tool category as compatibility adapters unless explicitly classified as risk-owned services.
- [X] Portfolio-under-risk compatibility adapters shall not own source-of-truth portfolio, execution, cost, incident, governance, or broad reporting state.
- [X] Each portfolio-under-risk compatibility adapter shall document its owning external domain, side effects, storage boundary, and failure behavior.
- [X] Portfolio-under-risk compatibility is transitional; the long-term target is a separate `app/services/portfolio` domain where Risk consumes read-only portfolio evidence and emits risk decisions through stable interfaces.
- [X] Portfolio-under-risk lazy service resolution shall raise `AttributeError` for unknown lazy service names.
- [X] Portfolio-under-risk compatibility shall preserve the method-level service surface for `propose`, `equal_capital`, `confidence_weighted`, `evaluate`, `trigger`, `resume`, `transition`, `audit`, `create_incident`, `report`, and `generate`.
- [X] Transitional compatibility facades shall emit deprecation warnings or deprecation metadata in public docs, tool metadata, or runtime diagnostics where applicable.
- [X] Transitional portfolio-under-risk facades shall be fully migrated to `app/services/portfolio` or explicitly reapproved by the owner/architect no later than v2.0.
- [X] Safe fallback compatibility facades shall not be treated as permanent architecture without owner/architect review.
- [X] `RiskConfig` / `RiskThresholds`
- [X] `PortfolioState`
- [X] `PortfolioRiskSnapshot`
- [X] `ProposedTrade`
- [X] `ProposedAllocation`
- [X] `RegimeAssessment`
- [X] `ScenarioResult`
- [X] `RiskDecisionPackage`
- [X] `RiskApprovalToken`
- [X] `RiskAuditRecord`
- [X] `RiskReport`
- [X] Shared helpers such as `risk_tool_result`, `risk_tool_context`, `risk_business_payload`, `risk_limit_check`, `risk_policy_module`, `risk_portfolio_module`, `risk_safety_module`, and `risk_live_module` shall remain support helpers and shall not be official AI tools.
- [X] Storage repositories, token-state backend clients, audit-chain internals, policy-resolution internals, and lazy service loaders shall not be agent-callable.
- [X] Private service internals shall not appear in `app.services.risk.__all__` unless they are intentionally classified, documented, tested, and reviewed for public import.

| Transitional surface | Classification | Target owner | Handoff requirement |
|---|---|---|---|
| Governor check exports | `deterministic_service` or `legacy_compatibility_export` | Risk | Map each export to a canonical official tool or private service before Builder handoff. |
| Portfolio state/risk exports | `public_python_contract` or `legacy_compatibility_export` | Risk plus external Portfolio/Data evidence owners | Document read-only evidence ownership and replacement path. |
| Allocation service facade | `legacy_compatibility_export` | Portfolio/Governance, with Risk constraints consumed through interfaces | Keep as compatibility facade until `app/services/portfolio` owns the service. |
| Cost service facade | `legacy_compatibility_export` | Cost/Observability | Keep out of core Risk ownership and document advisory/reporting behavior. |
| Incident service facade | `legacy_compatibility_export` | Incident/Governance | Keep out of core Risk ownership and document artifact/audit behavior. |
| Lifecycle service facade | `legacy_compatibility_export` | Strategy/Governance | Keep lifecycle execution external; Risk only supplies gate decisions. |
| Portfolio kill-switch facade | `legacy_compatibility_export` | Risk block state plus Execution/Governance enforcement | Risk emits block state; external authority mutates execution controls. |
| Portfolio audit/reporting facades | `legacy_compatibility_export` | Audit/Reporting | Keep broad reports external; Risk owns risk decision evidence and risk summaries. |

### 3.3 Configuration Defaults

## 4. Module Architecture

### 4.1 Target Folder Structure

```text
app/
    services/
        services/
                services/
                                risk/
                                    __init__.py
                                    models.py
                                    governor.py
                                    limits.py
                                    sizing.py
                                    lifecycle.py
                                    kill_switch.py
                                    scenarios.py
tests/
    unit/
        app/
            services/
                services/
                        services/
                                        risk/
                                            test_governor.py
                                            test_limits.py
                                            test_sizing.py
                                            test_kill_switch.py
    usage/
        app/
            services/
                05_risk.py```

### 4.2 Class Diagrams

```mermaid
classDiagram
    class RiskGovernor {
        +evaluate_proposal(proposal, state) RiskDecisionPackage
        +check_limits(state) list
    }
    class RiskDecisionPackage {
        +status: str
        +decision_id: str
        +rule_key: str
        +approval_token: str
    }
    class KillSwitchStateMachine {
        +state: str
        +trigger()
        +resume(approval_id)
    }
    RiskGovernor ..> RiskDecisionPackage : creates
    RiskGovernor --> KillSwitchStateMachine : checks
```

## 5. General / Cross-Cutting Non-Functional Requirements

- [X] The risk module shall define a canonical decision-state enum containing `approve`, `warn`, `needs_approval`, `needs_more_evidence`, `reject`, `block`, and `error`.
- [X] The risk module shall define a canonical limit-status enum containing `pass`, `warn`, `needs_more_evidence`, `fail`, and `blocked`.
- [X] The risk module shall define Decimal precision and rounding behavior for money, volume, lot size, pips, percentages, VaR, CVaR, margin, leverage, exposure, and allocation calculations.
- [X] Public Pydantic V2 model configuration shall set `allow_inf_nan=False` for public request, response, config, snapshot, decision, approval-token, audit, and tool contracts.
- [X] Public JSON serialization shall preserve Decimal precision through string or another documented exact JSON-safe representation and shall not silently convert Decimal values to binary floats.
- [X] The risk module shall expose a deterministic schema/version identifier for every public request and response contract.
- [X] Time-sensitive contracts and services shall accept an injected time provider or explicit `now` datetime for deterministic tests, scenario replay, and audit reproduction.
- [X] Official Risk tools shall not read local system time directly except through the approved time provider or shared Utils clock helper.
- [X] The risk module shall produce the same `RiskDecisionPackage` for the same inputs, configuration hash, and dependency versions.
- [X] All material decisions shall include enough metadata to reproduce the decision later.
- [X] Randomized scenario tests, if added, shall require explicit seeds and shall report the seed used.
- [X] Config changes shall create a new config hash visible in snapshots, decisions, approvals, and reports.
- [X] Pre-trade risk review latency for a normal portfolio shall complete within 100 ms p95 in local deterministic mode.
- [X] Snapshot generation for up to 500 open positions shall complete within 250 ms p95.
- [X] Markdown report generation from a completed decision package shall complete within 1 second p95.
- [X] Audit chain verification of 10,000 audit records shall complete within 2 seconds p95.
- [X] The module shall support at least 500 open positions in portfolio-level calculations.
- [X] The module shall support at least 100 strategies in allocation and concentration review.
- [X] The module shall support at least 5,000 historical return points for VaR/CVaR calculations.
- [X] The module shall avoid O(n³) algorithms in normal pre-trade paths unless explicitly justified.
- [X] Benchmark results shall report hardware, Python version, dependency versions, dataset size, and warm/cold cache state.
- [X] The module shall define maximum accepted payload sizes for public tools and return `PAYLOAD_TOO_LARGE` or `INVALID_INPUT` for oversized requests before expensive calculation begins.
- [X] Public official Risk tools shall reject payloads larger than 1 MiB by default unless an owner-approved profile sets a lower limit.
- [X] Public official Risk tools shall reject JSON payload nesting deeper than 10 levels by default before expensive validation or calculation begins.
- [X] Public official Risk tools shall reject arrays or lists with more than 10,000 items by default before expensive validation or calculation begins.
- [X] Normal pre-trade paths shall not exceed O(n^2) complexity over open positions and correlated symbols under supported portfolio sizes.
- [X] Non-critical reporting failures shall not silently hide risk decisions.
- [X] Audit write failure behavior shall be configurable.
- [X] Live-readiness workflows shall fail closed when audit persistence is mandatory and unavailable.
- [X] External dependency failure shall be represented as `needs_more_evidence`, `reject`, or `block`, never as silent success.
- [X] Exceptions shall be mapped to deterministic error codes, which must inherit and reuse exceptions from `app.utils.errors` to prevent duplicate declaration.
- [X] Failures shall not be swallowed.
- [X] The module shall define timeout behavior for governance, audit storage, token state backend, config loading, and evidence-provider calls.
- [X] The module shall define retry and retry-exhaustion behavior for idempotent persistence and validation operations.
- [X] Approval-token signing keys, secrets, broker credentials, and private account identifiers shall never be logged.
- [X] Approval tokens shall be tamper-evident using HMAC or stronger signing.
- [X] Risk tools shall declare accurate risk metadata and side-effect flags.
- [X] Internal helpers shall not be exposed as official AI tools unless intentionally promoted through `__all__`.
- [X] The module shall enforce least privilege: risk can approve or block readiness but cannot execute trades.
- [X] Every material risk decision shall emit structured logs with request id, workflow id, decision status, reason codes, and execution time.
- [X] Every material risk decision shall be serializable as an audit record.
- [X] Audit records shall include evidence references, config hash, input summary, limit results, approval state, and final decision.
- [X] Observability metrics shall include decision count, block count, reject count, approval-required count, latency, calculation failures, and missing-evidence events.
- [X] Logs and audit records shall redact secrets and sensitive account data.
- [X] Audit hash-chain verification shall complete before live-sensitive decisions when configured as mandatory.
- [X] Hash-chain generation shall use canonical serialization and a documented hash algorithm.
- [X] Audit-chain genesis behavior shall be deterministic and documented; genesis value shall not depend on random runtime state.
- [X] The module shall support Python 3.12 or newer.
- [X] The module shall use project logging and result conventions.
- [X] The module shall use Pydantic V2 for all public request, response, config, snapshot, decision, approval-token, audit, and tool contracts.
- [X] Frozen dataclasses may be used only for internal immutable calculation structures and shall not replace public Pydantic contracts.
- [X] The module shall avoid unnecessary heavy dependencies in deterministic pre-trade paths.
- [X] Public contracts shall be versioned when downstream workflows depend on them.
- [X] Each production file shall have a clear module-level docstring and public function/class docstrings.
- [X] Public functions shall have type hints.
- [X] Core functions shall remain small, focused, and testable.
- [X] Official AI tools shall not be added without tests, usage examples, metadata, and registry review.
- [X] Public interface changes shall be versioned, documented, and reviewed before downstream workflows depend on them.
- [X] `app.services.risk.__all__` shall remain the explicit current agent-facing export registry and shall be reviewed whenever current implementation exports diverge from canonical future tool names.
- [X] Portfolio-under-risk service classes shall be lazy-loaded so optional portfolio workflow dependencies do not break risk importability.
- [X] Portfolio-under-risk artifacts shall not contain secrets, credentials, broker passwords, API keys, or unredacted private data.
- [X] Portfolio-under-risk reports shall distinguish complete, incomplete, accepted, rejected, blocked, triggered, and approval-required states.
- [X] Concurrent risk decisions shall not share mutable request state, cached intermediate values, approval-token state, or audit buffers unless explicitly synchronized and tested.
- [X] Any cache used by the risk module shall be keyed by input evidence version, config hash, and dependency version and shall be safe for concurrent reads/writes.
- [X] Pre-trade risk review shall remain safe under concurrent strategy submissions using the same portfolio state.
- [X] Any pending-approval reservation cache used by the risk module shall be keyed by `workflow_id`, bounded by expiry, and synchronized for concurrent reads and writes.
- [X] Risk calculations for production live workflows shall prefer methods that reduce tail-risk underestimation.
- [X] VaR, CVaR, and correlation methods shall account for non-stationarity during high-volatility and crisis regimes.
- [X] Production live VaR behavior shall avoid Gaussian assumptions unless explicitly overridden and warning-tagged.
- [X] The module shall prevent LLM agents from approving live trading.
- [X] The module shall prevent approval tokens from authorizing mismatched subject/action scopes.
- [X] The module shall prevent stale, revoked, tampered, or expired approval tokens from validating.
- [X] The module shall prevent consumed approval tokens from validating for live-sensitive actions.
- [X] The module shall require nonce or single-use validation for live-sensitive approval tokens.
- [X] The module shall redact broker passwords, API keys, account passwords, private tokens, token signing keys, full account credentials, and raw private approval secrets from logs and audit records.
- [X] The module shall use HMAC or stronger signing for approval-token tamper evidence.
- [X] Audit hash chaining shall use SHA-256 or stronger and deterministic canonical JSON serialization.
- [X] The first audit-chain record shall use a documented genesis value; the default is 64 zeroes unless deployment config defines a different constant.
- [X] Live-sensitive workflows shall hard-fail when audit chain integrity is required and verification fails.
- [X] Risk tools shall never set `places_trade=True`.
- [X] The risk module shall enforce least privilege: readiness decisions only, no execution.

### 5.1 Other Global and Cross-Cutting Requirements

- [X] The risk module shall own portfolio risk state construction.
- [X] The risk module shall own portfolio exposure analysis.
- [X] The risk module shall own risk limit checks.
- [X] The risk module shall own strategy admission checks.
- [X] The risk module shall own pre-trade risk review.
- [X] The risk module shall own allocation review.
- [X] The risk module shall own portfolio-level risk decisions.
- [X] The risk module shall own approval-token creation and validation.
- [X] The risk module shall own risk audit records.
- [X] The risk module shall own risk report summaries.
- [X] The risk module shall own scenario and what-if analysis for risk review.
- [X] The risk module shall expose agent-safe risk tools.
- [X] The risk module shall not acquire market data directly.
- [X] The risk module shall not generate strategy signals.
- [X] The risk module shall not execute backtests.
- [X] The risk module shall not place broker orders.
- [X] The risk module shall not close positions.
- [X] The risk module shall not mutate live account state.
- [X] The risk module shall not render UI.
- [X] The risk module shall not allow LLM-based final approval.
- [X] The risk module shall not own database infrastructure outside its storage boundary.
- [X] The risk module shall emit execution-blocking decisions and risk-owned block state, but it shall not directly disable broker orders, cancel orders, close positions, or mutate execution controls.
- [X] The risk module shall not own or cache long-term historical market data; it shall consume point-in-time snapshots and bounded evidence packs from external evidence providers.
- [X] The risk module shall normalize raw account, equity, position, order, strategy, and symbol inputs into a canonical `PortfolioState`.
- [X] The risk module shall build a reproducible `RiskSnapshot` from `PortfolioState` and `RiskConfig` without mutating source inputs.
- [X] The risk module shall calculate account equity, balance, open risk, floating PnL, realized PnL, margin usage, free margin, and leverage when inputs are available.
- [X] The risk module shall explicitly mark unavailable snapshot fields as missing evidence rather than inventing defaults.
- [X] The risk module shall include `request_id`, `workflow_id`, `as_of`, `config_hash`, and evidence references in every material snapshot or decision package.
- [X] The risk module shall verify stored config hash compatibility before applying a previous decision or approval token; mismatches shall return `CONFIG_VERSION_MISMATCH` and require a new decision.
- [X] Pending orders shall be included in exposure, margin, leverage, concentration, and cluster-risk calculations according to the configured pending-order exposure policy.
- [X] Near-market pending orders shall be treated as potential exposure unless explicitly configured otherwise.
- [X] The risk module shall calculate exposure by symbol, strategy, currency, asset class, direction, and account-level aggregate.
- [X] The risk module shall calculate net and gross exposure separately.
- [X] The risk module shall detect currency-cluster and correlated-cluster exposure risks for FX portfolios.
- [X] The risk module shall support account-base-currency conversion when conversion rates are available.
- [X] The risk module shall block or request evidence when required FX conversion rates are unavailable for material decisions.
- [X] All monetary account-level risk metrics shall be expressed in account base currency.
- [X] Conversion assumptions shall appear in snapshot metadata and audit records.
- [X] Missing material conversion rates shall fail closed for live-readiness decisions.
- [X] The risk module shall calculate daily drawdown, total drawdown, peak-to-valley drawdown, and current drawdown state.
- [X] The risk module shall enforce configurable maximum daily loss, with default baseline of 5%.
- [X] Maximum daily loss percentage shall define its equity base explicitly in each risk profile; if the base is missing for live profiles, config validation shall return `INVALID_RISK_CONFIG`.
- [X] The risk module shall enforce configurable maximum total loss, with default baseline of 10%.
- [X] The risk module shall support configurable monthly profit target tracking, with default baseline of 10%.
- [X] Monthly profit target tracking shall define the reset calendar, account timezone, equity/balance base, inclusion of open PnL, and handling of deposits/withdrawals before production handoff.
- [X] The risk module shall detect best-day or consistency-rule risk when configured.
- [X] The risk module shall calculate margin required for current positions and proposed trades when contract size, leverage, price, and currency data are available.
- [X] The risk module shall calculate projected margin usage after a proposed trade.
- [X] The risk module shall fail closed when required broker symbol metadata is missing for live-readiness or pre-trade decisions.
- [X] The risk module shall calculate portfolio volatility using a deterministic method and documented lookback window.
- [X] The risk module shall calculate VaR at configurable confidence levels, with default baseline of 95%.
- [X] The risk module shall calculate CVaR / expected shortfall at configurable confidence levels.
- [X] The risk module shall support historical and parametric VaR methods when configured.
- [X] Historical VaR shall be the default VaR method for production live workflows unless an explicitly approved profile config selects another method.
- [X] If parametric VaR is used for production live workflows, it shall default to a heavy-tailed distribution.
- [X] If Gaussian parametric VaR is used, the decision or calculation result shall emit `PARAMETRIC_VAR_GAUSSIAN_WARNING`.
- [X] The risk module shall reject or request more evidence when return history is insufficient for configured VaR/CVaR requirements.
- [X] The minimum data points for VaR/CVaR sufficiency shall be explicit in each risk profile; missing production-live values shall return `INVALID_RISK_CONFIG`.
- [X] The risk module shall expose calculation assumptions in snapshot metadata, including lookback, confidence level, method, and data coverage.
- [X] The risk module shall calculate pairwise and portfolio-level correlation exposure for active positions and proposed trades.
- [X] The risk module shall evaluate proposed trades against the existing portfolio, not only against individual positions.
- [X] The risk module shall reject or warn when a proposed trade increases portfolio correlation above the configured threshold; the default FX baseline is 0.50.
- [X] The risk module shall handle missing or insufficient correlation data explicitly as missing evidence.
- [X] The risk module shall calculate incremental risk contribution when enough data exists.
- [X] The risk module shall accept spread, slippage, session, liquidity, and economic-calendar context as external evidence.
- [X] The risk module shall enforce high-impact-news blackout windows when calendar evidence is supplied; the default baseline is 10 minutes before and 10 minutes after high-impact events.
- [X] The risk module shall treat missing required news/calendar evidence according to configured mode: `ignore`, `warn`, `needs_more_evidence`, or `block`.
- [X] The risk module shall support weekend, overnight, and restricted-session rules when enabled.
- [X] Weekend, overnight, restricted-session, and news-blackout rules shall have a concrete configuration schema before Builder implementation.
- [X] The risk module shall use explicit timezone configuration for all session and calendar rules.
- [X] The risk module shall not compare naive and aware datetimes.
- [X] Timezone conversion failure shall fail closed for live workflows.
- [X] The risk module shall create tamper-evident approval tokens for approval-required decisions.
- [X] Approval tokens shall include request id, workflow id, approved action, approver, expiry, config hash, decision hash, scope, and nonce or single-use identifier.
- [X] Approval tokens shall expire deterministically and fail validation after expiry.
- [X] Approval tokens shall support revocation and fail validation after revocation.
- [X] Approval tokens shall be bound to the decision, account, strategy, symbol/action scope, and config hash they were created for.
- [X] The risk module shall reject approval reuse for materially different actions.
- [X] The risk module shall reject consumed approval tokens for live-sensitive actions, even if they are otherwise unexpired, correctly signed, and correctly scoped.
- [X] Approval-token consumption shall be persisted through the production token-state backend before a live-sensitive approval is treated as valid.
- [X] Approval-token compatibility across config changes shall fail closed unless an explicit governed compatibility policy authorizes the exact old config hash, new config hash, action scope, and expiry.
- [X] Emergency revocation shall be logged as a material governance event.
- [X] Token validation shall verify schema, signature, expiry, revocation, action type, scope, decision hash, config hash or approved config compatibility, nonce or single-use state, authorized approver, and required audit write.
- [X] The risk module shall run deterministic scenario and what-if analysis without changing live state.
- [X] The risk module shall generate human-readable Markdown risk reports from snapshots, decisions, and scenario outputs.
- [X] Risk reports shall separate evidence, calculations, assumptions, warnings, decisions, and recommendations.
- [X] Risk reports shall not claim live approval unless a valid approval token and risk decision exist.
- [X] The risk module shall calculate `RegimeAssessment` for portfolio snapshots when regime assessment is enabled.
- [X] The regime layer shall classify volatility, liquidity, correlation, drawdown, crisis, news, and session regimes.
- [X] The risk module shall support deterministic regime transitions with timestamp, previous regime, new regime, reason, and evidence references.
- [X] The risk module shall expose regime state in snapshots, risk reports, audit records, and decision packages.
- [X] The regime layer shall fail closed for live-sensitive workflows when required regime evidence is missing and policy requires it.
- [X] For live pre-trade review in `high_volatility` or `crisis` regimes, correlation calculations shall use stressed lookback evidence or configured stressed assumptions instead of the standard recent lookback.
- [X] For live pre-trade review in `high_volatility` or `crisis` regimes, VaR and CVaR calculations shall use stressed assumptions, stressed lookback evidence, or explicit crisis-period evidence.
- [X] Stressed lookback policy shall support configurable crisis references or maximum-observed-correlation style evidence over an approved historical window.
- [X] `PortfolioAuditService.audit` shall mark critical audit failure as disabling live trading when findings exist and severity is critical, and shall write an audit artifact.
- [X] `IncidentService.create_incident` shall create portfolio incident reports from supplied incident fields and write an incident audit artifact.
- [X] `CostService.report` shall aggregate cost by period, agent, provider, model, task, workflow, strategy, token usage, failed call cost, and backtest compute cost.
- [X] `ReportingService.generate` shall generate portfolio performance reports, mark reports incomplete when required fields or execution evidence are missing, include critical audit or risk findings in decision-required output, and write a performance report artifact.
- [X] The risk module shall calculate portfolio exit-liquidity stress for production live workflows and when otherwise enabled, including stressed VaR, stressed CVaR where available, stressed max drawdown, and market-impact assumptions.
- [X] The risk module shall apply graduated risk step-down controls before hard circuit breakers for production live workflows and when otherwise enabled.
- [X] The risk module shall validate live portfolio-state freshness for production live workflows and return `needs_more_evidence` or `block` when state is stale beyond configured tolerance.
- [X] The risk module shall support in-flight order tolerance buffers during live reconciliation for production live workflows and when otherwise enabled.
- [X] The risk module shall disclose `in_flight_tolerance_used` in decision metadata when used.
- [X] The audit layer shall support cryptographic hash chaining with `previous_hash` and `record_hash` for tamper-evident audit records, and production live workflows shall require audit-chain persistence.
- [X] Risk reports shall highlight `primary_failure_limit` first and list composite breach flags separately.
- [X] Missing risk configuration entirely shall return `INVALID_RISK_CONFIG` immediately.
- [X] Missing required field shall trigger invalid input, evidence request, warning, reject, or block according to workflow policy.
- [X] Wrong type shall trigger invalid input handling.
- [X] Negative price, equity, margin, volatility, or quantity shall be rejected where invalid.
- [X] Zero account equity shall be invalid for percentage risk calculations.
- [X] Impossible timestamps shall be rejected or blocked according to workflow policy.
- [X] Stale `as_of` timestamps shall trigger stale-evidence handling.
- [X] Timezone mismatch between broker-provided timestamps and the system-configured timezone shall trigger `INVALID_PORTFOLIO_STATE`.
- [X] Insufficient return history shall reject or request more evidence for VaR/CVaR.
- [X] Insufficient correlation overlap shall be handled explicitly as missing evidence or configured fallback.
- [X] Missing symbol metadata shall fail closed for live-readiness or pre-trade decisions.
- [X] Missing FX conversion rates shall fail closed for material live-readiness decisions.
- [X] Inconsistent account currency shall trigger data-quality failure.
- [X] Unsupported symbol or asset class shall trigger data-quality failure.
- [X] Duplicate position identifiers shall trigger data-quality failure.
- [X] Inconsistent position direction, quantity, or sign shall trigger data-quality failure.
- [X] Invalid approval-token scope shall fail token validation.
- [X] Insufficient ATR/volatility evidence shall emit `INSUFFICIENT_VOLATILITY_EVIDENCE`.
- [X] Insufficient Kelly trade sample evidence shall emit `INSUFFICIENT_K_EVIDENCE`.
- [X] Concurrent approval attempts that would overspend in-flight tolerance shall block or fail deterministically.
- [X] Parametric VaR configured with Gaussian assumptions shall emit `PARAMETRIC_VAR_GAUSSIAN_WARNING`.
- [X] Live pre-trade review in `high_volatility` or `crisis` regimes shall not silently use ordinary correlation, VaR, or CVaR lookbacks when stressed evidence is required.
- [X] Missing or ambiguous pending-order execution policy when pending orders exist shall trigger configured failure behavior.
- [X] Unknown regime state shall fail closed for live-sensitive workflows when configured.
- [X] Empty allocation strategy list shall return empty equal-capital allocation instead of dividing by zero.
- [X] Allocation confidence inputs that are missing or all zero shall not divide by zero.
- [X] Portfolio service lazy lookup for an unknown service name shall raise `AttributeError`.
- [X] Protected decision task routed to a non-deterministic model shall be flagged as a cost governance anomaly.
- [X] Performance report missing portfolio PnL, drawdown, trade count, audit evidence, or execution logs shall be marked incomplete.
- [X] Unreadable or corrupted persisted step-down state shall return `needs_more_evidence` or `block` for live-sensitive workflows according to config.
- [X] Audit-chain tamper detection shall emit `AUDIT_CHAIN_TAMPER_DETECTED`.
- [X] In-flight reconciliation grace-period expiry shall emit `IN_FLIGHT_RECONCILIATION_EXPIRED` and require forced portfolio-state refresh before live-sensitive decision.
- [X] Malformed JSON-like payloads shall return `INVALID_INPUT` through official AI tools.
- [X] Oversized payloads shall return `PAYLOAD_TOO_LARGE` or `INVALID_INPUT` before expensive calculation begins.
- [X] Maliciously deep JSON payloads or excessively large arrays, including more than 10,000 items in a single list, shall be rejected with `PAYLOAD_TOO_LARGE` before parsing or expensive validation.
- [X] Token-state backend unavailable during live-sensitive token validation shall fail closed.
- [X] Audit persistence partial write shall fail closed when audit persistence is mandatory.
- [X] Clock skew beyond configured tolerance shall trigger stale-evidence or token-validation failure.
- [X] Permission-denied responses from governance, audit, or token backends shall fail closed for live-sensitive workflows.
- [X] The risk module shall use deterministic error codes, including:
- [X] `INVALID_INPUT`
- [X] `INVALID_PORTFOLIO_STATE`
- [X] `INVALID_RISK_CONFIG`
- [X] `MISSING_EVIDENCE`
- [X] `STALE_EVIDENCE`
- [X] `LIMIT_FAILED`
- [X] `POLICY_BLOCKED`
- [X] `APPROVAL_REQUIRED`
- [X] `APPROVAL_TOKEN_INVALID`
- [X] `APPROVAL_TOKEN_EXPIRED`
- [X] `APPROVAL_TOKEN_REVOKED`
- [X] `APPROVAL_TOKEN_CONSUMED`
- [X] `CONFIG_VERSION_MISMATCH`
- [X] `CONFIG_COMPATIBILITY_NOT_APPROVED`
- [X] `PARAMETRIC_VAR_GAUSSIAN_WARNING`
- [X] `PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED`
- [X] `PAYLOAD_TOO_LARGE`
- [X] `MISSING_STOP_LOSS`
- [X] `INSUFFICIENT_VOLATILITY_EVIDENCE`
- [X] `INSUFFICIENT_K_EVIDENCE`
- [X] `LIVE_STATE_STALE`
- [X] `IN_FLIGHT_TOLERANCE_EXCEEDED`
- [X] `CALCULATION_FAILED`
- [X] `SNAPSHOT_BUILD_FAILED`
- [X] `REPORT_GENERATION_FAILED`
- [X] `STORAGE_ERROR`
- [X] `TOOL_EXECUTION_FAILED`
- [X] `UNKNOWN_ERROR`
- [X] Internal services may raise domain exceptions.
- [X] Official AI tools shall catch domain exceptions and return standard tool responses.
- [X] Unknown exceptions shall be logged and converted into `TOOL_EXECUTION_FAILED` or `UNKNOWN_ERROR`.
- [X] External dependency failures shall not result in silent success.
- [X] Double-spend detection shall not silently approve concurrent risk-increasing actions.
- [X] Gaussian parametric VaR shall not silently pass as normal production-live VaR behavior.
- [X] Zero-equity percentage-risk calculations shall not silently compute or default.
- [X] Unit tests shall exist for every non-trivial risk module file.
- [X] Contract tests shall validate all public contracts and invalid payloads.
- [X] Contract tests shall prove every official AI tool returns the standard envelope with `status`, `message`, `data`, `error`, and `metadata` on success.
- [X] Contract tests shall prove every official AI tool returns deterministic error envelopes for invalid input, missing evidence, hard block, approval required, domain exceptions, and tool execution failure.
- [X] Contract tests shall prove public contracts preserve Decimal precision during validation and JSON serialization without implicit float conversion.
- [X] Config tests shall cover loading, validation, hash stability, and config mismatch.
- [X] Calculator tests shall cover exposure, margin, drawdown, VaR, CVaR, volatility, and correlation.
- [X] Regime tests shall cover classification, transitions, missing evidence, and limit multipliers.
- [X] Regime tests shall prove stressed correlation lookback behavior is used in `high_volatility` or `crisis` regimes when required.
- [X] Regime tests shall prove stressed VaR/CVaR behavior is used in `high_volatility` or `crisis` regimes when required.
- [X] Limit tests shall cover pass, warn, fail, and block paths for every configured limit.
- [X] Approval tests shall cover nonce or single-use validation, consumed-token rejection, and config-compatibility rejection by default.
- [X] Approval tests shall prove unauthorized approvers cannot create or validate governed approval tokens.
- [X] Approval tests shall prove token-consumption write failure blocks live-sensitive validation.
- [X] Approval tests shall prove clock-skewed token expiry fails closed according to configured tolerance.
- [X] Tool-standard tests shall cover every exported AI tool.
- [X] Tool-standard tests shall verify every official AI tool has one success example and one failure example.
- [X] Export-registry tests shall verify `app.services.risk.__all__` exactly matches the expected current agent-facing tool surface until a versioned registry change is approved.
- [X] Documentation tests shall verify each risk file and top-level public member has a module or member docstring.
- [X] Usage tests shall verify every exported risk tool has a usage example or an explicit approved skip.
- [X] Failure tests shall cover missing evidence, stale evidence, dependency failure, and audit failure.
- [X] Security tests shall cover prompt override, token replay, secret logging, and permission bypass.
- [X] Edge-case hardening tests shall cover step-down startup/restore/reset, audit genesis, correlation fallback, deterministic limit order, and in-flight grace expiry.
- [X] Portfolio-under-risk tests shall cover lazy service loading, unknown lazy service names, and package import behavior.
- [X] Portfolio-under-risk tests shall cover `PortfolioAuditService.audit`, `IncidentService.create_incident`, `CostService.report`, and `ReportingService.generate`, including artifact references and missing-evidence behavior.
- [X] Profile fixture tests shall cover `prop_firm_default`, `paper`, and `live_conservative` default thresholds and documented overrides.
- [X] Traceability tests or review artifacts shall verify every business rule maps to an owning requirement before production promotion.
- [X] Performance tests shall prove oversized payload rejection happens before expensive calculations.
- [X] Payload parsing tests shall prove deeply nested, malformed, and excessively large JSON/list payloads are rejected efficiently without CPU exhaustion.
- [X] Performance tests shall cover cold-cache and warm-cache p95 latency when both cache states are supported.
- [X] Concurrency tests shall prove concurrent pre-trade requests cannot double-spend in-flight tolerance or pending approval capacity.
- [X] Concurrency tests shall prove pending-approval cache behavior is deterministic if implemented inside risk.
- [X] Workflow tests shall prove Execution/Governance serialization or state-refresh requirements are enforced if pending approval reservation is externalized.
- [X] Integration tests shall cover governance service unavailable during approval-required decisions.
- [X] Integration tests shall cover token-state backend unavailable during live-sensitive approval-token validation.
- [X] Integration tests shall cover audit persistence partial write when mandatory audit is enabled.
- [X] Integration tests shall cover the Execution/Governance serialization path when Risk does not own pending-approval reservations.
- [X] VaR/CVaR tests shall prove historical VaR is the production-live default.
- [X] VaR/CVaR tests shall prove parametric VaR defaults to a heavy-tailed distribution when used in production-live profiles.
- [X] VaR/CVaR tests shall prove Gaussian parametric VaR emits `PARAMETRIC_VAR_GAUSSIAN_WARNING`.
- [X] Error-code tests shall prove `PARAMETRIC_VAR_GAUSSIAN_WARNING` and `PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED` are included in deterministic error or warning handling.
- [X] Integration tests shall cover the current pipeline from portfolio state to risk snapshot, scorecard, recommendations, storage, and risk/scenario report generation.
- [X] Coverage shall remain above 80%, with higher practical coverage for core risk gates.
- [X] All FR and NFR requirements shall have implementation owners.
- [X] All FR and NFR requirements shall have test evidence or explicit deferral notes.
- [X] All official AI tools shall comply with the HaruQuant Tool Function Standard.
- [X] Regime assessment and transition tests shall pass.
- [X] Performance benchmarks shall be measured with hardware/reference-environment metadata.
- [X] Audit persistence behavior shall be verified.
- [X] Live execution shall remain outside the risk module.
- [X] Usage examples shall include one happy-path response envelope for a normal approved or warning-only advisory decision.
- [X] Usage examples shall include response examples for `approve`, `reject`, `block`, `needs_more_evidence`, `needs_approval`, and `error` states.
- [X] Before Builder handoff, every mandatory Risk requirement shall have a stable unique identifier.
- [X] Before Builder handoff, every official Risk tool shall have a public contract covering purpose, classification, stability, required inputs, optional inputs, output `data` schema, status values, error codes, warning codes, side-effect metadata, network behavior, persistence behavior, and success/failure examples.
- [X] Before Builder handoff, every pending production decision shall be resolved, explicitly deferred, or assigned an owner-approved safe default.
- [X] Builder handoff shall remain blocked while any `RISK-PEND-*` item is unresolved or not explicitly deferred by owner/architect approval.
- [X] No live-production Risk workflow shall depend on an unresolved `Pending:` production decision.
- [X] Before Builder handoff, the current checkbox inventory shall be converted into a numbered requirements catalogue with stable `RISK-FR-*`, `RISK-NFR-*`, `RISK-SEC-*`, `RISK-EDGE-*`, `RISK-TEST-*`, `RISK-DOC-*`, and `RISK-COMPAT-*` identifiers.
- [X] Forward references to source-only IDs such as `FR-096` through `FR-100` shall remain migration notes only until equivalent active `RISK-*` identifiers are assigned.
- [X] `README.md` shall explain risk module responsibilities.
- [X] Tool catalog shall document official tools.
- [X] Config documentation shall explain thresholds.
- [X] Config documentation shall identify `configs/risk/*.yaml` as the canonical risk config path and document `prop_firm_default`, `paper`, and `live_conservative` profiles.
- [X] Workflow documentation shall explain risk gates.
- [X] Workflow documentation shall explain concurrent pre-trade request behavior and the owner of double-spend prevention.
- [X] Workflow documentation shall state whether double-spend prevention is handled by an internal pending-approvals cache or by Execution/Governance serialization.
- [X] Error code documentation shall exist.
- [X] Error code documentation shall explain `PARAMETRIC_VAR_GAUSSIAN_WARNING` and `PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED`.
- [X] Component map shall document which file owns each risk capability.
- [X] A traceability table shall map each business rule to its owning FR, NFR, security, test, or documentation requirement.
- [X] Approval-token documentation shall define config-hash compatibility, default fail-closed behavior, nonce or single-use handling, token consumption, revocation, and replay rejection.
- [X] Benchmark documentation shall define `RISK_BENCHMARK_PROFILE_V1` and required benchmark manifest fields.
- [X] VaR documentation shall explain production-live VaR method defaults and parametric distribution assumptions.
- [X] Regime documentation shall explain stressed lookback behavior for `high_volatility` and `crisis` regimes.
- [X] Risk reports shall be available in Markdown and JSON-compatible dict formats.
- [X] Risk reports shall separate observed evidence, calculated metrics, limit results, assumptions, warnings, decisions, and approval requirements.
- [X] Risk decision reports shall include plain-language explanations for primary `reject` or `block` reasons.
- [X] Documentation review shall be complete before production promotion.
- [X] Portfolio workflow artifacts should have explicit retention, redaction, and artifact-write failure behavior before production use.
- [X] Portfolio service exposure should be reviewed whenever `app.services.portfolio.__all__` changes so lazy service exports and formal package exports remain intentionally aligned.
- [X] Institutional hardening requirements shall be canonically treated as `FR-096` through `FR-100`.
- [X] Duplicate source references to `FR-086` through `FR-091` shall be normalized during implementation planning and traceability review.
- [X] The official AI tool requirements shall use their own canonical tool-surface requirement group and shall not reuse institutional hardening IDs.
- [X] A requirements traceability table shall map each business rule to its owning FR, NFR, security, test, or documentation requirement before production promotion.
- [X] Risk thresholds and profiles shall be stored under `configs/risk/*.yaml`.
- [X] Production profile examples shall include `configs/risk/prop_firm_default.yaml`, `configs/risk/paper.yaml`, and `configs/risk/live_conservative.yaml`.
- [X] The module shall target Python 3.12 or newer.
- [X] Pydantic V2 shall be the standard implementation for public contracts.
- [X] Frozen dataclasses may be used internally for immutable performance-critical calculation steps when they do not replace public Pydantic contracts.
- [X] Default baselines such as 5% maximum daily loss, 10% maximum total loss, 10% monthly profit target tracking, 95% VaR, and 0.50 FX correlation threshold shall apply to `prop_firm_default` and `live_conservative` profiles.
- [X] The `paper` profile shall keep the same default thresholds unless a documented paper-only override is configured.
- [X] The `research` profile may relax, warn, or disable selected production baselines, but relaxed settings shall never be inherited by live workflows.
- [X] Acceptance fixtures shall exist for `prop_firm_default`, `paper`, and `live_conservative` profiles.
- [X] JSONL storage shall be permitted for local development and deterministic tests.
- [X] PostgreSQL shall be the mandatory durable production backend for live audit chains, approval-token state, token revocation state, and token consumption state.
- [X] Governance ownership shall remain in an external `app/services/governance` domain or governance service accessed through stable public interfaces; the risk module shall consume governance decisions and persist risk-owned audit facts through those interfaces without owning enterprise governance policy.
- [X] The production benchmark profile shall be `RISK_BENCHMARK_PROFILE_V1`: Python 3.12+, 8 vCPU minimum, 32 GB RAM minimum, NVMe SSD, release build settings, no debugger, and no unrelated heavy background workload.
- [X] Benchmark manifests shall record OS, CPU model, logical CPU count, RAM, storage type, Python version, dependency lock hash, git commit, dataset hash, warm/cold cache state, and benchmark profile id.
- [X] Approval tokens shall fail closed across config changes unless an explicit compatibility policy marks the old and new config hashes as equivalent for the same action scope.
- [X] Approval-token compatibility exceptions shall require authorized governance approval, bounded expiry, audit evidence, and deterministic compatibility metadata.
- [X] Approval tokens shall include a cryptographic nonce or single-use identifier.
- [X] Validated approval tokens for live-sensitive actions shall be marked consumed through the production token-state backend and shall not validate a second time.
- [X] Final risk gates shall be deterministic code decisions; LLM agents may explain, summarize, or recommend but shall not make final safety-critical decisions.
- [X] The module shall produce one canonical `RiskDecisionPackage` for approvals, rejections, warnings, and approval-required states.
- [X] Missing evidence, invalid state, missing approval, unclear policy, or calculation failure shall block or reject instead of guessing.
- [X] Risk may decide whether an action is allowed, blocked, or approval-required, but shall not place trades, close positions, mutate broker state, or override execution tools.
- [X] Risk shall advise and gate; Execution shall act.
- [X] Agents shall call official risk tools only; internal calculators and helpers shall remain private unless intentionally promoted.
- [X] Limit checks shall execute in a documented deterministic order.
- [X] Limit aggregation shall follow: `blocked > fail > needs_more_evidence > warn > pass`.
- [X] Approval shall be required for live trading requests, promotion to live candidate, risk budget increases, allocation increases beyond threshold, configured warning overrides, and high-risk or critical state transitions.
- [X] Allocation recommendations shall not be execution instructions.
- [X] Historical VaR shall be the production-live default.
- [X] Gaussian parametric VaR shall be warning-gated with `PARAMETRIC_VAR_GAUSSIAN_WARNING`.
- [X] Pre-trade approvals shall not be allowed to double-spend in-flight order tolerance.
- [X] Either Risk shall reserve pending approval capacity, or Execution/Governance shall serialize requests or update state before subsequent checks.
- [X] LLM Agent: may explain, summarize, or recommend, but shall not enforce final safety-critical gates.
- [X] Authorized Approver: may approve eligible approval-required actions through deterministic approval-token workflow.
- [X] Strategy/Research workflow user: may request advisory risk reviews and strategy admission checks.
- [X] Simulation/Paper/Live workflow caller: may request mode-specific risk decisions.
- [X] Execution layer: may consume readiness output from the risk module but must handle actual execution outside risk.
- [X] Execution/Governance layer: shall serialize pre-trade requests or update `PortfolioState` with pending orders when Risk does not own a pending-approval reservation cache.
- [X] Governance/audit service: may provide approval state, audit persistence, and policy metadata through stable public interfaces.
- [X] Risk Agent shall not approve live trading by itself.
- [X] Risk Agent shall not invent missing evidence.
- [X] Risk Agent shall not bypass approval tokens.
- [X] Agents shall not import internal calculators unless intentionally exposed as official tools.

## 6. Detailed Requirements by File

### File: app/__init__.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/__init__.py`.

#### Functional Requirements
- [X] `app/services/risk/__init__.py` shall expose only symbols intentionally classified as `official_ai_tool`, `public_python_contract`, `deterministic_service`, or `legacy_compatibility_export`.
- [X] `app/services/risk/__init__.py` shall use `__all__` as the strict public export registry.
- [X] Portfolio-under-risk compatibility shall preserve package-level traceability for `app.services.portfolio.__init__`, `app.services.portfolio.__all__`, and `app.services.portfolio.standard_tools` when portfolio remains exposed as a workflow-facing package under risk governance.
- [X] `ScenarioDefinition`
- [X] The risk module shall reject NaN, Infinity, non-finite Decimal values, and values outside configured numeric bounds for all public contracts.
- [X] Non-positive-semidefinite correlation matrices shall be detected and either sanitized through a documented deterministic method or rejected as a data-quality failure according to profile configuration.
- [X] The risk domain shall expose only approved official AI tools through `app/services/risk/__init__.py`.
- [X] Structured logs, metrics, and audit records shall include a `correlation_id` or `trace_id` propagated from the initial agent or API request through the risk decision and audit chain.
- [X] The root package initializer shall remain limited to import/export exposure and shall not contain business implementation.

#### Non-Functional & Security Requirements
- [X] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [X] NaN, Infinity, and non-finite Decimal values shall be rejected.
- [X] Contract tests shall prove public contracts reject NaN, Infinity, malformed payloads, unknown enum values, and out-of-range numeric values.
- [X] Correlation tests shall cover non-positive-semidefinite matrix handling, including deterministic sanitization or configured data-quality rejection.
- [X] Package-initializer tests shall verify `app.services.risk.__init__` has no business implementation beyond import/export exposure.
- [X] Portfolio-under-risk tests shall verify `app.services.portfolio.__init__` has no business implementation beyond package exposure, `app.services.portfolio.__all__` remains unique and aligned with the expected exported tool surface, and `app.services.portfolio.standard_tools` carries required tool documentation and envelope behavior.

### File: app/services/risk/__init__.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/risk/__init__.py`.

#### Functional Requirements
- [X] No file-specific functional requirements defined. Foundation properties apply.

#### Non-Functional & Security Requirements
- [X] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [X] No file-specific testing requirements defined.

### File: app/services/risk/models.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/risk/models.py`.

#### Functional Requirements
- [X] The risk module shall not train models.
- [X] `CostService.report` shall flag budget exceeded and protected decision types routed to non-deterministic models, require high-cost workflow approval when budget is exceeded, and write a cost audit artifact.

#### Non-Functional & Security Requirements
- [X] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [X] No file-specific testing requirements defined.

### File: app/services/risk/governor.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/risk/governor.py`.

#### Functional Requirements
- [X] `run_portfolio_risk_governor`
- [X] Current governor-check exports shall include `check_max_drawdown_limit`, `check_daily_loss_limit`, `check_strategy_loss_limit`, `check_portfolio_exposure_limit`, `check_symbol_exposure_limit`, `check_currency_exposure_limit`, `check_correlation_limit`, `check_var_limit`, `check_cvar_limit`, `check_leverage_limit`, `check_margin_limit`, `check_news_blackout`, `check_spread_limit`, `check_slippage_limit`, `check_trade_frequency_limit`, `check_kill_switch_state`, and `run_risk_governor_checks`.
- [X] The current implementation support surface shall include domain contracts for `RiskProposal`, `RiskApprovalToken`, `RiskGovernorDecision`, `RiskMemo`, `RiskAssessmentRequest`, `AccountState`, `MarketState`, `SymbolState`, `PositionState`, `PortfolioState`, `MarketSnapshot`, `AccountSnapshot`, and `PortfolioSnapshot`.
- [X] The current implementation support surface shall include policy and governance contracts through `RiskPolicy`, `CorrelationPreference`, `OverrideRecord`, `CircuitBreakerState`, `BudgetUtilization`, `GovernanceState`, `PolicyEngine`, `PolicyScope`, `PolicyVersion`, `PolicyBundle`, `PolicyEnforcementResult`, `PolicyResolutionQuery`, `PolicyResolver`, `RiskGovernor`, and `GovernanceEngine`.
- [X] The risk module shall review every proposed trade through a canonical `ProposedTrade` contract before execution.
- [X] The risk module shall return one canonical `RiskDecisionPackage` for each pre-trade review.
- [X] The risk module shall calculate projected exposure, margin, drawdown, VaR/CVaR, concentration, and correlation impact when evidence is available.
- [X] The risk module shall return `approve` only when all required hard limits pass and no unresolved blocking evidence exists.
- [X] The risk module shall return `reject` or `block` for hard-limit breaches, active kill-switch states, invalid input, or missing mandatory live-readiness evidence.
- [X] The risk module shall return `needs_more_evidence` when configured mandatory evidence is missing but the action is not automatically prohibited.
- [X] The risk module shall return `needs_approval` when a deterministic policy permits exception handling but requires approval.
- [X] The risk governor shall validate request, portfolio state, and risk configuration before evaluating risk.
- [X] The risk governor shall check kill switch before final approval.
- [X] The risk governor shall run required limit checks and missing/stale evidence checks.
- [X] The risk governor shall determine approval requirements and attach approval tokens only when policy permits.
- [X] The risk governor shall emit audit event metadata for material decisions.
- [X] The pre-trade risk workflow shall prevent concurrent double-spending of in-flight tolerance buffers when simultaneous requests use the same portfolio state.
- [X] The production architecture shall choose exactly one double-spend prevention owner before Builder handoff: Risk-owned pending-approval reservation cache or external Execution/Governance serialization.
- [X] The selected double-spend prevention owner shall be recorded in configuration and documentation.
- [X] If no double-spend prevention owner is configured for live workflows, pre-trade approval shall fail closed with `PENDING_APPROVAL_DOUBLE_SPEND_BLOCKED`.
- [X] If double-spend prevention is externalized, Execution/Governance shall update `PortfolioState` with pending orders or pending approvals before later risk checks.
- [X] The risk module shall reject or block simultaneous approvals that would collectively breach configured limits while relying on the same stale `PortfolioState`.
- [X] Pre-trade review output shall disclose whether pending approval capacity, in-flight tolerance, or external serialization evidence was used.
- [X] `LifecycleService.transition` shall require board approval and risk-governor compatibility for micro-live and live transitions.
- [X] Position sizing shall not approve trades; the governor shall review sized trades before they are approved, rejected, blocked, or marked approval-required.
- [X] `PortfolioKillSwitch.evaluate` shall trigger when critical audit failure, unavailable risk governor, unavailable audit logging, failed broker heartbeat, daily or weekly loss breach, account or strategy drawdown breach, spread spike, slippage spike, or repeated order failures are detected.
- [X] Scenario outputs shall be advisory unless passed through the canonical governor.
- [X] The Risk Governor shall consume `RegimeAssessment` before approving, warning, rejecting, or blocking proposed risk-increasing actions.
- [X] `PortfolioAuditService.audit` shall flag missing risk-governor approval, approval token/order mismatch, unauthorized risk threshold changes, skipped lifecycle stages, missing live strategy board approval, missing evidence refs, missing execution logs, missing broker responses, and hidden failed tool calls.
- [X] The risk governor shall downgrade decisions to `needs_approval`, `reject`, or `block` when portfolio exit-liquidity stress breaches configured limits.
- [X] The governor shall populate `primary_failure_limit` and `composite_breach_flags` in every material `RiskDecisionPackage`.
- [X] `run_portfolio_risk_governor`
- [X] Governor decision generation shall complete within 50 ms p95 after snapshot inputs are prepared.
- [X] Complex orchestration shall belong in services or the governor, not calculators.
- [X] Risk calculators, limit checks, sizing calculations, regime checks, and governor logic shall be stateless and thread-safe.
- [X] The governor shall not rely on unordered dictionaries, sets, filesystem discovery order, dynamic import order, or plugin discovery order for safety-critical limit sequencing.
- [X] Governor decision precedence shall follow: `block > error > reject > needs_more_evidence > needs_approval > warn > approve`.
- [X] Scenario outputs shall remain advisory unless passed through the governor.
- [X] Risk Agent: may request snapshots, ask for governor decisions, explain findings, summarize approval requirements, and package evidence for human review.
- [X] Risk Agent shall not override deterministic governor decisions.

#### Non-Functional & Security Requirements
- [X] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [X] `GOVERNOR_DECISION_FAILED`
- [X] Governor tests shall cover decision truth tables.
- [X] Portfolio-under-risk tests shall cover `LifecycleService.transition` across allowed transitions, invalid transitions, missing board approval, risk-governor incompatibility, missing strategy review evidence, and accepted transitions.
- [X] Governor truth-table tests shall pass.

### File: app/services/risk/limits.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/risk/limits.py`.

#### Functional Requirements
- [X] Recommendation: `RegimeAssessment` should output a configurable `risk_multiplier` that can scale position sizing and exposure limits when promoted by owner decision.
- [X] The current implementation support surface shall include validation contracts and validators through `ValidationIssue`, `ValidationSummary`, `validate_account_state`, `validate_market_states`, `validate_symbol_states`, `validate_position_states`, and `validate_risk_limits`.
- [X] The risk module shall detect symbol concentration breaches using configurable limits.
- [X] The risk module shall detect strategy concentration breaches using configurable limits.
- [X] The risk module shall enforce maximum margin utilization limits.
- [X] The risk module shall enforce maximum effective leverage limits.
- [X] The risk module shall enforce configurable maximum spread limits for pre-trade review.
- [X] The risk module shall enforce demotion, suspension, and retirement rules for strategies breaching risk limits.
- [X] The risk module shall clamp or reject position sizes that exceed broker constraints, configured risk, margin, leverage, concentration, or symbol limits.
- [X] The risk module shall validate allocation proposals against portfolio-level risk limits before approval.
- [X] The risk module shall apply stricter configured risk limits during high-risk regimes.
- [X] Agent-provided text shall never override deterministic policy, approvals, kill-switch state, or configured risk limits.
- [X] The module shall prevent LLM and agent prompt text from overriding deterministic policy, approvals, kill-switch state, or configured risk limits.
- [X] Composite breach tracking shall include all breached limits, but primary failure shall be selected from deterministic order after precedence is applied.

#### Non-Functional & Security Requirements
- [X] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [X] Concurrent pre-trade requests using the same stale `PortfolioState` shall not receive approvals that collectively breach configured risk limits.

### File: app/services/risk/sizing.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/risk/sizing.py`.

#### Functional Requirements
- [X] Institutional hardening blocks may be feature-flagged during implementation, but production live workflows require exit-liquidity stress, correlation-adjusted sizing, graduated step-down controls, live portfolio-state freshness checks, in-flight order tolerance enforcement, audit hash chaining, and composite breach reporting.
- [X] If `RISK-PEND-002` is unresolved, production Kelly sizing shall require `kelly_fraction_multiplier` in the active risk profile and shall return `INVALID_RISK_CONFIG` when it is missing.
- [X] The risk module shall own position sizing recommendations.
- [X] Current allocation and sizing exports shall include `calculate_fixed_fractional_size`, `calculate_volatility_adjusted_size`, `calculate_risk_parity_weights`, `calculate_correlation_adjusted_size`, `calculate_margin_aware_size`, `calculate_cost_adjusted_size`, `calculate_max_safe_position_size`, `propose_strategy_allocation`, `rebalance_strategy_allocations`, and `validate_allocation_proposal`.
- [X] The current implementation support surface shall include reusable calculation helpers for stop distance, pip value, proposed trade risk, notional exposure, risk/reward, VaR, CVaR, drawdown, exposure, concentration, margin, correlation, and position sizing.
- [X] `PositionSizingRequest`
- [X] `PositionSizingResult`
- [X] Raw calculators for stop distance, pip value, proposed trade risk, notional exposure, risk/reward, VaR, CVaR, drawdown, exposure, concentration, margin, correlation, and position sizing shall remain private or deterministic-service internals unless explicitly promoted.
- [X] Monetary and sizing calculations shall use `ROUND_HALF_EVEN` unless an approved risk profile explicitly documents a different deterministic rounding mode.
- [X] Public Pydantic V2 contracts shall use strict `Decimal` typing for monetary, sizing, margin, leverage, exposure, VaR, CVaR, and allocation fields and shall forbid implicit float casting for those fields.
- [X] The risk module shall calculate `fixed_lot` sizing using a configured lot size.
- [X] The risk module shall calculate `fixed_risk` sizing using fixed account risk percentage or fixed account risk amount.
- [X] The risk module shall calculate `milestone` sizing using deterministic account balance/equity milestone tables.
- [X] The risk module shall calculate conservative `kelly_criterion` sizing using validated win-rate/payoff evidence, configured caps, and a configurable minimum trade sample requirement.
- [X] Kelly sizing shall use default baseline `min_kelly_trades = 30`; insufficient samples shall emit `INSUFFICIENT_K_EVIDENCE`.
- [X] Production Kelly sizing shall apply fractional Kelly by default to account for estimation error in historical win-rate and payoff-ratio evidence.
- [X] Full Kelly sizing shall be prohibited by default and allowed only when an explicit documented risk waiver is supplied.
- [X] Kelly sizing output shall disclose the fractional Kelly multiplier applied and whether full Kelly was rejected, downgraded, or allowed by waiver.
- [X] The risk module shall calculate `volatility` sizing using ATR or volatility-adjusted stop distance.
- [X] The risk module shall calculate `fixed_fractional` sizing using configured capital fraction or notional allocation.
- [X] The `fixed_risk` sizing method shall calculate risk from distance to the provided stop-loss.
- [X] `ProposedTrade.stop_loss` shall be required and valid for `fixed_risk` sizing unless an approved sizing policy explicitly uses another stop-distance evidence field.
- [X] The risk module shall return a canonical `PositionSizingResult` for every sizing request.
- [X] The risk module shall support risk-parity-style allocation proposals for strategy baskets.
- [X] `AllocationService.propose` shall evaluate portfolio allocation proposals against available capital, stale allocation data, eligible lifecycle states, maximum strategy allocation, maximum symbol allocation, and maximum cluster allocation.
- [X] `AllocationService.propose` shall reject allocations that exceed capital, use ineligible lifecycle states, exceed strategy caps, exceed symbol concentration, exceed cluster concentration, or rely on stale allocation data.
- [X] `AllocationService.propose` shall accept valid allocations with a constraint report and board approval flag, and shall write an allocation audit artifact.
- [X] `AllocationService.equal_capital` shall split available capital equally across supplied strategy ids and return an empty allocation when no strategy ids are supplied.
- [X] `AllocationService.confidence_weighted` shall allocate capital in proportion to non-negative strategy confidence scores and avoid division by zero when confidence inputs are absent or all zero.
- [X] The position sizing engine shall support correlation-adjusted sizing for production live workflows and when otherwise enabled, using marginal correlation to open positions and configured penalty method.
- [X] Kelly sizing shall either reject insufficient evidence with `INSUFFICIENT_K_EVIDENCE` or, when configured, fall back to `fixed_risk` and emit `SIZING_FALLBACK_TO_FIXED_RISK`.
- [X] Position sizing for one standard sizing request with broker constraints shall complete within 25 ms p95.
- [X] Correlation-adjusted sizing for one request plus 100-symbol correlation context shall complete within 50 ms p95.
- [X] Sizing documentation shall explain the default fractional Kelly policy and risk-waiver requirement for full Kelly.
- [X] Production live workflows shall enable exit-liquidity stress, correlation-adjusted sizing, graduated step-down controls, live portfolio-state freshness checks, in-flight order tolerance enforcement, audit hash chaining, and composite breach reporting.
- [X] Per-trade sizing shall call `sizing.py`; allocation shall not duplicate sizing formulas.
- [X] Valid `PositionSizingResult` shall mean only that sizing calculated successfully, not that the trade is approved.
- [X] Production Kelly sizing shall be fractional by default.
- [X] Full Kelly sizing shall require an explicit documented risk waiver.

#### Non-Functional & Security Requirements
- [X] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [X] Missing stop-loss for fixed-risk sizing shall emit `MISSING_STOP_LOSS` when required.
- [X] Full Kelly sizing requested without a documented waiver shall be rejected or downgraded to fractional Kelly according to policy.
- [X] Stop-loss-dependent sizing shall not silently infer stop-loss distance when required evidence is absent.
- [X] Position sizing tests shall cover `fixed_lot`, `fixed_risk`, `milestone`, Kelly, volatility, and `fixed_fractional`.
- [X] Position sizing tests shall prove production Kelly sizing applies fractional Kelly by default.
- [X] Position sizing tests shall prove full Kelly requires a documented risk waiver.
- [X] Position sizing tests shall prove missing or invalid stop-loss for `fixed_risk` returns `MISSING_STOP_LOSS`.
- [X] Position sizing tests shall prove zero account equity returns `INVALID_PORTFOLIO_STATE` for percentage-risk calculations.
- [X] Workflow tests shall cover pre-trade, position sizing, regime assessment, strategy admission, allocation, and live-readiness.
- [X] Institutional hardening tests shall cover exit-liquidity stress, correlation-adjusted sizing, step-down state, live freshness, in-flight tolerance, audit chain, and composite failure.
- [X] Concurrency tests shall cover simultaneous risk decisions, simultaneous sizing calls, and cached read/write paths.
- [X] Position sizing methods shall have expected-value fixtures.

### File: app/services/risk/lifecycle.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/risk/lifecycle.py`.

#### Functional Requirements
- [X] The risk module shall not own portfolio management, cost aggregation, incident management, lifecycle execution logic, or broad reporting workflows.
- [X] Current strategy lifecycle and decision-package exports shall include `admit_strategy_to_portfolio`, `promote_strategy_to_paper`, `promote_strategy_to_live_candidate`, `suspend_strategy`, `retire_strategy`, `demote_strategy_to_paper`, `update_strategy_status`, and `build_risk_decision_package`.
- [X] `AllocationService`, `CostService`, `IncidentService`, `LifecycleService`, `PortfolioKillSwitch`, `PortfolioAuditService`, and `ReportingService` shall be documented as external compatibility facades and not core Risk-owned services unless a later owner decision explicitly reclassifies them.
- [X] Portfolio-under-risk compatibility shall include lazy service exposure through `__getattr__` for `AllocationService`, `CostService`, `IncidentService`, `PortfolioAuditService`, `PortfolioKillSwitch`, `LifecycleService`, and `ReportingService`.
- [X] The risk module shall review strategy admission using a canonical validation evidence package.
- [X] The risk module shall support the canonical lifecycle states `research`, `validated`, `paper_candidate`, `paper_active`, `live_candidate`, `live_active`, `suspended`, `retired`, and `rejected`.
- [X] The risk module shall normalize legacy lifecycle aliases to canonical lifecycle states only when the mapping is deterministic.
- [X] The risk module shall reject ambiguous lifecycle aliases with a deterministic data-quality failure.
- [X] The risk module shall enforce promotion gates before a strategy moves into paper or live eligibility.
- [X] The risk module shall not mark a strategy live-ready without evidence, risk decision, approval state, and kill-switch status.
- [X] `LifecycleService.transition` shall evaluate governed strategy lifecycle transitions against the allowed transition map.
- [X] `LifecycleService.transition` shall reject transitions that are not allowed by the lifecycle transition map.
- [X] `LifecycleService.transition` shall require strategy review evidence when transitioning to paper-live.
- [X] `LifecycleService.transition` shall write a lifecycle audit artifact.
- [X] A canonical glossary shall document decision states, lifecycle states, evidence states, workflow modes, and limit statuses.
- [X] Strategy lifecycle state names and board approval semantics should remain aligned between portfolio-under-risk workflows and the canonical risk governance glossary.
- [X] The canonical strategy lifecycle states shall be `research`, `validated`, `paper_candidate`, `paper_active`, `live_candidate`, `live_active`, `suspended`, `retired`, and `rejected`.
- [X] Legacy or source-only lifecycle aliases such as `draft`, `candidate`, `backtested`, `robustness_passed`, `paper`, `approved_for_live`, `live_approved`, and `live` shall be normalized to canonical lifecycle states or rejected when ambiguous.
- [X] The risk module documentation shall include a canonical glossary for decision states, lifecycle states, evidence states, workflow modes, and limit statuses.
- [X] Any important risk decision, approval token, kill-switch check, live-readiness decision, or strategy lifecycle change shall produce audit data.

#### Non-Functional & Security Requirements
- [X] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [X] Invalid strategy lifecycle state shall trigger data-quality failure.
- [X] Portfolio-under-risk tests shall cover `AllocationService.propose`, `AllocationService.equal_capital`, and `AllocationService.confidence_weighted` across accepted, rejected, stale, over-capital, ineligible lifecycle, strategy cap, symbol cap, cluster cap, empty strategy list, and zero-confidence cases.

### File: app/services/risk/kill_switch.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/risk/kill_switch.py`.

#### Functional Requirements
- [X] The risk module shall own kill-switch state checks.
- [X] `check_risk_kill_switch`
- [X] The current implementation support surface shall include kill-switch contracts through `KillSwitchStateMachine`, `KillSwitchService`, `evaluate_new_entry_block`, and `require_hard_trigger_recovery_dual_auth`.
- [X] `KillSwitchState`
- [X] Token expiry, stale evidence detection, kill-switch timeout handling, step-down expiry, audit ordering, and clock-skew checks shall use the injected time source where available.
- [X] The risk module shall classify portfolio drawdown state as normal, caution, restricted, blocked, or kill-switch-required according to configured thresholds.
- [X] Kill-switch activation shall revoke or invalidate outstanding approval tokens for affected global, account, strategy, or symbol scope.
- [X] The risk module shall check kill-switch state for live-readiness and execution-sensitive workflows.
- [X] Active kill switch shall force `block` for live-related decisions.
- [X] Unknown kill-switch state shall fail closed for live-related decisions.
- [X] LLM agents shall not be able to override kill-switch state through prompt text, tool arguments, or approval tokens.
- [X] The module shall support graduated risk step-down controls when enabled.
- [X] Step-down controls shall apply before hard circuit breakers.
- [X] Step-down controls shall never authorize a trade that would breach a hard risk limit.
- [X] Step-down state shall support deterministic initialization, restoration, reset, expiry, and corruption handling.
- [X] Live-sensitive workflows shall treat unreadable or corrupted persisted step-down state as `needs_more_evidence` or `block` according to config.
- [X] `PortfolioKillSwitch.evaluate` shall return current state when no trigger is active.
- [X] `PortfolioKillSwitch.trigger` shall set risk-owned kill-switch state to triggered, emit a deterministic block decision for new orders, require approval before resume, create incident details, and write a kill-switch audit artifact.
- [X] Any execution-control mutation required to disable new orders shall be performed only by Execution/Governance through its own authorized interface after consuming the risk-owned block state.
- [X] `PortfolioKillSwitch.resume` shall block resume without approval id and restore healthy state only when approval id is supplied.
- [X] Every risk decision report shall include a plain-language explanation for `reject` or `block`, referencing the specific limit, rule, missing evidence, approval failure, or kill-switch state.
- [X] `check_risk_kill_switch`
- [X] Safety-critical decisions shall fail closed on invalid input, missing mandatory evidence, unknown approval state, unknown kill-switch state, or calculation failure.
- [X] The module shall prevent LLM agents from overriding kill switch.
- [X] The module shall invalidate outstanding approvals affected by kill-switch activation.
- [X] Approval shall never be allowed for LLM kill-switch override, hidden live execution, broker action without execution gate, missing portfolio evidence, stale approval token, or mismatched subject/action token.
- [X] Active kill switch shall always block risk-increasing and live-related action.
- [X] Unknown kill switch shall fail closed for live-related actions.
- [X] Tolerance buffers shall never override kill-switch, max-total-loss, or prohibited-action rules.
- [X] Risk Agent shall not override kill switch.

#### Non-Functional & Security Requirements
- [X] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [X] `KILL_SWITCH_ACTIVE`
- [X] `KILL_SWITCH_UNKNOWN`
- [X] Safety-critical workflows shall fail closed on invalid input, missing evidence, unknown approval state, unknown kill-switch state, or calculation failure.
- [X] Approval tests shall cover creation, validation, expiry, revocation, emergency kill-switch revocation, mismatch, and tamper.
- [X] Time manipulation tests shall prove token expiry, stale evidence detection, kill-switch timeouts, step-down expiry, and clock-skew behavior remain deterministic with mocked or injected clocks.
- [X] Kill-switch tests shall cover active, inactive, unknown, and attempted override.
- [X] Portfolio-under-risk tests shall cover `PortfolioKillSwitch.evaluate`, `PortfolioKillSwitch.trigger`, and `PortfolioKillSwitch.resume` across each trigger condition and approval-required resume behavior.
- [X] Approval and kill-switch security tests shall pass.
- [X] Usage examples shall include failure response envelopes for missing evidence, active kill switch, and invalid approval token.

### File: app/services/risk/scenarios.py

#### Purpose & Scope
Contains functional, security, and testing requirements specifically assigned to `app/services/risk/scenarios.py`.

#### Functional Requirements
- [X] The current implementation support surface shall include scenario and replay contracts through `StressScenario`, `ScenarioResult`, `ScenarioRegistry`, `build_default_scenario_registry`, and `evaluate_scenarios`.
- [X] Scenario analysis with up to 100 scenarios and 500 positions shall complete within 5 seconds p95.
- [X] The module shall support at least 100 stress scenarios per scenario-analysis run.
- [X] Benchmark scenarios `PERF-001` through `PERF-012` shall define dataset size, portfolio shape, strategy count, historical return count, scenario count, cache state, expected p95 latency, and acceptable variance.

#### Non-Functional & Security Requirements
- [X] No file-specific non-functional requirements defined.

#### Testing & Edge Cases
- [X] Performance tests shall cover benchmark scenarios `PERF-001` through `PERF-012`.

## 7. Global Testing, Quality Gates, and Usage Examples


### 7.3 Usage Examples

#### Example 1
```python
from app.services.risk import build_portfolio_risk_snapshot, review_trade_risk, calculate_position_size

snapshot_response = build_portfolio_risk_snapshot(
    portfolio_state=portfolio_state,
    risk_config=risk_config,
    request_id="req-risk-001",
)

sizing_response = calculate_position_size(
    sizing_request={
        "symbol": "EURUSD",
        "method": "fixed_risk",
        "risk_percent": 1.0,
        "stop_loss_pips": 30,
    },
    portfolio_state=portfolio_state,
    risk_config=risk_config,
    request_id="req-risk-002",
)

decision_response = review_trade_risk(
    proposed_trade={
        "symbol": "EURUSD",
        "side": "long",
        "volume": "0.10",
        "requires_live_execution": False,
    },
    portfolio_state=portfolio_state,
    market_context=market_context,
    risk_config=risk_config,
    request_id="req-risk-003",
)
```

#### Example 2
```python
from app.services.risk import validate_risk_approval_token, check_risk_kill_switch

kill_switch_response = check_risk_kill_switch(
    scope={"account_id": "account-001", "strategy_id": "mean-reversion-v1"},
    request_id="req-risk-004",
)

token_response = validate_risk_approval_token(
    token=approval_token,
    expected_scope={
        "account_id": "account-001",
        "strategy_id": "mean-reversion-v1",
        "symbol": "EURUSD",
        "action": "increase_allocation",
    },
    request_id="req-risk-005",
)
```

#### Example 3
```python
from app.services.risk import run_risk_scenario_analysis, generate_risk_report

scenario_response = run_risk_scenario_analysis(
    portfolio_state=portfolio_state,
    scenarios=[
        {"name": "USD shock", "currency_move": {"USD": -0.02}},
        {"name": "spread widening", "spread_multiplier": 3.0},
    ],
    risk_config=risk_config,
    request_id="req-risk-006",
)

report_response = generate_risk_report(
    risk_decision_package=decision_response["data"],
    output_format="markdown",
    request_id="req-risk-007",
)
```

## 8. Acceptance
