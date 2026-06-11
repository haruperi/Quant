"""Public registry for the utilities domain.

This module exports approved public names only. It is import-safe and
side-effect free, meaning importing this package does not configure logging,
read configuration files, open network connections, or import heavy optional
dependencies.
"""

# The following list defines the approved public names exported by the utils domain.
# Since individual modules will be implemented incrementally, this list serves
# as the source of truth for public API boundaries.
__all__ = [
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
]
