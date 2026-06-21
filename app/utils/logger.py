"""Project-wide structured logging utilities.

This module is a support helper, not an official AI tool. It provides
structured JSON logging for production, colorized human-readable console
logs for local development, opt-in rotating file logging, and safeguards
against logging sensitive credentials or secrets.

Public exports:
    LOGGER_NAME, logger, get_logger, configure_logging,
    set_trace_context, clear_trace_context, redact_message.

Side effects:
    Importing this module creates a module-level ``threading.local()``
    context store and a root ``logging.Logger`` instance named
    ``haruquant``. No handlers are attached until ``configure_logging``
    is called explicitly.
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

# ---------------------------------------------------------------------------
# Module-level state (immutable after assignment)
# ---------------------------------------------------------------------------

# Thread-local store for request_id / workflow_id / correlation_id.
_log_context: threading.local = threading.local()

# Lock guarding handler reconfiguration to prevent duplicate-handler races.
_configure_lock: threading.Lock = threading.Lock()

# Root logger name for the entire project.
LOGGER_NAME: str = "haruquant"

# Regex: detect secret-bearing keys in mappings.
SECRET_KEYS_PATTERN: re.Pattern[str] = re.compile(
    r"(pass(word)?|api_?key|token|credential|secret"
    r"|private_?key|bot_?token|auth(orization)?_?header)",
    re.IGNORECASE,
)

# Regex: detect JWTs or long hex credentials in string values.
SECRET_VALUE_PATTERN: re.Pattern[str] = re.compile(
    r"(eyJhbGciOi[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_.+/=]*)"
    r"|([a-f0-9]{32,})",
)

# Regex: detect inline key=value or key:value credential patterns in messages.
_SECRET_INLINE_PATTERN: re.Pattern[str] = re.compile(
    r"((?:pass(?:word)?|api_?key|token|credential|secret"
    r"|private_?key|bot_token|authorization)\s*[:=]\s*)[^\s,;&'\"]+",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Trace context helpers
# ---------------------------------------------------------------------------


def set_trace_context(
    request_id: str | None = None,
    workflow_id: str | None = None,
    correlation_id: str | None = None,
) -> None:
    """Store trace correlation identifiers in the current thread's context.

    Call this at the entry point of a request or workflow before any
    logging takes place so that all log records emitted on this thread
    automatically carry the identifiers.

    Args:
        request_id: Unique identifier for the current request.
        workflow_id: Identifier for the owning workflow or agent run.
        correlation_id: Cross-service correlation identifier.

    Returns:
        None.

    Side effects:
        Mutates the thread-local ``_log_context`` store.
    """
    _log_context.request_id = request_id
    _log_context.workflow_id = workflow_id
    _log_context.correlation_id = correlation_id


def clear_trace_context() -> None:
    """Reset all trace identifiers for the current thread to ``None``.

    Call this at the end of a request or workflow to prevent trace
    identifiers from leaking into unrelated log records on pooled threads.

    Returns:
        None.

    Side effects:
        Mutates the thread-local ``_log_context`` store.
    """
    _log_context.request_id = None
    _log_context.workflow_id = None
    _log_context.correlation_id = None


def _get_trace_context() -> dict[str, str | None]:
    """Return the current thread's trace context safely.

    Returns:
        Mapping with ``request_id``, ``workflow_id``, and
        ``correlation_id`` keys. Values are ``None`` when not set.

    Side effects:
        None.
    """
    return {
        "request_id": getattr(_log_context, "request_id", None),
        "workflow_id": getattr(_log_context, "workflow_id", None),
        "correlation_id": getattr(_log_context, "correlation_id", None),
    }


# ---------------------------------------------------------------------------
# Secret redaction helpers
# ---------------------------------------------------------------------------


def _redact_value(value: Any) -> Any:  # noqa: ANN401
    """Recursively redact secret-like values from an arbitrary structure.

    Args:
        value: Any Python value — string, mapping, sequence, or scalar.

    Returns:
        A copy of ``value`` with secrets replaced by ``"[REDACTED]"``.
        Non-string scalars are returned unchanged.

    Side effects:
        None.
    """
    if isinstance(value, str):
        if SECRET_VALUE_PATTERN.search(value):
            return "[REDACTED]"
        return value
    if isinstance(value, Mapping):
        return {
            str(k): (
                "[REDACTED]" if SECRET_KEYS_PATTERN.search(str(k)) else _redact_value(v)
            )
            for k, v in value.items()
        }
    if isinstance(value, list | tuple | set):
        return [_redact_value(item) for item in value]
    return value


def redact_message(msg: str) -> str:
    """Redact secret-like patterns from a plain log message string.

    Handles ``key=value`` and ``key:value`` inline credential patterns as
    well as standalone JWT and long hex key values.

    Args:
        msg: Raw log message string.

    Returns:
        Copy of ``msg`` with secrets replaced by ``"[REDACTED]"``.

    Side effects:
        None.
    """
    redacted = _SECRET_INLINE_PATTERN.sub(r"\1[REDACTED]", msg)
    return SECRET_VALUE_PATTERN.sub("[REDACTED]", redacted)


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------


class JSONFormatter(logging.Formatter):
    """Production structured log formatter that outputs JSON lines.

    Each log record is serialized as a single-line JSON object containing
    all required fields plus optional trace and event fields.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record into a structured JSON string.

        Args:
            record: The log record to format.

        Returns:
            Single-line JSON string with all required log fields.

        Side effects:
            None.
        """
        trace = _get_trace_context()
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
        if hasattr(record, "event_name"):
            log_data["event_name"] = record.event_name
        if hasattr(record, "error_code"):
            log_data["error_code"] = record.error_code

        log_data = _redact_value(log_data)

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, sort_keys=True)


class ColorConsoleFormatter(logging.Formatter):
    """Local development console formatter with colorized human-readable output.

    Produces lines in the format::

        YYYY-MM-DD HH:MM:SS | LEVEL    | module.filename:function:line | message

    ANSI colors are applied to the level token when ``use_color=True``.
    Windows 10+ and PowerShell support ANSI sequences natively.
    """

    COLORS: ClassVar[dict[str, str]] = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[41m\033[37m",
    }
    RESET: ClassVar[str] = "\033[0m"

    def __init__(self, use_color: bool = True) -> None:
        """Initialize the formatter.

        Args:
            use_color: Whether to apply ANSI color codes to the level token.

        Side effects:
            None.
        """
        super().__init__()
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        """Format a log record into the approved console line format.

        Args:
            record: The log record to format.

        Returns:
            Formatted string: ``timestamp | level | path:function:line | msg``.

        Side effects:
            None.
        """
        dt = datetime.fromtimestamp(record.created, tz=UTC).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        level = record.levelname
        module_path = self._resolve_module_path(record)
        # Required format: module.submodule.filename:function:line
        mod_func = f"{module_path}:{record.funcName}:{record.lineno}"
        msg = redact_message(record.getMessage())

        trace = _get_trace_context()
        trace_str = ""
        if trace["request_id"] or trace["workflow_id"]:
            req = trace["request_id"] or "-"
            wf = trace["workflow_id"] or "-"
            trace_str = f" | req:{req} wf:{wf}"

        if self.use_color:
            color = self.COLORS.get(level, "")
            level_str = f"{color}{level:<8}{self.RESET}"
        else:
            level_str = f"{level:<8}"

        formatted = f"{dt} | {level_str} | {mod_func} | {msg}{trace_str}"
        if record.exc_info:
            formatted += "\n" + self.formatException(record.exc_info)
        return formatted

    @staticmethod
    def _resolve_module_path(record: logging.LogRecord) -> str:
        """Derive a dotted module path from the log record's file path.

        Anchors resolution at the first occurrence of standard project
        root directories (``app``, ``tools``, ``src``, ``tests``).  Falls
        back to ``record.name`` when no anchor is found.

        Args:
            record: The log record to inspect.

        Returns:
            Dotted module path ending with the filename stem.

        Side effects:
            None.
        """
        if not record.pathname:
            return record.name
        normalized = Path(record.pathname).resolve()
        parts = normalized.parts
        for anchor in ("tools", "app", "tests"):
            if anchor in parts:
                idx = parts.index(anchor)
                module_parts = list(parts[idx:])
                module_parts[-1] = normalized.stem
                return ".".join(module_parts)
        if "src" in parts:
            idx = parts.index("src")
            module_parts = list(parts[idx + 1 :])
            module_parts[-1] = normalized.stem
            return ".".join(module_parts)
        return record.name


# ---------------------------------------------------------------------------
# Log filter
# ---------------------------------------------------------------------------


class LogFilter(logging.Filter):
    """Route-based log filter for multi-file handler setups.

    Allows a handler to receive only a specific category of log records
    based on the ``target`` routing key.
    """

    def __init__(self, target: str) -> None:
        """Initialize the filter with a routing target.

        Args:
            target: One of ``"all"``, ``"debug"``, ``"access"``,
                or ``"error"``.

        Side effects:
            None.
        """
        super().__init__()
        self.target = target

    def filter(self, record: logging.LogRecord) -> bool:
        """Return whether ``record`` passes this filter.

        Args:
            record: The candidate log record.

        Returns:
            ``True`` when the record matches the configured target.

        Side effects:
            None.
        """
        if self.target == "error":
            return record.levelno >= logging.ERROR
        if self.target == "debug":
            return record.levelno == logging.DEBUG
        if self.target == "access":
            event = getattr(record, "event_name", "")
            return bool(
                event
                and any(
                    x in str(event).lower()
                    for x in ("access", "request", "auth", "login")
                )
            )
        return True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a logger under the stable ``haruquant`` root namespace.

    Use this in every module that needs structured logging. Child loggers
    inherit the root logger's handlers and level configuration.

    Args:
        name: Optional sub-logger name. If omitted or empty, the root
            ``haruquant`` logger is returned. If the name already starts
            with ``haruquant``, it is used as-is; otherwise it is
            prefixed with ``haruquant.``.

    Returns:
        A ``logging.Logger`` instance under the ``haruquant`` namespace.

    Side effects:
        None beyond the stdlib ``logging.getLogger`` registry update.
    """
    if not name:
        return logging.getLogger(LOGGER_NAME)
    if name.startswith(LOGGER_NAME):
        return logging.getLogger(name)
    return logging.getLogger(f"{LOGGER_NAME}.{name}")


# Module-level root logger — export as a support object only.
logger: logging.Logger = get_logger()


def _bootstrap_default_handler() -> None:
    """Attach a minimal default console handler if none exists yet.

    Called once at module import time so that every log record emitted
    before an explicit ``configure_logging()`` call still uses the
    approved ``timestamp | level | path:function:line | message`` format
    instead of Python's built-in ``WARNING:name:message`` fallback.

    ``configure_logging()`` clears this handler when it runs, so there
    is no conflict with production setup.  This is library-level
    bootstrap, not application-level configuration: it performs no file
    I/O, no JSON serialisation, and no network operations.
    """
    if "pytest" in sys.modules:
        return
    root_l = logging.getLogger(LOGGER_NAME)
    if root_l.handlers:
        return
    root_l.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ColorConsoleFormatter(use_color=True))
    root_l.addHandler(handler)


_bootstrap_default_handler()


def configure_logging(
    level: str | int = "INFO",
    *,
    use_json: bool = False,
    use_color: bool = True,
    log_dir_path: str | Path | None = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> None:
    """Configure the project-wide logging system.

    This is the only approved entry-point for attaching handlers. It must
    be called explicitly at application startup; importing this module
    does not configure any handlers.

    Clears existing handlers before applying the new configuration to
    prevent duplicate log records. The operation is protected by a module
    lock to prevent duplicate-handler races under concurrent startup
    threads.

    Args:
        level: Root log level as a string (``"DEBUG"``, ``"INFO"``,
            ``"WARNING"``, ``"ERROR"``, ``"CRITICAL"``) or an integer
            constant from the ``logging`` module.  Defaults to
            ``"INFO"``.  An unrecognized string raises ``ValueError``.
        use_json: When ``True``, attach a ``JSONFormatter`` to both the
            console and file handlers (production mode).  When ``False``
            (default), attach a ``ColorConsoleFormatter`` (development
            mode).
        use_color: When ``True`` (default), apply ANSI color codes to
            the console level token.  Ignored when ``use_json`` is
            ``True``.
        log_dir_path: Optional filesystem path to a directory for
            rotating file handlers.  File logging is **opt-in**: passing
            ``None`` (default) disables it entirely.
        max_bytes: Maximum size of each rotating log file in bytes.
            Defaults to 10 MiB.
        backup_count: Number of rotated backup files to retain.
            ``RotatingFileHandler`` deletes older backups automatically.
            Defaults to 5.

    Returns:
        None.

    Raises:
        ValueError: If ``level`` is a string that is not a recognized
            Python logging level name.

    Side effects:
        Attaches handlers to the root ``haruquant`` logger and sets its
        level.  Writes to ``sys.stderr`` if file handler setup fails so
        that the console handler remains operational.
    """
    numeric_level: int
    if isinstance(level, str):
        resolved = getattr(logging, level.upper(), None)
        if resolved is None:
            msg = (
                f"Unknown log level: {level!r}. "
                "Expected DEBUG, INFO, WARNING, ERROR, or CRITICAL."
            )
            raise ValueError(msg)
        numeric_level = resolved
    else:
        numeric_level = int(level)

    with _configure_lock:
        root_l = logging.getLogger(LOGGER_NAME)
        root_l.setLevel(numeric_level)

        for handler in list(root_l.handlers):
            root_l.removeHandler(handler)
            handler.close()

        if use_json:
            console_formatter: logging.Formatter = JSONFormatter()
            file_formatter: logging.Formatter = JSONFormatter()
        else:
            console_formatter = ColorConsoleFormatter(use_color=use_color)
            file_formatter = ColorConsoleFormatter(use_color=False)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        root_l.addHandler(console_handler)

        if log_dir_path:
            try:
                d_path = Path(log_dir_path).resolve()
                d_path.mkdir(parents=True, exist_ok=True)
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
            except (OSError, PermissionError) as exc:
                sys.stderr.write(f"Logging file configuration failed safely: {exc}\n")
