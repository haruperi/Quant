"""Unit tests for the tools/utils registry."""

import sys


def test_utils_registry_exports() -> None:
    """Verify that only the approved public names are declared in __all__."""
    import tools.utils

    expected_exports = {
        "ConfigurationError",
        "DataError",
        "Error",
        "ExternalServiceError",
        "SecurityError",
        "StandardEnvelope",
        "StandardResponse",
        "ValidationError",
        "configure_logging",
        "error_name",
        "get_execution_ms",
        "get_logger",
        "logger",
        "message_for",
    }

    assert hasattr(tools.utils, "__all__")
    assert set(tools.utils.__all__) == expected_exports


def test_registry_import_side_effects() -> None:
    """Verify that importing tools.utils does not run unwanted side-effects.

    Specifically, check that heavy modules like pandas, cryptography, etc.
    are not loaded into sys.modules just by importing tools.utils.
    """
    # Ensure tools.utils is not yet imported (or clean it if it is)
    if "tools.utils" in sys.modules:
        del sys.modules["tools.utils"]

    import tools.utils  # noqa: F401

    # Assert that heavy optional libraries are not eagerly loaded
    assert "pandas" not in sys.modules
    assert "cryptography" not in sys.modules
    assert "dotenv" not in sys.modules
