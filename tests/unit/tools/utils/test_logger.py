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
        # Redact matches key format and replaces with REDACTED
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
    # Redaction checks: msg is redacted, so 'password=[REDACTED]'
    # replaces 'password=sec'
    # note that "This has a password=[REDACTED] secret!" contains 'sec' inside 'secret!'
    # we verify that 'password=sec' was redacted
    assert "password=sec" not in log_dict["message"]
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
    log_dir = tmp_path / "logs"
    configure_logging(
        level="DEBUG",
        use_json=True,
        log_dir_path=log_dir,
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
    app_log = log_dir / "app.log"
    assert app_log.exists()
    rotated = list(log_dir.glob("app.log*"))
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


def test_file_routing(tmp_path: Path) -> None:
    """Verify file-based logging routes correctly to app, debug, access, error logs."""
    log_dir = tmp_path / "routed_logs"
    configure_logging(
        level="DEBUG",
        use_json=False,
        log_dir_path=log_dir,
    )

    logger = get_logger("routed")

    # 1. Log a DEBUG level message
    logger.debug("Debug event message")
    # 2. Log an ACCESS log message
    logger.info("Access granted", extra={"event_name": "user_login_success"})
    # 3. Log an ERROR message
    logger.error("Database connection failed")

    # Force flush files/handlers
    for h in list(logging.getLogger("haruquant").handlers):
        h.flush()

    time.sleep(0.1)

    app_path = log_dir / "app.log"
    debug_path = log_dir / "debug.log"
    access_path = log_dir / "access.log"
    errors_path = log_dir / "errors.log"

    assert app_path.exists()
    assert debug_path.exists()
    assert access_path.exists()
    assert errors_path.exists()

    app_content = app_path.read_text(encoding="utf-8")
    debug_content = debug_path.read_text(encoding="utf-8")
    access_content = access_path.read_text(encoding="utf-8")
    errors_content = errors_path.read_text(encoding="utf-8")

    # Assert correct routing contents
    assert "Debug event message" in debug_content
    assert "Access granted" in access_content
    assert "Database connection failed" in errors_content

    # app.log must record everything
    assert "Debug event message" in app_content
    assert "Access granted" in app_content
    assert "Database connection failed" in app_content


def test_file_logging_disables_color_when_console_color_enabled(
    tmp_path: Path,
) -> None:
    """Verify ANSI color codes are only written to the terminal, not log files."""
    log_dir = tmp_path / "plain_file_logs"
    stream = io.StringIO()
    root_logger = get_logger()
    configure_logging(
        level="INFO",
        use_json=False,
        use_color=True,
        log_dir_path=log_dir,
    )

    for h in root_logger.handlers:
        if isinstance(h, logging.StreamHandler) and not isinstance(
            h,
            logging.FileHandler,
        ):
            h.stream = stream

    root_logger.info("Color should stay out of files")

    for h in list(root_logger.handlers):
        h.flush()

    console_output = stream.getvalue()
    app_content = (log_dir / "app.log").read_text(encoding="utf-8")

    assert "\033[" in console_output
    assert "\033[" not in app_content
    assert "Color should stay out of files" in app_content
