"""Structured logging setup using structlog.

Logging conventions
-------------------
* In development (``app_env != "production"``): coloured, human-readable console output.
* In production: machine-parseable JSON lines.

Standard fields present in every log record:

    timestamp   ISO-8601 UTC timestamp
    level       Log level string (info, warning, …)
    logger      Dotted module name of the caller
    message     Human-readable event description

Context fields injected per-request (Phase 2+):

    request_id  UUID string identifying the HTTP request

Usage::

    from toolbridge.logging import get_logger

    logger = get_logger(__name__)
    logger.info("server.started", port=8000)
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.types import FilteringBoundLogger


def configure_logging(*, log_level: str = "INFO", production: bool = False) -> None:
    """Configure structlog and stdlib logging.

    Should be called exactly once at application startup before any log
    messages are emitted.

    Args:
        log_level: One of DEBUG / INFO / WARNING / ERROR / CRITICAL.
        production: When True, emit JSON lines; otherwise emit dev-friendly
                    coloured output.
    """
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
    ]

    if production:
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    # Quieten noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> FilteringBoundLogger:
    """Return a structlog bound logger for *name* (typically ``__name__``).

    Args:
        name: Logger name, usually the module's ``__name__``.

    Returns:
        A structlog ``FilteringBoundLogger`` ready to use.
    """
    return structlog.get_logger(name)  # type: ignore[no-any-return]
