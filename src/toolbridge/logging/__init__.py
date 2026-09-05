"""Logging package.

Provides structured, levelled application logging via structlog.
Use ``get_logger(__name__)`` to obtain a context-bound logger in any module.
"""

from toolbridge.logging.setup import configure_logging, get_logger

__all__ = ["configure_logging", "get_logger"]
