"""
Structured logging configuration for WalletMonitor.

Provides JSON logging for production environments and colored,
human-readable format for development. Supports environment-based
configuration via LOG_LEVEL and LOG_FILE variables.

Usage:
    from wallet_monitor.logging_config import setup_logging
    setup_logging()
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from typing import Any, Dict, Optional


# ---------------------------------------------------------------------------
# Request‑id middleware helpers
# ---------------------------------------------------------------------------

class _RequestIdFilter(logging.Filter):
    """Injects a per‑request ``request_id`` into every log record.

    The id is stored in ``threading.local`` storage so each thread/task
    can have its own value.
    """

    import threading
    _local = threading.local()

    @classmethod
    def set_request_id(cls, request_id: str) -> None:
        cls._local.request_id = request_id

    @classmethod
    def get_request_id(cls) -> Optional[str]:
        return getattr(cls._local, "request_id", None)

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = self.get_request_id() or "-"
        return True


# ---------------------------------------------------------------------------
# Formatter implementations
# ---------------------------------------------------------------------------

class _JsonFormatter(logging.Formatter):
    """Structured JSON formatter for production logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "request_id": getattr(record, "request_id", "-"),
        }

        # Include exception info when present
        if record.exc_info and record.exc_info[0] is not None:
            log_data["exception"] = self.formatException(record.exc_info)

        # Merge any extra fields that were attached to the record
        # via ``extra={…}`` in the logging call.
        standard_attrs = {
            "name", "msg", "args", "created", "relativeCreated",
            "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "pathname", "filename", "module", "levelno", "levelname",
            "thread", "threadName", "process", "processName", "message",
            "taskName", "request_id", "msecs", "levelname",
            "levelname", "levelname",
        }
        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in standard_attrs and not k.startswith("_")
        }
        if extras:
            log_data["extra"] = extras

        return json.dumps(log_data, default=str)


class _DevFormatter(logging.Formatter):
    """Colored, human-readable formatter for development / local use."""

    # ANSI color codes
    COLORS = {
        logging.DEBUG: "\033[36m",     # Cyan
        logging.INFO: "\033[32m",      # Green
        logging.WARNING: "\033[33m",   # Yellow
        logging.ERROR: "\033[31m",     # Red
        logging.CRITICAL: "\033[1;31m",# Bold Red
    }
    RESET = "\033[0m"
    BOLD = "\033[1m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        level = f"{color}{record.levelname:<8}{self.RESET}"
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        request_id = getattr(record, "request_id", "-")
        name = f"{self.BOLD}{record.name}{self.RESET}"

        base = (
            f"{timestamp}  {level}  {name}  "
            f"[req:{request_id}]  {record.getMessage()}"
        )

        if record.exc_info and record.exc_info[0] is not None:
            base += f"\n{self.formatException(record.exc_info)}"

        return base


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    production: Optional[bool] = None,
) -> None:
    """Configure the root logger for the WalletMonitor application.

    Parameters
    ----------
    level:
        Minimum log level as a string (e.g. ``"DEBUG"``).  Falls back
        to the ``LOG_LEVEL`` env var, then ``"INFO"``.
    log_file:
        Path to a log file for ``RotatingFileHandler``.  Falls back to
        the ``LOG_FILE`` env var.  When ``None`` / empty, only console
        output is produced.
    production:
        When *True* use JSON formatting; when *False* use colored dev
        formatting.  When *None* (the default) the module checks
        ``ENVIRONMENT`` / ``APP_ENV`` env vars for the values
        ``"production"`` or ``"prod"``.
    """

    # ── Resolve parameters from env when not explicit ──────────────────
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, level, logging.INFO)

    if log_file is None:
        log_file = os.getenv("LOG_FILE")

    if production is None:
        env = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development")).lower()
        production = env in ("production", "prod", "staging")

    # ── Build formatter ────────────────────────────────────────────────
    formatter = _JsonFormatter() if production else _DevFormatter()

    # ── Request‑id filter (shared across handlers) ─────────────────────
    req_filter = _RequestIdFilter()

    # ── Console handler ────────────────────────────────────────────────
    console_handler = logging.StreamHandler(stream=sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(req_filter)

    handlers: list[logging.Handler] = [console_handler]

    # ── Rotating file handler (optional) ───────────────────────────────
    if log_file:
        # Ensure parent directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(_JsonFormatter())  # Files always use JSON
        file_handler.addFilter(req_filter)
        handlers.append(file_handler)

    # ── Configure root logger ──────────────────────────────────────────
    root_logger = logging.getLogger()
    # Clear existing handlers to avoid duplicate output on repeated calls
    root_logger.handlers.clear()
    root_logger.setLevel(log_level)

    for handler in handlers:
        root_logger.addHandler(handler)

    # ── Quiet down noisy third‑party loggers ────────────────────────────
    for noisy in ("httpx", "httpcore", "urllib3", "asyncio"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    root_logger.info(
        "Logging configured – level=%s format=%s file=%s",
        level,
        "json" if production else "dev",
        log_file or "(stdout only)",
    )


# ---------------------------------------------------------------------------
# Convenience context‑manager / decorator for request‑id scoping
# ---------------------------------------------------------------------------

from contextlib import contextmanager
import uuid


@contextmanager
def request_id_context(request_id: Optional[str] = None):
    """Context manager that sets a ``request_id`` for the current thread.

    If *request_id* is ``None``, a new UUID4 is generated automatically.

    Example::

        with request_id_context() as rid:
            logger.info("Processing wallet %s", wallet_id)  # rid attached
    """
    rid = request_id or str(uuid.uuid4())
    _RequestIdFilter.set_request_id(rid)
    try:
        yield rid
    finally:
        _RequestIdFilter.set_request_id("-")
