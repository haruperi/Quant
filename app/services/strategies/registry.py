# ruff: noqa: E501, RUF012, C901, PLR0912, PLR0915, EM101, EM102, TRY301, TRY300, BLE001, B904, PLR0911, PLW2901, SIM102, SIM201, ANN401, PLR2004, RUF100
"""Thread-safe strategy registry catalog and configuration validations.

Provides support for registering strategy classes, checking constraint matches,
validating environments against lifecycle approvals, and scanning configuration
dictionaries for security vulnerabilities or dynamic code injections.
"""

from __future__ import annotations

import json
from threading import Lock
from typing import Any, cast

from pydantic import BaseModel

from app.services.strategies.protocols import (
    StrategyEnvironment,
    StrategyProtocol,
    StrategyRefInput,
)
from app.utils.errors import (
    SimArbitraryCodeRejectedError,
    StrategyConfigError,
    StrategyDeprecatedError,
    StrategyEnvironmentNotPermittedError,
    StrategyLifecycleNotApprovedError,
    StrategyNotFoundError,
    StrategyVersionConstraintUnsatisfiableError,
    ValidationError,
    map_exception_to_strategy_error,
)
from app.utils.logger import logger


def parse_version(v_str: str) -> tuple[int, ...]:
    """Parse a semantic version string into a tuple of integers for comparison."""
    clean = v_str.strip().lstrip("v")
    parts = clean.split(".")
    res = []
    for p in parts:
        num = ""
        for char in p:
            if char.isdigit():
                num += char
            else:
                break
        res.append(int(num) if num else 0)
    return tuple(res)


def match_constraint(version: str, constraint: str | None) -> bool:
    """Check if version matches the given semantic version constraint specifier."""
    if not constraint or constraint == "*":
        return True

    v_parts = parse_version(version)
    conditions = constraint.split(",")

    for cond in conditions:
        cond = cond.strip()
        if not cond:
            continue

        if cond.startswith(">="):
            op = ">="
            target = cond[2:]
        elif cond.startswith("<="):
            op = "<="
            target = cond[2:]
        elif cond.startswith(">"):
            op = ">"
            target = cond[1:]
        elif cond.startswith("<"):
            op = "<"
            target = cond[1:]
        elif cond.startswith("=="):
            op = "=="
            target = cond[2:]
        else:
            op = "=="
            target = cond

        t_parts = parse_version(target)
        max_len = max(len(v_parts), len(t_parts))
        v_padded = v_parts + (0,) * (max_len - len(v_parts))
        t_padded = t_parts + (0,) * (max_len - len(t_parts))

        if op == ">=":
            if not (v_padded >= t_padded):
                return False
        elif op == "<=":
            if not (v_padded <= t_padded):
                return False
        elif op == ">":
            if not (v_padded > t_padded):
                return False
        elif op == "<":
            if not (v_padded < t_padded):
                return False
        elif op == "==":
            if not (v_padded == t_padded):
                return False

    return True


class StrategyRegistry:
    """Thread-safe catalog registry for quantitative strategy classes."""

    def __init__(self) -> None:
        """Initialize lock and strategy registries map."""
        self._lock = Lock()
        self._registry: dict[str, dict[str, type[StrategyProtocol]]] = {}

    def register_strategy(self, strategy_class: type[StrategyProtocol]) -> None:
        """Register a strategy class in the catalog, verifying no duplicate exists."""
        # Conformance check
        res = validate_strategy_class(strategy_class)
        if not res.valid:
            raise ValidationError(f"Strategy class does not conform: {res.message}")

        strat_id = getattr(strategy_class, "strategy_id", None)
        version = getattr(strategy_class, "version", None)

        if not isinstance(strat_id, str) or not strat_id:
            raise ValidationError("Strategy class must define non-empty 'strategy_id'.")
        if not isinstance(version, str) or not version:
            raise ValidationError("Strategy class must define non-empty 'version'.")

        strat_id_lower = strat_id.lower()

        with self._lock:
            if strat_id_lower not in self._registry:
                self._registry[strat_id_lower] = {}

            # REQ-STRAT-070: Duplicate strategy id/version registry entries shall fail registry validation deterministically
            if version in self._registry[strat_id_lower]:
                msg = f"Duplicate strategy registry entry: {strat_id} version {version} is already registered."
                logger.error(msg)
                raise ValidationError(msg)

            self._registry[strat_id_lower][version] = strategy_class
            logger.info(f"Registered strategy: {strat_id} (v{version})")

    def get_strategy(
        self, strategy_id: str, version_constraint: str | None = None
    ) -> type[StrategyProtocol]:
        """Fetch the registered strategy class that matches constraints."""
        strat_id_lower = strategy_id.lower()
        with self._lock:
            if strat_id_lower not in self._registry:
                raise StrategyNotFoundError(
                    f"Strategy '{strategy_id}' is not registered."
                )

            versions = self._registry[strat_id_lower]
            matching_classes = []

            for ver, cls in versions.items():
                if match_constraint(ver, version_constraint):
                    matching_classes.append((parse_version(ver), cls))

            if not matching_classes:
                raise StrategyVersionConstraintUnsatisfiableError(
                    f"No matching version for strategy '{strategy_id}' satisfies constraint '{version_constraint}'."
                )

            # Return the highest matching version class
            matching_classes.sort(key=lambda x: x[0])
            return matching_classes[-1][1]

    def unregister_strategy(self, strategy_id: str, version: str | None = None) -> None:
        """Remove strategy classes from the registry catalog."""
        strat_id_lower = strategy_id.lower()
        with self._lock:
            if strat_id_lower in self._registry:
                if version is not None:
                    if version in self._registry[strat_id_lower]:
                        del self._registry[strat_id_lower][version]
                        logger.info(
                            f"Unregistered strategy: {strategy_id} version {version}"
                        )
                    if not self._registry[strat_id_lower]:
                        del self._registry[strat_id_lower]
                else:
                    del self._registry[strat_id_lower]
                    logger.info(f"Unregistered all versions of strategy: {strategy_id}")

    def list_strategies(self) -> list[str]:
        """Return sorted registered strategy identifiers with their versions."""
        res = []
        with self._lock:
            for s_id, vers in self._registry.items():
                for ver in vers:
                    res.append(f"{s_id}:{ver}")
        return sorted(res)


class ValidationResult:
    """Wrapper holding strategy class conformance audit details."""

    def __init__(self, valid: bool, message: str) -> None:
        """Initialize the validation result."""
        self.valid = valid
        self.message = message


def validate_strategy_class(strategy_class: Any) -> ValidationResult:
    """Perform static typing conformance audits on candidate strategy classes."""
    required_attrs = [
        "strategy_id",
        "version",
        "lifecycle_status",
        "permitted_environments",
    ]
    for attr in required_attrs:
        if not hasattr(strategy_class, attr):
            return ValidationResult(False, f"Missing required class attribute: {attr}")

    allowed_statuses = (
        "DRAFT",
        "RESEARCH",
        "BACKTEST_APPROVED",
        "PAPER_APPROVED",
        "LIVE_ELIGIBLE",
        "DEPRECATED",
        "REVOKED",
    )
    status = strategy_class.lifecycle_status
    if status not in allowed_statuses:
        return ValidationResult(
            False,
            f"Invalid lifecycle status '{status}'. Must be one of {allowed_statuses}.",
        )

    required_methods = ["run_vectorized_signals"]
    for method in required_methods:
        if not hasattr(strategy_class, method) or not callable(
            getattr(strategy_class, method)
        ):
            return ValidationResult(False, f"Missing required method: {method}")

    return ValidationResult(True, "Strategy conforms to protocols.")


# Singleton registry instance
global_registry = StrategyRegistry()


def register_strategy(strategy_class: type[StrategyProtocol]) -> None:
    """Register a strategy class in the catalog."""
    global_registry.register_strategy(strategy_class)


def get_strategy(
    strategy_id: str, version_constraint: str | None = None
) -> type[StrategyProtocol]:
    """Retrieve the strategy class that satisfies constraint specs."""
    return global_registry.get_strategy(strategy_id, version_constraint)


def unregister_strategy(strategy_id: str, version: str | None = None) -> None:
    """Unregister the specified strategy versions."""
    global_registry.unregister_strategy(strategy_id, version)


def list_strategies() -> list[str]:
    """List registered strategy tokens."""
    return global_registry.list_strategies()


def validate_strategy_ref(
    strategy_id: str,
    version_constraint: str | None = None,
    environment: StrategyEnvironment = "BACKTEST",
    request_id: str | None = None,
) -> dict[str, Any]:
    """Validate requested strategy identifiers, version constraints, and lifecycle environments.

    Returns:
        Standard response dict with success status and resolved refs or error fields.
    """
    try:
        if not strategy_id:
            # REQ-STRAT-325: Empty strategy identifier shall fail
            raise StrategyNotFoundError("Strategy identifier must not be empty.")

        strat_class = get_strategy(strategy_id, version_constraint)

        # Environment check
        permitted = getattr(strat_class, "permitted_environments", [])
        if environment not in permitted:
            raise StrategyEnvironmentNotPermittedError(
                f"Strategy is not permitted to execute in environment '{environment}'."
            )

        # Lifecycle check
        status = getattr(strat_class, "lifecycle_status", "DRAFT")
        if status in ("DEPRECATED", "REVOKED") and environment != "REPLAY":
            raise StrategyDeprecatedError(
                f"Strategy '{strategy_id}' is {status} and cannot be executed outside of REPLAY environment."
            )

        env_min_status: dict[StrategyEnvironment, str] = {
            "LIVE": "LIVE_ELIGIBLE",
            "SHADOW": "PAPER_APPROVED",
            "PAPER": "PAPER_APPROVED",
            "REPLAY": "BACKTEST_APPROVED",
            "BACKTEST": "DRAFT",
        }

        status_levels = {
            "DRAFT": 0,
            "RESEARCH": 1,
            "BACKTEST_APPROVED": 2,
            "PAPER_APPROVED": 3,
            "LIVE_ELIGIBLE": 4,
            "DEPRECATED": -1,
            "REVOKED": -2,
        }

        required_status = env_min_status.get(environment, "DRAFT")
        if status_levels.get(status, 0) < status_levels.get(required_status, 0):
            raise StrategyLifecycleNotApprovedError(
                f"Strategy lifecycle status '{status}' is insufficient for environment '{environment}'. "
                f"Requires at least '{required_status}'."
            )

        resolved_ref = StrategyRefInput(
            strategy_id=str(strat_class.strategy_id),
            version=str(strat_class.version),
            version_constraint=version_constraint,
            environment=environment,
            request_id=request_id,
        )

        return {
            "status": "success",
            "message": "Strategy reference validated successfully.",
            "data": {
                "strategy_ref": resolved_ref,
                "strategy_class": strat_class,
            },
            "error": None,
            "metadata": {
                "request_id": request_id,
            },
        }

    except Exception as exc:
        mapped = map_exception_to_strategy_error(exc)
        return {
            "status": "error",
            "message": f"Strategy validation failed: {exc}",
            "data": None,
            "error": {
                "code": mapped.code,
                "details": str(exc),
            },
            "metadata": {
                "request_id": request_id,
            },
        }


def validate_config_security(
    config: Any,
    max_nesting_depth: int = 10,
    max_string_length: int = 1000,
    max_collection_length: int = 1000,
    current_depth: int = 0,
) -> None:
    """Recursively scan configuration payload to reject malicious code injections and limit sizes."""
    if current_depth > max_nesting_depth:
        raise StrategyConfigError("Configuration nesting depth limit exceeded.")

    # Blocked keywords/injection patterns
    blocked_keywords = [
        "eval(",
        "exec(",
        "__import__",
        "subprocess",
        "os.system",
        "shutil",
        "open(",
        "import ",
        "sys.",
        "getattr",
        "setattr",
        "delattr",
        "__class__",
        "__subclasses__",
        "__globals__",
        "__builtins__",
        "__code__",
        "__init__",
        "template",
        "jinja2",
        "mako",
        "lambda",
    ]

    if isinstance(config, str):
        if len(config) > max_string_length:
            raise StrategyConfigError(
                f"Configuration string length exceeds maximum: {max_string_length}"
            )

        for kw in blocked_keywords:
            if kw in config:
                logger.warning(
                    f"Code injection security pattern '{kw}' detected in strategy config string.",
                    extra={
                        "event_name": "config_security_injection_blocked",
                        "blocked_keyword": kw,
                    },
                )
                raise SimArbitraryCodeRejectedError(
                    f"Configuration parameter rejected due to unsafe pattern/code injection: keyword '{kw}' found",
                    code="SIM_ARBITRARY_CODE_REJECTED",
                )

    elif isinstance(config, dict):
        if len(config) > max_collection_length:
            raise StrategyConfigError(
                f"Configuration collection size exceeds limit: {max_collection_length}"
            )
        for k, v in config.items():
            validate_config_security(
                k,
                max_nesting_depth,
                max_string_length,
                max_collection_length,
                current_depth + 1,
            )
            validate_config_security(
                v,
                max_nesting_depth,
                max_string_length,
                max_collection_length,
                current_depth + 1,
            )

    elif isinstance(config, list | tuple | set):
        if len(config) > max_collection_length:
            raise StrategyConfigError(
                f"Configuration collection size exceeds limit: {max_collection_length}"
            )
        for item in config:
            validate_config_security(
                item,
                max_nesting_depth,
                max_string_length,
                max_collection_length,
                current_depth + 1,
            )


def validate_dict_by_json_schema(
    config: dict[str, Any],
    schema: dict[str, Any],
    unknown_field_policy: str = "REJECT",
) -> dict[str, Any]:
    """Validate a dictionary against a basic JSON Schema.

    Args:
        config: Configuration dictionary.
        schema: The JSON Schema definition.
        unknown_field_policy: Defines how to handle unknown fields ("REJECT" or "IGNORE").

    Returns:
        Validated config dictionary with defaults applied.

    Raises:
        StrategyConfigError: If schema validation fails.
    """
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    # 1. Reject unknown fields if policy is REJECT
    if unknown_field_policy == "REJECT":
        extra_fields = set(config).difference(properties)
        if extra_fields:
            raise StrategyConfigError(f"Unknown configuration fields: {extra_fields}")

    validated = {}

    # 2. Iterate properties in the schema
    for name, prop in properties.items():
        if name not in config:
            if "default" in prop:
                validated[name] = prop["default"]
            elif name in required:
                raise StrategyConfigError(f"Missing required field: '{name}'")
            continue

        val = config[name]
        val_type = prop.get("type")

        # Type check
        if val_type == "string":
            if not isinstance(val, str):
                raise StrategyConfigError(
                    f"Field '{name}' must be a string, got {type(val).__name__}"
                )
        elif val_type == "integer":
            if not isinstance(val, int) or isinstance(val, bool):
                raise StrategyConfigError(
                    f"Field '{name}' must be an integer, got {type(val).__name__}"
                )
        elif val_type == "number":
            if not isinstance(val, int | float) or isinstance(val, bool):
                raise StrategyConfigError(
                    f"Field '{name}' must be a number, got {type(val).__name__}"
                )
        elif val_type == "boolean":
            if not isinstance(val, bool):
                raise StrategyConfigError(
                    f"Field '{name}' must be a boolean, got {type(val).__name__}"
                )

        # Numeric bounds checking
        if val_type in ("integer", "number"):
            minimum = prop.get("minimum")
            if minimum is not None and val < minimum:
                raise StrategyConfigError(
                    f"Field '{name}' must be greater than or equal to {minimum}, got {val}"
                )
            maximum = prop.get("maximum")
            if maximum is None:
                maximum = prop.get("max")
            if maximum is not None and val > maximum:
                raise StrategyConfigError(
                    f"Field '{name}' must be less than or equal to {maximum}, got {val}"
                )
            step = prop.get("step")
            if step is not None:
                import math

                remainder = val % step
                if not (
                    math.isclose(remainder, 0, abs_tol=1e-9)
                    or math.isclose(remainder, step, abs_tol=1e-9)
                ):
                    raise StrategyConfigError(
                        f"Field '{name}' must be a multiple of step size {step}, got {val}"
                    )

        validated[name] = val

    # Copy over extra fields if policy is IGNORE
    if unknown_field_policy == "IGNORE":
        for k, v in config.items():
            if k not in validated:
                validated[k] = v

    return validated


def validate_strategy_config(
    strategy_class: type[StrategyProtocol],
    config: dict[str, Any],
    unknown_field_policy: str = "REJECT",
) -> dict[str, Any]:
    """Validate strategy configuration schema and check for security vulnerabilities.

    Args:
        strategy_class: The target strategy class.
        config: Dictionary containing user-supplied config parameters.
        unknown_field_policy: Defines how to handle unknown fields ("REJECT" or "IGNORE").

    Returns:
        Validated config dictionary.
    """
    # Enforce payload size limit (64 KB)
    try:
        json_str = json.dumps(config)
        if len(json_str.encode("utf-8")) > 65536:
            raise StrategyConfigError(
                "Configuration payload exceeds maximum allowed size (64 KB)."
            )
    except Exception as exc:
        if isinstance(exc, StrategyConfigError):
            raise
        raise StrategyConfigError(f"Configuration is not JSON-serializable: {exc}")

    # Security check
    validate_config_security(config)

    # Schema check if class declares a Pydantic config_model
    config_model = getattr(strategy_class, "config_model", None)
    if config_model and issubclass(config_model, BaseModel):
        try:
            if unknown_field_policy == "REJECT":
                model_fields = (
                    config_model.model_fields
                    if hasattr(config_model, "model_fields")
                    else config_model.__fields__
                )
                extra_fields = set(config).difference(model_fields)
                if extra_fields:
                    raise StrategyConfigError(
                        f"Unknown configuration fields: {extra_fields}"
                    )

            validated = config_model(**config)
            return cast(
                "dict[str, Any]",
                validated.model_dump()
                if hasattr(validated, "model_dump")
                else validated.dict(),
            )
        except Exception as exc:
            if isinstance(exc, StrategyConfigError):
                raise
            raise StrategyConfigError(f"Configuration schema validation failed: {exc}")

    # Check JSON schema if class declares a config_schema dict
    config_schema = getattr(strategy_class, "config_schema", None)
    if config_schema and isinstance(config_schema, dict):
        try:
            return validate_dict_by_json_schema(
                config, config_schema, unknown_field_policy
            )
        except Exception as exc:
            if isinstance(exc, StrategyConfigError):
                raise
            raise StrategyConfigError(f"Configuration schema validation failed: {exc}")

    return dict(config)
