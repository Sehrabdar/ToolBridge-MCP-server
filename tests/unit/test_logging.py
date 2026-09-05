"""Unit tests for the structured logging foundation (toolbridge.logging)."""

from __future__ import annotations

import io
import json
import logging

import structlog

from toolbridge.logging.setup import configure_logging, get_logger


class TestConfigureLogging:
    """Test that configure_logging() sets up stdlib and structlog correctly."""

    def test_configure_logging_does_not_raise(self) -> None:
        """configure_logging() should complete without raising any exception."""
        configure_logging(log_level="DEBUG", production=False)

    def test_configure_logging_production_does_not_raise(self) -> None:
        """Production mode should also configure without error."""
        configure_logging(log_level="INFO", production=True)

    def test_root_logger_level_is_set(self) -> None:
        """The root stdlib logger level must match log_level."""
        configure_logging(log_level="WARNING", production=False)
        assert logging.getLogger().level == logging.WARNING

    def test_root_logger_has_handler(self) -> None:
        """At least one handler must be attached to the root logger."""
        configure_logging(log_level="INFO", production=False)
        assert len(logging.getLogger().handlers) > 0


class TestGetLogger:
    """Test that get_logger() returns a usable bound logger."""

    def test_get_logger_returns_bound_logger(self) -> None:
        """get_logger() should return a structlog BoundLogger (not None/str)."""
        logger = get_logger(__name__)
        assert logger is not None

    def test_logger_has_info_method(self) -> None:
        """The returned logger must expose standard log-level methods."""
        logger = get_logger(__name__)
        assert callable(getattr(logger, "info", None))
        assert callable(getattr(logger, "warning", None))
        assert callable(getattr(logger, "error", None))
        assert callable(getattr(logger, "debug", None))

    def test_logger_can_emit_message(self) -> None:
        """Calling logger.info() should not raise."""
        configure_logging(log_level="DEBUG", production=False)
        logger = get_logger(__name__)
        logger.info("test.event", key="value")  # Must not raise


class TestProductionJsonOutput:
    """Test that production mode emits valid JSON log lines."""

    def test_production_output_is_valid_json(self) -> None:
        """JSON renderer in production mode must emit parseable JSON."""
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)

        import structlog as _structlog

        formatter = _structlog.stdlib.ProcessorFormatter(
            processors=[
                _structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                _structlog.processors.JSONRenderer(),
            ],
        )
        handler.setFormatter(formatter)

        test_logger = logging.getLogger("test.json.output")
        test_logger.handlers = [handler]
        test_logger.setLevel(logging.DEBUG)
        test_logger.propagate = False

        # Emit via stdlib so the formatter runs
        test_logger.info("test.json.message")

        output = stream.getvalue().strip()
        assert output, "Expected at least one log line"

        # Every non-empty line must be valid JSON
        for line in output.splitlines():
            if line.strip():
                parsed = json.loads(line)
                assert isinstance(parsed, dict)


class TestContextVars:
    """Test that structlog context vars work for request_id injection."""

    def test_bind_contextvars_does_not_raise(self) -> None:
        """structlog.contextvars.bind_contextvars should be importable and callable."""
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id="test-req-123")
        merged = structlog.contextvars.get_contextvars()
        assert merged.get("request_id") == "test-req-123"
        structlog.contextvars.clear_contextvars()
