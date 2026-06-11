"""Unit tests for tools/utils/logger.py."""

import io
import json
import logging
import threading
import time
from pathlib import Path
from typing import Any

from tools.utils.logger import (
    _get_trace_context,
    clear_trace_context,
    configure_logging,
    get_logger,
    redact_message,
    set_trace_context,
)


def test_secret_redaction() -> None:
    """Verify that redact_message removes sensitive credentials correctly."""
    # Use short lowercase strings to completely avoid
    # detect-secrets high entropy trigger
    secrets = [
        "password=sec",  # pragma: allowlist secret
        "api_key: abc",  # pragma: allowlist secret
        "token: eyj",  # pragma: allowlist secret
        "bot_token=123",  # pragma: allowlist secret
    ]
    for s in secrets:
        redacted = redact_message(s)
        assert "sec" not in redacted
        assert "abc" not in redacted
        assert "eyj" not in redacted


def test_json_formatter_keys_and_redaction() -> None:
    """Verify that JSONFormatter structures data with log fields and redacts secrets."""
    # Capture output
    stream = io.StringIO()
    root_logger = get_logger()
    configure_logging(level="DEBUG", use_json=True)

    # Temporary hijack handler stream
    for h in root_logger.handlers:
        if isinstance(h, logging.StreamHandler):
            h.stream = stream

    set_trace_context(
        request_id="req-123", workflow_id="wf-456", correlation_id="corr-789"
    )

    # Wrap to fit line length limit (88 chars)
    msg = "This has a password=sec secret!"
    root_logger.info(msg)  # pragma: allowlist secret

    # Reset
    clear_trace_context()

    output = stream.getvalue().strip()
    assert output
    log_dict = json.loads(output)

    assert log_dict["request_id"] == "req-123"
    assert log_dict["workflow_id"] == "wf-456"
    assert log_dict["correlation_id"] == "corr-789"
    assert log_dict["level"] == "INFO"
    assert "sec" not in log_dict["message"]
    assert "[REDACTED]" in log_dict["message"]


def test_color_console_formatter() -> None:
    """Verify console output format is datetime | level | module.function | message."""
    stream = io.StringIO()
    root_logger = get_logger()
    configure_logging(level="INFO", use_json=False, use_color=False)

    for h in root_logger.handlers:
        if isinstance(h, logging.StreamHandler):
            h.stream = stream

    root_logger.info("Normal text log message")

    output = stream.getvalue().strip()
    assert "Normal text log message" in output
    # Check parts structure
    parts = output.split(" | ")
    assert len(parts) >= 4  # datetime, level, location, msg


def test_rotating_file_logger(tmp_path: Path) -> None:
    """Verify opt-in file logging rotates files correctly."""
    log_file = tmp_path / "logs" / "app.log"
    configure_logging(
        level="DEBUG",
        use_json=True,
        log_file_path=log_file,
        max_bytes=100,  # very small to trigger rotation
        backup_count=2,
    )

    logger = get_logger()
    # Write messages to trigger rotation
    for i in range(10):
        # Avoid f-string in log statement to satisfy Ruff G004 lint
        logger.info("Log line %d writing extra bytes to trigger rotation", i)
        time.sleep(0.01)

    # Check files exist
    assert log_file.exists()
    rotated = list(tmp_path.glob("logs/app.log*"))
    assert len(rotated) > 1


def test_thread_safety_trace_context() -> None:
    """Verify thread-local correlation context doesn't leak between threads."""
    results: dict[str, Any] = {}

    def worker(name: str, req_id: str) -> None:
        set_trace_context(request_id=req_id)
        # Capture logger details inside the thread
        ctx = _get_trace_context()
        results[name] = ctx["request_id"]
        clear_trace_context()

    t1 = threading.Thread(target=worker, args=("t1", "req-A"))
    t2 = threading.Thread(target=worker, args=("t2", "req-B"))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    assert results["t1"] == "req-A"
    assert results["t2"] == "req-B"
