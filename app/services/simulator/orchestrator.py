"""Simulator orchestration and official tool boundary.

Exports BacktestOrchestrator, EventDrivenExecutionEngine, and run_backtest.
Only run_backtest is intended as the official AI-callable simulator tool.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, Literal

from app.services.simulator.engine import EventDrivenExecutionEngine, build_run_id
from app.services.simulator.validation import parse_backtest_request
from app.services.strategies import (
    get_strategy,
    validate_strategy_config,
    validate_strategy_ref,
    vet_and_sandbox_code,
)
from app.utils.errors import (
    SimArbitraryCodeRejectedError,
    SimulationError,
    ValidationError,
)
from app.utils.logger import logger
from app.utils.standard import (
    StandardResponse,
    build_metadata,
    error_response,
    success_response,
)

if TYPE_CHECKING:
    from app.services.simulator.models import SimulatorBacktestRequestV1

TOOL_NAME = "run_backtest"
TOOL_VERSION = "0.8.0"
TOOL_CATEGORY = "simulator"
TOOL_RISK_LEVEL: Literal["medium"] = "medium"
NON_FATAL_DIAGNOSTIC_CODES = frozenset({"SIM_IOC_REMAINDER_CANCELLED"})
SIMULATOR_RUN_STATUSES = frozenset(
    {"success", "failed", "queued", "cancelled", "diagnostic_failed"}
)


def is_non_fatal_diagnostic(code: str) -> bool:
    """Return whether a simulator diagnostic code is non-fatal.

    Args:
        code: Simulator diagnostic code.

    Returns:
        bool: True when the code is explicitly non-fatal.

    Raises:
        No exceptions are raised.
    """
    return code in NON_FATAL_DIAGNOSTIC_CODES


class BacktestOrchestrator:
    """Coordinate validation, engine execution, and result envelopes.

    Args:
        engine: Optional execution engine instance.

    Raises:
        No exceptions are raised during construction.
    """

    def __init__(self, engine: EventDrivenExecutionEngine | None = None) -> None:
        """Initialize the orchestrator."""
        self.engine = engine or EventDrivenExecutionEngine()

    def execute(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        """Validate and coordinate a simulator request.

        Args:
            payload: Request mapping.

        Returns:
            dict[str, Any]: Simulator lifecycle payload.

        Raises:
            ValidationError: If payload validation fails.
            SimArbitraryCodeRejectedError: If raw strategy code is detected.
            SimulationError: If a supported fail-closed simulator condition occurs.
        """
        request = parse_backtest_request(payload)
        self._validate_strategy_boundary(request)
        self._validate_resume_boundary(request.metadata)
        control_status = self._control_status(request.metadata)
        if control_status is not None:
            return self._terminal_payload(status=control_status, request=request)

        result = self.engine.run(request)
        result_payload = result.to_dict()
        return self._success_payload(
            request=request,
            result_payload=result_payload,
            warnings=[],
        )

    def _validate_strategy_boundary(self, request: SimulatorBacktestRequestV1) -> None:
        """Validate strategy registry and sandbox boundaries.

        Args:
            request: Validated simulator request.

        Returns:
            None.

        Raises:
            ValidationError: If the registered strategy reference or config fails.
            SimArbitraryCodeRejectedError: If code-based strategy execution is
                requested.
        """
        strategy_input_mode = str(
            request.metadata.get("strategy_input_mode", "registered")
        )
        if strategy_input_mode == "code":
            vet_and_sandbox_code(
                "code-based strategy execution requested",
                request_id=request.request_id,
            )
        if strategy_input_mode != "registered":
            raise ValidationError(
                "strategy_input_mode must be 'registered' unless code execution is "
                "explicitly enabled by a future sandbox profile.",
                code="SIM_INVALID_CONFIG",
            )
        validation = validate_strategy_ref(
            request.strategy_ref,
            environment="BACKTEST",
            request_id=request.request_id,
        )
        if validation["status"] != "success":
            error = validation.get("error")
            code = "SIM_INVALID_CONFIG"
            details = "Strategy reference validation failed."
            if isinstance(error, Mapping):
                details = str(error.get("details", details))
            raise ValidationError(details, code=code)
        strategy_class = get_strategy(request.strategy_ref)
        validate_strategy_config(
            strategy_class,
            request.strategy_config,
            unknown_field_policy="IGNORE",
        )

    def _validate_resume_boundary(self, metadata: Mapping[str, object]) -> None:
        """Validate checkpoint resume metadata before execution.

        Args:
            metadata: Request metadata mapping.

        Returns:
            None.

        Raises:
            SimulationError: If checkpoint compatibility fails.
        """
        if metadata.get("resume_from_checkpoint") and (
            metadata.get("checkpoint_compatible") is False
        ):
            raise SimulationError(
                "Checkpoint compatibility validation failed.",
                code="SIM_CHECKPOINT_INCOMPATIBLE",
            )

    def _control_status(
        self,
        metadata: Mapping[str, object],
    ) -> Literal["queued", "cancelled", "diagnostic_failed"] | None:
        """Resolve supported service-control statuses from metadata.

        Args:
            metadata: Request metadata mapping.

        Returns:
            Optional simulator lifecycle status.

        Raises:
            No exceptions are raised.
        """
        if metadata.get("cancel_requested") is True:
            return "cancelled"
        if (
            metadata.get("diagnostic_mode") is True
            and metadata.get("force_diagnostic_failure") is True
        ):
            return "diagnostic_failed"
        if (
            metadata.get("service_mode") is True
            and metadata.get("workers_saturated") is True
        ):
            return "queued"
        return None

    def _success_payload(
        self,
        *,
        request: SimulatorBacktestRequestV1,
        result_payload: dict[str, Any],
        warnings: list[dict[str, str]],
    ) -> dict[str, Any]:
        """Build a successful simulator lifecycle payload.

        Args:
            request: Validated simulator request.
            result_payload: Engine result dictionary.
            warnings: Non-fatal warnings.

        Returns:
            dict[str, Any]: Standard simulator lifecycle payload.

        Raises:
            No exceptions are raised.
        """
        artifacts = dict(result_payload.get("artifact_manifest", {}))
        orchestration_metadata = self._orchestration_metadata(
            lifecycle_state="completed",
            queue_metadata=None,
            retry_metadata=None,
        )
        return {
            **result_payload,
            "request_id": request.request_id,
            "status": "success",
            "result": result_payload,
            "error": None,
            "warnings": warnings,
            "metadata": orchestration_metadata,
            "artifacts": artifacts,
        }

    def _terminal_payload(
        self,
        *,
        status: Literal["queued", "cancelled", "diagnostic_failed"],
        request: SimulatorBacktestRequestV1,
    ) -> dict[str, Any]:
        """Build a supported non-completed simulator lifecycle payload.

        Args:
            status: Supported terminal or service-control lifecycle status.
            request: Validated simulator request.

        Returns:
            dict[str, Any]: Simulator lifecycle payload.

        Raises:
            ValidationError: If an unsupported status is passed.
        """
        if status not in SIMULATOR_RUN_STATUSES:
            raise ValidationError(
                "unsupported simulator status.",
                code="SIM_INVALID_CONFIG",
            )
        run_id = build_run_id(request)
        error = None
        warnings: list[dict[str, str]] = []
        queue_metadata = None
        lifecycle_state = status
        retry_metadata: dict[str, object] | None = None
        if status == "queued":
            queue_metadata = {
                "run_id": run_id,
                "queue_position": 1,
                "max_queue_length": 1,
                "cancellation_supported": True,
            }
            retry_metadata = {"retry_after_seconds": 1}
            warnings.append(
                {
                    "code": "SIM_QUEUE_LIMIT_DEFERRED",
                    "details": "Workers are saturated; run was queued.",
                }
            )
        elif status == "cancelled":
            warnings.append(
                {
                    "code": "SIM_RUN_CANCELLED",
                    "details": "Run was cancelled before execution.",
                }
            )
        else:
            error = {
                "code": "SIM_DATA_QUALITY_FAILED",
                "details": "Diagnostic mode stopped before promotable execution.",
            }
            warnings.append(
                {
                    "code": "SIM_DIAGNOSTIC_ONLY",
                    "details": "Partial diagnostics are non-promotable.",
                }
            )
        return {
            "schema_version": "1.0.0",
            "request_id": request.request_id,
            "run_id": run_id,
            "classification": "research_approximation",
            "status": status,
            "result": None,
            "error": error,
            "warnings": warnings,
            "metadata": self._orchestration_metadata(
                lifecycle_state=lifecycle_state,
                queue_metadata=queue_metadata,
                retry_metadata=retry_metadata,
            ),
            "artifacts": {},
        }

    def _orchestration_metadata(
        self,
        *,
        lifecycle_state: str,
        queue_metadata: dict[str, object] | None,
        retry_metadata: dict[str, object] | None,
    ) -> dict[str, object]:
        """Build redacted orchestrator metadata.

        Args:
            lifecycle_state: Current lifecycle state.
            queue_metadata: Optional bounded queue metadata.
            retry_metadata: Optional retry metadata.

        Returns:
            dict[str, object]: Metadata for simulator result payload.

        Raises:
            No exceptions are raised.
        """
        return {
            "module": "simulator",
            "operation": "run_backtest",
            "engine_version": self.engine.engine_version,
            "lifecycle_state": lifecycle_state,
            "queue": queue_metadata,
            "retry": retry_metadata,
            "pipeline": [
                "validated",
                "data_quality_checked",
                "signals_planned",
                "ticks_planned",
                "executed",
                "metrics_collected",
                "reporting_ready",
            ],
        }


def run_backtest(
    payload: Mapping[str, Any],
    *,
    request_id: str | None = None,
) -> StandardResponse:
    """Run a validated simulator backtest request.

    Args:
        payload: Backtest request mapping.
        request_id: Optional trace request id overriding metadata only.

    Returns:
        StandardResponse: Success or deterministic error envelope.

    Raises:
        No exceptions are raised for handled validation or execution failures.
    """
    start = time.perf_counter()
    effective_request_id = request_id
    raw_request_id = payload.get("request_id") if isinstance(payload, Mapping) else None
    if effective_request_id is None and isinstance(raw_request_id, str):
        effective_request_id = raw_request_id
    metadata = build_metadata(
        tool_name=TOOL_NAME,
        tool_version=TOOL_VERSION,
        tool_category=TOOL_CATEGORY,
        tool_risk_level=TOOL_RISK_LEVEL,
        request_id=effective_request_id,
        reads=True,
        writes=False,
        trades=False,
        requires_network=False,
        start_time=start,
    )
    try:
        logger.info(
            "run_backtest called",
            extra={
                "event_name": "run_backtest_called",
                "request_id": effective_request_id,
            },
        )
        data = BacktestOrchestrator().execute(payload)
        metadata["execution_ms"] = round((time.perf_counter() - start) * 1000, 3)
        return success_response(
            message="Simulator backtest completed.",
            data=data,
            metadata=metadata,
        )
    except SimArbitraryCodeRejectedError as exc:
        metadata["execution_ms"] = round((time.perf_counter() - start) * 1000, 3)
        logger.warning(
            "run_backtest rejected arbitrary code",
            extra={
                "event_name": "run_backtest_arbitrary_code_rejected",
                "request_id": effective_request_id,
                "error_code": exc.code,
            },
        )
        return error_response(
            message="Simulator request rejected.",
            code="SIM_ARBITRARY_CODE_REJECTED",
            details="Raw arbitrary Python strategy code is not accepted.",
            metadata=metadata,
        )
    except SimulationError as exc:
        metadata["execution_ms"] = round((time.perf_counter() - start) * 1000, 3)
        code = getattr(exc, "code", "SIM_INTERNAL_ERROR")
        logger.warning(
            "run_backtest simulator boundary failed",
            extra={
                "event_name": "run_backtest_simulation_failed",
                "request_id": effective_request_id,
                "error_code": code,
            },
        )
        return error_response(
            message="Simulator request failed.",
            code=str(code),
            details=str(exc),
            metadata=metadata,
        )
    except ValidationError as exc:
        metadata["execution_ms"] = round((time.perf_counter() - start) * 1000, 3)
        logger.warning(
            "run_backtest validation failed",
            extra={
                "event_name": "run_backtest_validation_failed",
                "request_id": effective_request_id,
            },
        )
        return error_response(
            message="Simulator request validation failed.",
            code=getattr(exc, "code", "SIM_INVALID_CONFIG"),
            details=str(exc),
            metadata=metadata,
        )
    except Exception as exc:  # noqa: BLE001
        metadata["execution_ms"] = round((time.perf_counter() - start) * 1000, 3)
        logger.exception(
            "run_backtest execution failed",
            extra={
                "event_name": "run_backtest_execution_failed",
                "request_id": effective_request_id,
            },
        )
        return error_response(
            message="Simulator execution failed.",
            code="SIM_INTERNAL_ERROR",
            details=f"{exc.__class__.__name__}: execution failed",
            metadata=metadata,
        )
