# ruff: noqa
"""Backtest orchestrator for simulation.

Coordinates configuration validation, historical data fetching, data quality checks,
strategy signal generation, tick streaming, accounting/execution loop, and report persistence.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pandas as pd

from app.services.data import get_data, get_symbol_metadata
from app.services.simulation.engine import EventDrivenExecutionEngine
from app.services.simulation.journal import Journal
from app.services.simulation.models import (
    FeeModel,
    LiquidityModel,
    MarginModel,
    SlippageModel,
    SpreadModel,
    SwapModel,
    TickGenerator,
)
from app.services.simulation.report import (
    generate_json_report,
    generate_markdown_report,
)
from app.services.simulation.validation.quality import check_data_quality
from app.services.simulation.validation.schema import (
    SimulationBacktestRequestV1,
    SimulationToolEnvelopeV1,
    SymbolSpec,
)
from app.services.strategies import (
    StrategyExecutionContext,
    StrategyRefInput,
    run_vectorized_strategy_signals,
)
from app.utils.errors import (
    SimulationError,
)
from app.utils.logger import logger
from app.utils.normalization import parse_datetime
from app.utils.standard import (
    StandardResponse,
    build_metadata,
    error_response,
    success_response,
)


def calculate_sized_volume(
    sizing_mode: str,
    balance: Decimal,
    price: Decimal,
    stop_loss: Decimal | None,
    symbol_spec: SymbolSpec,
    quantity_hint: Decimal | None = None,
    risk_pct: Decimal = Decimal("0.01"),  # 1% default risk
) -> Decimal:
    """Compute normalized lot volume based on configured position sizing mode."""
    mode = sizing_mode.upper()

    if mode == "FIXED_LOT":
        vol = quantity_hint if quantity_hint is not None else Decimal("0.1")
    elif mode == "FIXED_RISK":
        if stop_loss is None or stop_loss == 0:
            raise SimulationError(
                "Stop loss is required for FIXED_RISK position sizing.",
                code="SIM_SIZING_REQUIRES_STOP_LOSS",
            )
        stop_distance = abs(price - stop_loss)
        if stop_distance <= 0:
            raise SimulationError(
                "Stop distance must be greater than zero for FIXED_RISK position sizing.",
                code="SIM_INVALID_PRICE",
            )

        # Risk amount = 1% of balance
        risk_amount = balance * risk_pct
        # Volume = Risk amount / (stop_distance * contract_size * tick_value)
        vol = risk_amount / (stop_distance * symbol_spec.contract_size)
    else:
        # Default fallback
        vol = quantity_hint if quantity_hint is not None else Decimal("0.1")

    # Normalize volume constraints
    vol = max(symbol_spec.volume_min, min(symbol_spec.volume_max, vol))
    # Step rounding (floor-to-step)
    steps = (vol - symbol_spec.volume_min) / symbol_spec.volume_step
    vol = symbol_spec.volume_min + (
        steps.quantize(Decimal(1), rounding="ROUND_DOWN") * symbol_spec.volume_step
    )
    return vol


def run_backtest(request_data: dict[str, Any] | Mapping[str, Any]) -> StandardResponse:
    """Execute a backtest coordinate run and return standard tool response envelope."""
    start_time_ms = datetime.now(UTC).timestamp()

    # Extract/Generate IDs
    req_id = request_data.get("request_id") or f"req_sim_{int(start_time_ms * 1000)}"
    run_id = f"run_sim_{int(start_time_ms * 1000)}"
    journal: Journal | None = None

    try:
        # 1. Parse and Validate Request Schema
        req = SimulationBacktestRequestV1(**dict(request_data))

        # Initialize Journal Persistence
        art_dir = req.journal_persistence.get("artifact_dir") or "artifacts/simulation"
        journal = Journal(
            run_id=run_id,
            artifact_dir=art_dir,
            use_sqlite_sidecar=req.journal_persistence.get("use_sqlite_sidecar", True),
        )

        # Journal request configuration
        journal.append_event(
            "backtest_started",
            {
                "run_id": run_id,
                "request_id": req_id,
                "config": req.model_dump(mode="json"),
            },
        )

        # Check symbol list
        if not req.symbols:
            raise SimulationError(
                "No symbols specified in request.", code="SIM_MISSING_SYMBOL"
            )

        primary_symbol = req.symbols[0]

        # 2. Retrieve Symbol Metadata and construct SymbolSpec
        raw_meta = get_symbol_metadata(
            primary_symbol, source=req.broker_profile_ref.split("_")[0] or "csv"
        )
        symbol_spec = SymbolSpec(
            symbol=primary_symbol,
            point=Decimal(str(raw_meta.get("point", "0.00001"))),
            tick_size=Decimal(str(raw_meta.get("tick_size", "0.00001"))),
            tick_value=Decimal(str(raw_meta.get("tick_value", "1.0"))),
            contract_size=Decimal(str(raw_meta.get("contract_size", "100000.0"))),
            volume_min=Decimal(str(raw_meta.get("lot_min", "0.01"))),
            volume_max=Decimal(str(raw_meta.get("lot_max", "100.0"))),
            volume_step=Decimal(str(raw_meta.get("lot_step", "0.01"))),
            asset_class=raw_meta.get("asset_class", "FX").upper(),
            profit_currency=raw_meta.get("profit_currency", "USD"),
            margin_currency=raw_meta.get("margin_currency", "USD"),
            stops_level=Decimal(str(raw_meta.get("stops_level", "0.0"))),
            freeze_level=Decimal(str(raw_meta.get("freeze_level", "0.0"))),
        )

        # 3. Retrieve Historical Bar data
        records = get_data(
            symbol=primary_symbol,
            start_time=req.start,
            end_time=req.end,
            timeframe=req.timeframe,
            source=req.broker_profile_ref.split("_")[0] or "csv",
        )

        # 4. Check Data Quality Gate (fails closed by default)
        dq_report = check_data_quality(
            records=records,
            expected_symbol=primary_symbol,
            timeframe=req.timeframe,
            block_on_severe=True,
        )

        # Convert to DataFrame for strategy signals computation
        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.set_index("timestamp")
        if df.index.tz is None:
            df.index = df.index.tz_localize("UTC")
        else:
            df.index = df.index.tz_convert("UTC")

        # 5. Execute Vectorized Strategy Signals
        strategy_ref = StrategyRefInput(
            strategy_id=req.strategy_ref,
            environment="BACKTEST",
        )
        ctx = StrategyExecutionContext(
            environment="BACKTEST",
            decision_timestamp=parse_datetime(req.end),
            timing_policy="BAR_OPEN_PREVIOUS_CLOSE",
            seed_material="sim_seed_v1",
            request_id=req_id,
            correlation_id=req_id,
        )

        sig_res = run_vectorized_strategy_signals(
            strategy_ref=strategy_ref,
            market_data=df,
            indicators=df,
            context=ctx,
            config=req.strategy_config,
        )

        if sig_res["status"] == "error":
            msg = f"Strategy signal generation failed: {sig_res['error']['details']}"
            raise SimulationError(
                msg,
                code=sig_res["error"]["code"],
            )

        trade_intents = sig_res["data"]["trade_intents"]

        # 6. Initialize Simulator Models & Engine
        spread_model = SpreadModel(model_type=req.spread_model)
        slippage_model = SlippageModel(model_type=req.slippage_model)
        liquidity_model = LiquidityModel(model_type="INFINITE_LIQUIDITY")
        fee_model = FeeModel(model_type=req.commission_model)
        swap_model = SwapModel(model_type=req.swap_model)
        margin_model = MarginModel(leverage=Decimal("100.0"))

        engine = EventDrivenExecutionEngine(
            initial_balance=req.initial_balance,
            account_currency=req.account_currency,
            journal=journal,
            spread_model=spread_model,
            slippage_model=slippage_model,
            liquidity_model=liquidity_model,
            fee_model=fee_model,
            swap_model=swap_model,
            margin_model=margin_model,
        )

        tick_generator = TickGenerator(
            symbol_spec=symbol_spec,
            spread_model=spread_model,
            tick_model=req.tick_model,
            global_seed=42,
        )

        # 7. Run chronological tick execution loop
        for bar in records:
            ticks = tick_generator.generate_ticks_for_bar(bar)
            if not ticks:
                continue

            bar_ts = bar["timestamp"]

            # Filter signals corresponding to this bar open time
            # Match ISO strings
            bar_intents = [
                intent
                for intent in trade_intents
                if pd.Timestamp(intent.decision_timestamp).tz_convert("UTC").isoformat()
                == bar_ts
            ]

            first_tick = ticks[0]
            for intent in bar_intents:
                price = (
                    Decimal(str(first_tick["ask"]))
                    if intent.side == "BUY"
                    else Decimal(str(first_tick["bid"]))
                )
                volume = calculate_sized_volume(
                    sizing_mode="FIXED_LOT",
                    balance=engine.balance,
                    price=price,
                    stop_loss=intent.stop_loss,
                    symbol_spec=symbol_spec,
                    quantity_hint=intent.quantity_hint,
                )

                if intent.intent_type == "OPEN":
                    engine.execute_order(
                        symbol=intent.symbol,
                        direction=intent.side,
                        volume=volume,
                        price=price,
                        sl=intent.stop_loss,
                        tp=intent.take_profit,
                        symbol_spec=symbol_spec,
                        magic=12345,
                        comment=intent.rationale_ref or "",
                    )
                elif intent.intent_type == "CLOSE":
                    # Find open position for this symbol and close it
                    pos_to_close = None
                    for p_id, pos in engine.positions.items():
                        if pos["symbol"] == intent.symbol:
                            pos_to_close = p_id
                            break
                    if pos_to_close:
                        engine._close_position(
                            pos_id=pos_to_close,
                            close_price=price,
                            close_time=bar_ts,
                            symbol_spec=symbol_spec,
                            comment="Closed by strategy intent",
                        )

            # Process all generated ticks chronologically in engine
            for tick in ticks:
                engine.process_tick(tick, symbol_spec)

        # Post-loop: SQLite sidecar connection will be closed in finally block

        # 8. Compile Reports and Save files
        report_json = generate_json_report(
            run_id=run_id,
            config=req.model_dump(mode="json"),
            deals=engine.deals,
            equity_curve=engine.equity_curve,
            initial_balance=req.initial_balance,
            symbol_specs={primary_symbol: symbol_spec},
            data_quality_reports={primary_symbol: dq_report.to_dict()},
        )

        def decimal_to_float(obj: Any) -> Any:
            if isinstance(obj, Decimal):
                return float(obj)
            if isinstance(obj, dict):
                return {k: decimal_to_float(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [decimal_to_float(x) for x in obj]
            if isinstance(obj, tuple):
                return tuple(decimal_to_float(x) for x in obj)
            return obj

        report_json = decimal_to_float(report_json)

        md_report = generate_markdown_report(report_json)

        # Save Markdown report
        md_path = os.path.join(art_dir, f"report_{run_id}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_report)

        json_path = os.path.join(art_dir, f"report_{run_id}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(report_json, indent=2))

        # Construct Envelope V1 Response
        envelope = SimulationToolEnvelopeV1(
            request_id=req_id,
            status="success",
            result=report_json,
            artifacts={
                "report_md": md_path,
                "report_json": json_path,
                "journal_jsonl": journal.jsonl_path or "",
            },
        )

        end_time_ms = datetime.now(UTC).timestamp()
        duration_ms = (end_time_ms - start_time_ms) * 1000.0

        meta = build_metadata(
            tool_name="run_backtest",
            tool_version="1.0.0",
            tool_category="simulation",
            tool_risk_level="low",
            request_id=req_id,
            reads=True,
            writes=True,
            updates=False,
            deletes=False,
            trades=False,
            requires_network=False,
            execution_ms=duration_ms,
        )
        return success_response(
            message="Backtest run completed successfully.",
            data=envelope.model_dump(mode="json"),
            metadata=meta,
        )

    except Exception as exc:
        # Error handling with SIM_* taxonomy compliance
        code = getattr(exc, "code", "SIM_INTERNAL_ERROR")
        logger.error(
            f"Backtest run failed: {exc}",
            extra={
                "request_id": req_id,
                "error_code": code,
            },
        )

        # Construct Failed Envelope V1 Response
        envelope = SimulationToolEnvelopeV1(
            request_id=req_id,
            status="failed",
            error={
                "code": code,
                "details": str(exc),
            },
        )

        end_time_ms = datetime.now(UTC).timestamp()
        duration_ms = (end_time_ms - start_time_ms) * 1000.0

        meta = build_metadata(
            tool_name="run_backtest",
            tool_version="1.0.0",
            tool_category="simulation",
            tool_risk_level="low",
            request_id=req_id,
            reads=True,
            writes=True,
            updates=False,
            deletes=False,
            trades=False,
            requires_network=False,
            execution_ms=duration_ms,
        )
        return error_response(
            message=f"Backtest run failed: {exc}",
            code=code,
            details=str(exc),
            metadata=meta,
        )
    finally:
        if journal is not None:
            journal.close()
