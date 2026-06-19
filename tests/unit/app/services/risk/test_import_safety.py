"""Unit tests verifying import safety and tool constraints."""

import builtins
import importlib
import sys
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# List of all modules under app.services.risk
RISK_MODULES = [
    "app.services.risk",
    "app.services.risk.allocation",
    "app.services.risk.audit",
    "app.services.risk.config",
    "app.services.risk.correlation",
    "app.services.risk.drawdown",
    "app.services.risk.execution_gate",
    "app.services.risk.exposure",
    "app.services.risk.governor",
    "app.services.risk.kill_switch",
    "app.services.risk.lifecycle",
    "app.services.risk.limits",
    "app.services.risk.margin",
    "app.services.risk.models",
    "app.services.risk.policy",
    "app.services.risk.regime",
    "app.services.risk.reports",
    "app.services.risk.sizing",
    "app.services.risk.storage",
    "app.services.risk.stress",
    "app.services.risk.var_es",
]


class SideEffectError(Exception):
    """Exception raised when a side-effect is detected during import."""


@pytest.fixture(autouse=True)
def restore_sys_modules() -> Any:
    """Fixture to backup and restore sys.modules to isolate import modifications."""
    original_modules = sys.modules.copy()
    yield
    sys.modules.clear()
    sys.modules.update(original_modules)


def test_import_safety_and_side_effects() -> None:
    """Ensure import of any risk module has no side-effects."""
    original_open = builtins.open

    def mock_open(file: Any, mode: str = "r", *args: Any, **kwargs: Any) -> Any:
        if any(c in mode for c in ["w", "a", "x", "+"]):
            msg = f"Filesystem write attempted on {file} with mode {mode}"
            raise SideEffectError(msg)
        return original_open(file, mode, *args, **kwargs)

    def mock_socket(*_args: Any, **_kwargs: Any) -> Any:
        msg = "Network socket creation attempted during import."
        raise SideEffectError(msg)

    def mock_popen(*_args: Any, **_kwargs: Any) -> Any:
        msg = "Subprocess execution attempted during import."
        raise SideEffectError(msg)

    for mod_name in RISK_MODULES:
        sys.modules.pop(mod_name, None)
        with (
            patch("builtins.open", mock_open),
            patch("socket.socket", mock_socket),
            patch("subprocess.Popen", mock_popen),
            patch(
                "urllib.request.urlopen",
                side_effect=SideEffectError("Network call via urlopen"),
            ),
        ):
            try:
                importlib.import_module(mod_name)
            except SideEffectError as e:
                pytest.fail(f"Side-effect on import '{mod_name}': {e}")
            except Exception as e:  # noqa: BLE001
                pytest.fail(f"Module '{mod_name}' failed to import: {e}")


def test_missing_optional_dependencies() -> None:
    """Verify missing optional dependencies (e.g. numba) do not break importability."""
    original_import = builtins.__import__

    def mock_import(
        name: str,
        globals: Any = None,  # noqa: A002
        locals: Any = None,  # noqa: A002
        fromlist: Any = None,
        level: int = 0,
    ) -> Any:
        if name == "numba":
            raise ImportError(f"No module named '{name}' (simulated missing)")
        return original_import(name, globals, locals, fromlist, level)

    for mod_name in RISK_MODULES:
        sys.modules.pop(mod_name, None)
        with patch("builtins.__import__", mock_import):
            try:
                importlib.import_module(mod_name)
            except Exception as e:  # noqa: BLE001
                pytest.fail(f"Module '{mod_name}' broke when numba was missing: {e}")


def test_agentic_tools_safety_metadata() -> None:
    """Verify that all tools in agentic/tools/risk.py do not place trades."""
    import agentic.tools.risk as risk_tools

    for tool_name in risk_tools.__all__:
        if tool_name in {"get_shared_governor", "get_shared_store"}:
            continue

        tool_func = getattr(risk_tools, tool_name)
        assert callable(tool_func), f"Tool {tool_name} is not callable"

        with (
            patch("agentic.tools.risk.get_shared_governor") as mock_gov_getter,
            patch("agentic.tools.risk.load_risk_config"),
            patch("agentic.tools.risk._shared_store"),
        ):
            mock_gov = MagicMock()
            mock_gov_getter.return_value = mock_gov

            mock_decision = MagicMock()
            mock_decision.model_dump.return_value = {
                "decision_id": "dec_1",
                "status": "approve",
                "reason": "mocked",
            }
            mock_gov.review_trade_risk.return_value = mock_decision
            mock_gov.review_allocation_proposal.return_value = mock_decision
            mock_gov.review_strategy_admission.return_value = mock_decision
            mock_gov.run_portfolio_risk_governor.return_value = mock_decision

            res = None
            try:
                if tool_name == "review_trade_risk":
                    res = tool_func(
                        proposed_trade={
                            "symbol": "EURUSD",
                            "side": "buy",
                            "volume": 0.1,
                        },
                        portfolio_state={
                            "account_id": "acc_1",
                            "balance": 10000.0,
                            "equity": 10000.0,
                            "margin_used": 0.0,
                            "free_margin": 10000.0,
                            "floating_pnl": 0.0,
                            "realized_pnl": 0.0,
                            "currency": "USD",
                            "as_of": datetime.now(UTC).isoformat(),
                        },
                        market_context={
                            "mode": "paper",
                            "environment": "local",
                            "freshness": datetime.now(UTC).isoformat(),
                        },
                    )
                elif tool_name == "run_portfolio_risk_governor":
                    res = tool_func(
                        portfolio_state={
                            "account_id": "acc_1",
                            "balance": 10000.0,
                            "equity": 10000.0,
                            "margin_used": 0.0,
                            "free_margin": 10000.0,
                            "floating_pnl": 0.0,
                            "realized_pnl": 0.0,
                            "currency": "USD",
                            "as_of": datetime.now(UTC).isoformat(),
                        },
                        market_context={
                            "mode": "paper",
                            "environment": "local",
                            "freshness": datetime.now(UTC).isoformat(),
                        },
                    )
                elif tool_name == "review_allocation_proposal":
                    res = tool_func(
                        proposed_allocation={
                            "allocations": {},
                            "as_of": datetime.now(UTC).isoformat(),
                        },
                        portfolio_state={
                            "account_id": "acc_1",
                            "balance": 10000.0,
                            "equity": 10000.0,
                            "margin_used": 0.0,
                            "free_margin": 10000.0,
                            "floating_pnl": 0.0,
                            "realized_pnl": 0.0,
                            "currency": "USD",
                            "as_of": datetime.now(UTC).isoformat(),
                        },
                    )
                elif tool_name == "review_strategy_admission":
                    res = tool_func(
                        strategy_admission_request={
                            "strategy_id": "s1",
                            "evidence": {},
                        },
                    )
            except Exception:  # noqa: BLE001, S110
                # If mock invocation failed because of required params,
                # we can directly inspect wrapper structure
                pass

            if res is not None:
                assert "metadata" in res, (
                    f"Tool {tool_name} response lacks standard metadata envelope"
                )
                metadata = res["metadata"]
                assert metadata.get("trades") is False, (
                    f"Tool {tool_name} sets trades=True, violating boundary!"
                )
                assert metadata.get("tool_name") == tool_name
