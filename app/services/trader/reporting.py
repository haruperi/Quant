# ruff: noqa: E501
"""ReportingService implementation.

Generates structured trading summaries, audit histories, and lists of
active positions, active pending orders, and recent reconciliation drifts.
"""

from typing import Any

from app.services.trader.store import TradeStore


class ReportingService:
    """Compiles statistics and details of active trade objects and reconciliation history."""

    @staticmethod
    def build_report(
        store: TradeStore,
        reconciliation_summary: dict[str, Any] | None = None,
        validation_warnings: list[str] | None = None,
    ) -> dict[str, Any]:
        """Aggregate data to form a structured trading report.

        Args:
            store: The TradeStore holding active records.
            reconciliation_summary: The results of the last reconciliation pass.
            validation_warnings: Any accumulated warnings.

        Returns:
            dict[str, Any]: Structured report.
        """
        positions = store.get_positions()
        orders = store.get_orders()
        executions = store.get_executions()

        total_profit = sum(p.get("profit", 0.0) for p in positions)
        total_exposure = sum(p.get("volume", 0.0) for p in positions)

        return {
            "summary": {
                "active_positions_count": len(positions),
                "active_orders_count": len(orders),
                "total_executions_count": len(executions),
                "total_profit": total_profit,
                "total_exposure": total_exposure,
            },
            "positions": positions,
            "orders": orders,
            "executions": executions,
            "reconciliation": reconciliation_summary or {"is_reconciled": False},
            "validation_warnings": validation_warnings or [],
        }
