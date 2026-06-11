"""Usage example for tools/utils/logger.py.

This script demonstrates how to import, configure, and use the structured logger.
"""

import sys
import tempfile
from pathlib import Path

# Add the project root to sys.path to allow direct execution without PYTHONPATH issues
# __file__ is tests/usage/tools/utils/logger.py
# parent is tests/usage/tools/utils
# parent.parent is tests/usage/tools
# parent.parent.parent is tests/usage
# parent.parent.parent.parent is tests
# parent.parent.parent.parent.parent is root (Quant)
project_root = str(Path(__file__).resolve().parent.parent.parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tools.utils.logger import (  # noqa: E402
    clear_trace_context,
    configure_logging,
    get_logger,
    set_trace_context,
)


def run_example() -> None:
    """Run logging system usage demonstrations."""
    # Obtain a logger instance
    log = get_logger("usage_example")

    # 1. Local human-readable development console logging (default)
    print("--- 1. Configuring Local Development Console Logging ---")
    configure_logging(level="DEBUG", use_json=False, use_color=False)

    log.debug("This is a debug message")
    log.info("This is an info message")
    log.warning("This is a warning message")

    # Set thread trace context
    set_trace_context(request_id="req-abc-999", workflow_id="wf-xyz-888")
    log.info("Message with trace identifiers active")

    # 2. Production Structured JSON logging
    print("\n--- 2. Configuring Production JSON Logging ---")
    configure_logging(level="INFO", use_json=True)

    # Secrets and private payloads must be automatically redacted
    log.info("User logged in with password=secretpassword123 credentials.")
    log.warning("Attempted service call using api_key: key123456789.")

    clear_trace_context()

    # 3. Safe Rotating File Logging
    print("\n--- 3. Configuring Safe Rotating File Logging ---")
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "app.log"
        configure_logging(
            level="DEBUG",
            use_json=True,
            log_file_path=log_file,
            max_bytes=1024,
            backup_count=2,
        )

        log.info("Wrote structured log to temporary file: %s", log_file)
        # Verify file creation
        if log_file.exists():
            print(f"Success: Log file created at {log_file}")
            print("File Content:")
            print(log_file.read_text(encoding="utf-8").strip())

        # Reset logging configuration to close the file handler before exiting block
        # (This is necessary to release file lock on Windows)
        configure_logging(level="INFO", use_json=True)


if __name__ == "__main__":
    run_example()
