"""Project-wide structured logging utilities.

This module provides structured JSON logging for production, colorized human-readable
console logs for local development, opt-in rotating file logging, and safeguards
against logging sensitive credentials or secrets.
"""

import json
import logging
import re
import sys
import threading
from collections.abc import Mapping
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, ClassVar

# Global thread-local context for trace identifiers
# (request_id, workflow_id, correlation_id)
_log_context = threading.local()

# Default root logger name
LOGGER_NAME = "haruquant"

# RegEx patterns to detect potential secrets in keys or messages
SECRET_KEYS_PATTERN = re.compile(
    r"(pass(word)?|api_?key|token|credential|secret|private_?key|bot_?token|auth(orization)?_?header)",
    re.IGNORECASE,
)
# Matches typical JWTs, hex keys, or other generic credentials
SECRET_VALUE_PATTERN = re.compile(
    r"(eyJhbGciOi[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*)|([a-f0-9]{32,})"
)


def set_trace_context(
    request_id: str | None = None,
    workflow_id: str | None = None,
    correlation_id: str | None = None,
) -> None:
    """Set the trace correlation identifiers for the current thread context."""
    _log_context.request_id = request_id
    _log_context.workflow_id = workflow_id
    _log_context.correlation_id = correlation_id


def clear_trace_context() -> None:
    """Clear the trace context for the current thread."""
    _log_context.request_id = None
    _log_context.workflow_id = None
    _log_context.correlation_id = None


def _get_trace_context() -> dict[str, str | None]:
    """Retrieve trace context attributes for the current thread safely."""
    return {
        "request_id": getattr(_log_context, "request_id", None),
        "workflow_id": getattr(_log_context, "workflow_id", None),
        "correlation_id": getattr(_log_context, "correlation_id", None),
    }


def _redact_value(val: Any) -> Any:  # noqa: ANN401
    """Recursively redact secrets from a value.

    Checks if it looks like sensitive information.
    """
    if isinstance(val, str):
        if SECRET_VALUE_PATTERN.search(val):
            return "[REDACTED]"
        return val
    if isinstance(val, Mapping):
        return {
            str(k): (
                "[REDACTED]" if SECRET_KEYS_PATTERN.search(str(k)) else _redact_value(v)
            )
            for k, v in val.items()
        }
    if isinstance(val, list | tuple | set):
        return [_redact_value(item) for item in val]
    return val


def redact_message(msg: str) -> str:
    """Redact secrets within a raw string message."""

    # Look for API keys / passwords / secrets in format: key=value or key:value
    def replacement(match: re.Match[str]) -> str:
        return f"{match.group(1)}[REDACTED]"

    pattern = re.compile(
        r"((?:pass(?:word)?|api_?key|token|credential|secret|private_?key|bot_token|authorization)\s*[:=]\s*)[^\s,;&'\"]+",
        re.IGNORECASE,
    )
    msg = pattern.sub(replacement, msg)
    # Also find standalone JWTs or hex secret values
    msg = SECRET_VALUE_PATTERN.sub("[REDACTED]", msg)
    return msg


class JSONFormatter(logging.Formatter):
    """Production structured log formatter outputting JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        """Format a LogRecord into a JSON string."""
        trace = _get_trace_context()

        # Build basic structured dictionary
        log_data: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger_name": record.name,
            "message": redact_message(record.getMessage()),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "request_id": trace["request_id"],
            "workflow_id": trace["workflow_id"],
            "correlation_id": trace["correlation_id"],
        }

        # Handle extra parameters passed to logging calls
        if hasattr(record, "event_name"):
            log_data["event_name"] = record.event_name
        if hasattr(record, "error_code"):
            log_data["error_code"] = record.error_code

        # Clean/Redact dictionary values
        log_data = _redact_value(log_data)

        # Include exception info safely if available
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, sort_keys=True)


class ColorConsoleFormatter(logging.Formatter):
    """Local development console log formatter with colorized human-readable output."""

    # ANSI escape sequences for coloring levels
    COLORS: ClassVar[dict[str, str]] = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[41m\033[37m",  # White on Red background
    }
    RESET: ClassVar[str] = "\033[0m"

    def __init__(self, use_color: bool = True) -> None:
        """Initialize the formatter with color control."""
        super().__init__()
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record to the specified console format."""
        dt = datetime.fromtimestamp(record.created, tz=UTC).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        level = record.levelname

        # Format module path hierarchy: module.submodule.filename
        # (e.g. app.utils.logger). Resolve relative to project root.
        module_path = record.name
        if record.pathname:
            normalized_path = Path(record.pathname).resolve()
            parts = normalized_path.parts
            if "tools" in parts:
                idx = parts.index("tools")
                module_parts = list(parts[idx:])
                module_parts[-1] = normalized_path.stem
                module_path = ".".join(module_parts)
            elif "app" in parts:
                idx = parts.index("app")
                module_parts = list(parts[idx:])
                module_parts[-1] = normalized_path.stem
                module_path = ".".join(module_parts)
            elif "src" in parts:
                idx = parts.index("src")
                module_parts = list(parts[idx + 1 :])
                module_parts[-1] = normalized_path.stem
                module_path = ".".join(module_parts)
            elif "tests" in parts:
                idx = parts.index("tests")
                module_parts = list(parts[idx:])
                module_parts[-1] = normalized_path.stem
                module_path = ".".join(module_parts)

        mod_func = f"{module_path}.{record.funcName}:{record.lineno}"
        msg = redact_message(record.getMessage())

        # Redact extra fields if present
        trace = _get_trace_context()
        trace_str = ""
        if trace["request_id"] or trace["workflow_id"]:
            req = trace["request_id"] or "-"
            wf = trace["workflow_id"] or "-"
            trace_str = f" | req:{req} wf:{wf}"

        # Windows supports ANSI color escape sequences since Windows 10
        # and PowerShell handles them perfectly, so we allow colorized logs.
        if self.use_color:
            color = self.COLORS.get(level, "")
            level_str = f"{color}{level:<8}{self.RESET}"
        else:
            level_str = f"{level:<8}"

        formatted = f"{dt} | {level_str} | {mod_func} | {msg}{trace_str}"

        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        return formatted


class LogFilter(logging.Filter):
    """Custom filter to route specific types of logs.

    Filters based on record level or attributes.
    """

    def __init__(self, target: str) -> None:
        """Initialize filter with routing target.

        Targets: 'debug', 'access', 'error', 'all'
        """
        super().__init__()
        self.target = target

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records based on the routing target."""
        if self.target == "error":
            return record.levelno >= logging.ERROR
        if self.target == "debug":
            return record.levelno == logging.DEBUG
        if self.target == "access":
            # Match logs carrying 'event_name' containing access/request patterns
            event = getattr(record, "event_name", "")
            return bool(
                event
                and any(
                    x in str(event).lower()
                    for x in ("access", "request", "auth", "login")
                )
            )
        return True


def get_logger(name: str | None = None) -> logging.Logger:
    """Retrieve or create a logger.

    If name is provided, returns a child logger under the root name.
    """
    if not name:
        return logging.getLogger(LOGGER_NAME)
    if name.startswith(LOGGER_NAME):
        return logging.getLogger(name)
    return logging.getLogger(f"{LOGGER_NAME}.{name}")


# Default root logger
logger = get_logger()


def configure_logging(
    level: str | int = "DEBUG",
    *,
    use_json: bool = False,
    use_color: bool = True,
    log_dir_path: str | Path | None = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """Configure the project-wide logging system.

    Clears existing handlers to avoid duplicate log emissions. Sets up console handler
    and file-based logging (app.log, debug.log, access.log, errors.log).
    """
    root_l = logging.getLogger(LOGGER_NAME)
    numeric_level = level
    if isinstance(level, str):
        numeric_level = getattr(logging, level.upper(), logging.DEBUG)

    root_l.setLevel(numeric_level)

    # Clean existing handlers to avoid duplicates
    for h in list(root_l.handlers):
        root_l.removeHandler(h)
        h.close()

    # Formatter setup: console may be colorized, but file logs must remain plain.
    if use_json:
        console_formatter: logging.Formatter = JSONFormatter()
        file_formatter: logging.Formatter = JSONFormatter()
    else:
        console_formatter = ColorConsoleFormatter(use_color=use_color)
        file_formatter = ColorConsoleFormatter(use_color=False)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    root_l.addHandler(console_handler)

    # Multi-file routing under log directory
    if log_dir_path:
        try:
            d_path = Path(log_dir_path).resolve()
            d_path.mkdir(parents=True, exist_ok=True)

            # Files definitions: (filename, filter_target)
            files_config = [
                ("app.log", "all"),
                ("debug.log", "debug"),
                ("access.log", "access"),
                ("errors.log", "error"),
            ]

            for filename, target in files_config:
                f_path = d_path / filename
                file_handler = RotatingFileHandler(
                    f_path,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding="utf-8",
                )
                file_handler.setFormatter(file_formatter)
                file_handler.addFilter(LogFilter(target))
                root_l.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            # Degrade safely
            sys.stderr.write(f"Logging file configuration failed safely: {e}\n")
