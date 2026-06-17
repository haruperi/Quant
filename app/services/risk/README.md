# Risk Service (`app/services/risk`)

The Risk Service acts as the pre-trade risk governance layer and safety gate for HaruQuantAI. It intercepts strategy-generated trade signals and evaluates them against strict account limits, sizing constraints, market regimes, and stress scenarios before they can be routed to the execution boundary.

---

## 1. Directory Structure

```text
app/
  services/
    risk/
      __init__.py       # Entry point facade exposing official tools & models
      models.py         # Pydantic schemas & risk configuration rules
      governor.py       # Orchestration engine for pre-trade risk validation
      limits.py         # Daily loss, gross exposure, and max drawdown limits
      sizing.py         # Advanced position sizing calculators (Kelly, Volatility, etc.)
      lifecycle.py      # Strategy lifecycle admission & capital allocation
      kill_switch.py    # Drawdown regime classification & emergency kill switch
      scenarios.py      # Stress scenario evaluation (shocks, spread spikes)
      tools.py          # Concrete implementations of the 10 official AI tools
```

---

## 2. Core Components

### 2.1. Governor (`governor.py`)
Provides the pre-trade risk interception gate. The `RiskGovernor` evaluates proposed strategy trades against the active limits and rules, signing them with approval tokens if passed, or flagging them with warnings, rejections, or blocks if limits are violated.

### 2.2. Limits (`limits.py`)
Implements stateless rules that validate proposed trades against:
- **Daily Loss Limits**: Rejects trades if daily cumulative losses exceed thresholds.
- **Max Drawdown Limits**: Restricts trading if the current account drawdown crosses boundaries.
- **Leverage & Exposure**: Enforces absolute gross and net leverage limits.

### 2.3. Sizing (`sizing.py`)
Computes capital allocations and target lot sizes based on multiple methodologies:
- **Fixed Risk**: Percentage of equity at risk per trade.
- **Fixed Fractional**: Sizing proportional to account equity.
- **Kelly Criterion**: Sizing based on historical strategy win/loss ratios.
- **Volatility Sizing**: Adjusted by ATR or rolling historical volatility.
- **Milestone Sizing**: Sizing based on strategy milestone performance tiers.

*Note: Sizing dynamically resolves symbol parameters (e.g. point size, contract size) from active MetaTrader5 terminal sessions with robust offline fallback maps (per DEC-011).*

### 2.4. Kill Switch (`kill_switch.py`)
Defines the emergency account management actions:
- Monitors account drawdown.
- Classifies drawdown into distinct regimes: `normal`, `caution`, `warning`, `crisis`.
- Coordinates immediate order cancellation or position flattening during emergency events.

### 2.5. Scenarios (`scenarios.py`)
Evaluates portfolio stability under adverse price shocks (e.g. $\pm 5\%$, $\pm 10\%$, $\pm 20\%$) and spread spikes. The engine computes hypothetical equity outcomes and metrics (VaR/CVaR) to flag high-risk positions.

---

## 3. Official AI Tools Surface

The Risk domain exports 10 official, agent-callable AI tools from `tools.py`. Each tool performs payload limits verification and wraps results in the standard HaruQuant `StandardResponse` JSON-compatible envelope.

| Official AI Tool Name | Primary Input Parameter | Risk Level | Description |
|---|---|---|---|
| `build_portfolio_risk_snapshot` | `PortfolioState`, `RiskConfig` | Low | Builds a complete risk snapshot containing calculated drawdown, leverage, gross/net exposure, and VaR/CVaR. |
| `review_trade_risk` | `ProposedTrade`, `PortfolioState` | High | Evaluates a proposed strategy trade against active risk limits and policy rules. |
| `calculate_position_size` | `PositionSizingRequest`, `PortfolioState` | Medium | Calculates target lot sizes or capital allocation weights based on active sizing methods. |
| `assess_risk_regime` | `PortfolioState`, `RiskConfig` | Low | Classifies the current market volatility regime, liquidity regime, and drawdown state. |
| `review_strategy_admission` | `strategy_id`, `admission_evidence` | Medium | Evaluates strategy backtest audit logs before admitting the strategy to the active pool. |
| `review_allocation_proposal` | `ProposedAllocation`, `PortfolioState` | Medium | Verifies strategy capital allocation proposals against maximum allowed asset caps. |
| `create_risk_decision_package` | `decision_id`, `status`, `rule_key` | Low | Constructs a canonical decision envelope wrapping risk evaluations and signatures. |
| `validate_risk_approval_token` | `RiskApprovalToken`, `expected_scope` | High | Verifies signature, expiry, and single-use status of trading exception approval tokens. |
| `run_risk_scenario_analysis` | `PortfolioState`, `scenarios` | Medium | Simulates portfolio equity outcomes under custom price shocks and spread spikes. |
| `generate_risk_report` | `RiskDecisionPackage`, `output_format` | Low | Generates human-readable summary documents (Markdown/JSON) from snapshot evaluations. |

---

## 4. Usage Example

```python
from app.services.risk import (
    ProposedTrade,
    PortfolioState,
    RiskConfig,
    review_trade_risk,
)

# 1. Initialize proposed trade and portfolio state
trade = ProposedTrade(
    symbol="EURUSD",
    direction="long",
    quantity=1.5,
    entry_price=1.08500,
    stop_loss=1.08000,
    take_profit=1.10000,
    strategy_id="trend_ema_cross"
)

state = PortfolioState(
    account_id="real_12345",
    balance=50000.0,
    equity=49850.0,
    margin_used=1200.0,
    positions=[]
)

config = {
    "max_drawdown_limit": 0.05,
    "max_gross_leverage": 10.0,
}

# 2. Run the trade risk review tool
response = review_trade_risk(
    proposed_trade=trade,
    portfolio_state=state,
    risk_config=config,
    request_id="req_98765"
)

print(response)
```
