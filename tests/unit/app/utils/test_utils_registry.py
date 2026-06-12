"""Unit tests for the app.utils registry."""

import sys


def test_utils_registry_exports() -> None:
    """Verify that only the approved public names are declared in __all__."""
    import app.utils

    required_exports = {
        "MetricRegistry",
        "NotificationRouter",
        "InMemoryEventBus",
        "validate_ohlcv_quality",
        "validate_input_schema",
        "redact_payload",
        "validate_auth_context",
        "route_error",
        "CircuitBreaker",
    }

    assert hasattr(app.utils, "__all__")
    assert required_exports <= set(app.utils.__all__)
    assert all(not name.startswith("_") for name in app.utils.__all__)
    assert len(app.utils.__all__) == len(set(app.utils.__all__))


def test_registry_import_side_effects() -> None:
    """Verify that importing app.utils does not run unwanted side-effects.

    Specifically, check that heavy modules like pandas, cryptography, etc.
    are not loaded into sys.modules just by importing app.utils.
    """
    for module_name in ("app.utils", "pandas", "cryptography", "dotenv"):
        sys.modules.pop(module_name, None)

    import app.utils  # noqa: F401

    # Assert that heavy optional libraries are not eagerly loaded
    assert "pandas" not in sys.modules
    assert "cryptography" not in sys.modules
    assert "dotenv" not in sys.modules
