# ADR-ANALYTICS-PUBLIC-SURFACE

Status: Approved

Date: 2026-06-18

## Context

Analytics must expose a small, read-only, agent/API-safe public surface while
keeping low-level metric kernels available for developer use through explicit
classification. The service must not grant trading, broker, risk approval, file
write, database mutation, or network authority.

## Decision

The initial official high-level Analytics tool surface is approved as:

- `build_analytics_report`
- `build_portfolio_analytics_report`
- `evaluate_strategy_quality`
- `compare_analytics_reports`
- `calculate_trade_metrics`
- `calculate_equity_metrics`
- `calculate_drawdown_metrics`
- `calculate_risk_metrics`
- `calculate_benchmark_metrics`
- `calculate_statistical_validation`
- `calculate_prop_firm_compliance`
- `build_overview_payload`

The durable machine-readable catalog is
`app.services.analytics.models.OFFICIAL_ANALYTICS_TOOL_CATALOG`. Official tools
must return standard envelopes, accept `request_id`, declare read-only side
effects, and remain safe for agent/API use. Low-level metric kernels are
internal/developer helpers unless listed in the catalog.

## Consequences

Agentic workflows import from `app.services.analytics`. Deep imports remain
test/developer-only. Public surface changes require catalog updates, tests, and
changelog documentation.
