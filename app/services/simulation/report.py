# ruff: noqa
"""Report generation and metrics calculations for simulation.

Computes trade-by-trade metrics, drawdowns, win rates, Sharpe ratio,
and constructs JSON and Markdown summary reports.
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Any

from app.services.simulation.validation.schema import SymbolSpec


def calculate_sharpe_ratio(
    equity_curve: list[tuple[str, Decimal]],
    risk_free_rate_annual: Decimal = Decimal("0.0"),
) -> float:
    """Calculate annualized Sharpe Ratio from daily equity snapshots."""
    if len(equity_curve) < 2:
        return 0.0

    # Group equity by date to get daily values
    daily_equities: dict[str, Decimal] = {}
    for ts_str, eq in equity_curve:
        # Get date part (YYYY-MM-DD)
        date_part = ts_str.split("T")[0]
        daily_equities[date_part] = eq

    sorted_dates = sorted(daily_equities.keys())
    if len(sorted_dates) < 2:
        return 0.0

    # Compute daily returns
    returns: list[float] = []
    for i in range(1, len(sorted_dates)):
        prev_eq = daily_equities[sorted_dates[i - 1]]
        curr_eq = daily_equities[sorted_dates[i]]
        if prev_eq > 0:
            ret = float((curr_eq - prev_eq) / prev_eq)
            returns.append(ret)
        else:
            returns.append(0.0)

    if not returns:
        return 0.0

    mean_ret = sum(returns) / len(returns)
    # Sample variance/std
    if len(returns) > 1:
        variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
        std_ret = math.sqrt(variance)
    else:
        std_ret = 0.0

    if std_ret == 0.0:
        return 0.0

    # Annualize (assuming 252 trading days)
    daily_rf = float(risk_free_rate_annual) / 252.0
    sharpe = (mean_ret - daily_rf) / std_ret * math.sqrt(252)
    return sharpe


def calculate_metrics(
    deals: list[dict[str, Any]],
    equity_curve: list[tuple[str, Decimal]],
    initial_balance: Decimal,
) -> dict[str, Any]:
    """Compute detailed performance metrics from execution deals and equity curve."""
    # Find all "out" deals or trade settlements
    # In MT5, a trade is completed by a deal with entry = DEAL_ENTRY_OUT or similar.
    # Let's look at all deals that modify position or close parts of it.
    # For a general backtest, closed trades are where we realize profit/loss.
    # Let's reconstruct trades from deals or compute directly from deal profits.
    # In our simulator, each deal has a "profit" field. We can aggregate all deals with non-zero profit.
    closed_deals = [
        d
        for d in deals
        if Decimal(str(d.get("profit", "0.0"))) != 0
        or d.get("entry") in {"out", "out_by"}
    ]

    total_trades = len(closed_deals)
    wins = 0
    losses = 0
    gross_profit = Decimal("0.0")
    gross_loss = Decimal("0.0")
    total_commission = Decimal("0.0")
    total_swap = Decimal("0.0")

    for d in deals:
        total_commission += Decimal(str(d.get("commission", "0.0")))
        total_swap += Decimal(str(d.get("swap", "0.0")))

    for d in closed_deals:
        pnl = Decimal(str(d.get("profit", "0.0")))
        if pnl > 0:
            wins += 1
            gross_profit += pnl
        elif pnl < 0:
            losses += 1
            gross_loss += abs(pnl)

    net_profit = gross_profit - gross_loss - total_commission - total_swap
    win_rate = (wins / total_trades * 100.0) if total_trades > 0 else 0.0
    profit_factor = (
        float(gross_profit / gross_loss) if gross_loss > 0 else float(gross_profit)
    )

    # Compute Max Drawdown
    peak = initial_balance
    max_dd = Decimal("0.0")
    max_dd_pct = 0.0

    for _ts, eq in equity_curve:
        peak = max(peak, eq)
        dd = peak - eq
        max_dd = max(max_dd, dd)
        if peak > 0:
            dd_pct = float(dd / peak) * 100.0
            max_dd_pct = max(max_dd_pct, dd_pct)

    # Sharpe ratio
    sharpe = calculate_sharpe_ratio(equity_curve)

    return {
        "initial_balance": float(initial_balance),
        "net_profit": float(net_profit),
        "gross_profit": float(gross_profit),
        "gross_loss": float(gross_loss),
        "total_commission": float(total_commission),
        "total_swap": float(total_swap),
        "total_trades": total_trades,
        "winning_trades": wins,
        "losing_trades": losses,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "max_drawdown": float(max_dd),
        "max_drawdown_percent": max_dd_pct,
        "sharpe_ratio": sharpe,
    }


def generate_json_report(
    run_id: str,
    config: dict[str, Any],
    deals: list[dict[str, Any]],
    equity_curve: list[tuple[str, Decimal]],
    initial_balance: Decimal,
    symbol_specs: dict[str, SymbolSpec],
    data_quality_reports: dict[str, Any],
) -> dict[str, Any]:
    """Compile all results and metrics into a standard JSON report format."""
    metrics = calculate_metrics(deals, equity_curve, initial_balance)

    # Serialize equity curve
    serialized_equity = [
        {"timestamp": ts, "equity": float(eq)} for ts, eq in equity_curve
    ]

    report = {
        "schema_version": "simulation.report.v1",
        "run_id": run_id,
        "status": "success",
        "configuration": config,
        "metrics": metrics,
        "data_quality": data_quality_reports,
        "equity_curve": serialized_equity,
        "deals_count": len(deals),
        "deals": [
            {k: (float(v) if isinstance(v, Decimal) else v) for k, v in d.items()}
            for d in deals
        ],
    }
    return report


def generate_markdown_report(report_json: dict[str, Any]) -> str:
    """Generate a premium-style human-readable Markdown summary from report JSON."""
    metrics = report_json["metrics"]
    config = report_json["configuration"]
    dq = report_json["data_quality"]

    md = f"""# Simulation Run Report - {report_json["run_id"]}

## Overview
- **Strategy Ref**: `{config.get("strategy_ref")}`
- **Symbols**: {", ".join(config.get("symbols", []))}
- **Timeframe**: `{config.get("timeframe")}`
- **Period**: `{config.get("start")}` to `{config.get("end")}`
- **Status**: **{report_json["status"].upper()}**

## Performance Summary
| Metric | Value |
| :--- | :--- |
| **Initial Balance** | {metrics["initial_balance"]:,.2f} |
| **Net Profit** | {metrics["net_profit"]:,.2f} |
| **Gross Profit** | {metrics["gross_profit"]:,.2f} |
| **Gross Loss** | {metrics["gross_loss"]:,.2f} |
| **Total Commissions** | {metrics["total_commission"]:,.2f} |
| **Total Swaps** | {metrics["total_swap"]:,.2f} |
| **Total Trades** | {metrics["total_trades"]} |
| **Win Rate** | {metrics["win_rate"]:.2f}% ({metrics["winning_trades"]} wins, {metrics["losing_trades"]} losses) |
| **Profit Factor** | {metrics["profit_factor"]:.2f} |
| **Max Drawdown** | {metrics["max_drawdown"]:,.2f} ({metrics["max_drawdown_percent"]:.2f}%) |
| **Sharpe Ratio** | {metrics["sharpe_ratio"]:.2f} |

## Realism & Configuration Profile
- **Realism Profile**: `{config.get("realism_profile", "research_approximation")}`
- **Tick Model**: `{config.get("tick_model")}`
- **Spread Model**: `{config.get("spread_model")}`
- **Slippage Model**: `{config.get("slippage_model")}`
- **Commission Model**: `{config.get("commission_model")}`
- **Swap Model**: `{config.get("swap_model")}`

## Data Quality Summary
"""
    for symbol, report in dq.items():
        md += f"""### Symbol: `{symbol}`
- **Status**: {report.get("status", "unknown").upper()}
- **History Quality Score**: {report.get("history_quality", 0.0):.2f}%
- **Total Rows Analyzed**: {report.get("metrics", {}).get("total_rows", 0)}
- **Duplicate Timestamps**: {report.get("metrics", {}).get("duplicate_timestamps", 0)}
- **Non-Monotonic Timestamps**: {report.get("metrics", {}).get("non-monotonic_timestamps", 0)}
"""
        issues = report.get("issues", [])
        if issues:
            md += "\n#### Detected Data Issues:\n"
            for issue in issues[:5]:
                md += f"- **[{issue.get('severity', 'info').upper()}]** {issue.get('message')} (column: `{issue.get('column')}`)\n"
            if len(issues) > 5:
                md += f"- *And {len(issues) - 5} more issues...*\n"

    md += """
---
*Report generated automatically by HaruQuant Simulation service.*
"""
    return md
