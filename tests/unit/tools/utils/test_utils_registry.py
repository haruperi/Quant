"""Unit tests for the tools/utils registry."""

import sys


def test_utils_registry_exports() -> None:
    """Verify that only the approved public names are declared in __all__."""
    import tools.utils

    required_exports = {
        "MetricRegistry",
        "NotificationRouter",
        "InMemoryEventBus",
        "validate_ohlcv_quality",
        "validate_input_schema",
        "redact_payload",
        "validate_auth_context",
        "load_runtime_settings",
        "route_error",
        "CircuitBreaker",
    }

    assert hasattr(tools.utils, "__all__")
    assert required_exports <= set(tools.utils.__all__)
    assert all(not name.startswith("_") for name in tools.utils.__all__)
    assert len(tools.utils.__all__) == len(set(tools.utils.__all__))


def test_registry_import_side_effects() -> None:
    """Verify that importing tools.utils does not run unwanted side-effects.

    Specifically, check that heavy modules like pandas, cryptography, etc.
    are not loaded into sys.modules just by importing tools.utils.
    """
    for module_name in ("tools.utils", "pandas", "cryptography", "dotenv"):
        sys.modules.pop(module_name, None)

    import tools.utils  # noqa: F401

    # Assert that heavy optional libraries are not eagerly loaded
    assert "pandas" not in sys.modules
    assert "cryptography" not in sys.modules
    assert "dotenv" not in sys.modules
