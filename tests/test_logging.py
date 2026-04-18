from __future__ import annotations

import json
import logging

import pytest

import ausecon_mcp.logging as ausecon_logging
from ausecon_mcp.logging import configure_logging, get_logger


@pytest.fixture(autouse=True)
def _reset_logging_state(monkeypatch):
    namespace_logger = logging.getLogger("ausecon_mcp")
    original_handlers = list(namespace_logger.handlers)
    original_level = namespace_logger.level
    original_propagate = namespace_logger.propagate
    monkeypatch.setattr(ausecon_logging, "_CONFIGURED", False, raising=False)
    namespace_logger.handlers = []
    try:
        yield
    finally:
        namespace_logger.handlers = original_handlers
        namespace_logger.setLevel(original_level)
        namespace_logger.propagate = original_propagate
        monkeypatch.setattr(ausecon_logging, "_CONFIGURED", False, raising=False)


def test_configure_logging_is_idempotent() -> None:
    configure_logging()
    handler_count = len(logging.getLogger("ausecon_mcp").handlers)

    configure_logging()
    configure_logging()

    assert len(logging.getLogger("ausecon_mcp").handlers) == handler_count


def test_configure_logging_writes_json_to_stderr(capsys) -> None:
    configure_logging()

    get_logger("providers.abs").info("hello", extra={"source": "abs", "identifier": "CPI"})

    captured = capsys.readouterr()
    assert captured.out == ""
    payload = json.loads(captured.err.strip().splitlines()[-1])
    assert payload["msg"] == "hello"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "ausecon_mcp.providers.abs"
    assert payload["source"] == "abs"
    assert payload["identifier"] == "CPI"


def test_get_logger_namespaces_names() -> None:
    assert get_logger("cache").name == "ausecon_mcp.cache"
    assert get_logger("ausecon_mcp.providers.abs").name == "ausecon_mcp.providers.abs"


def test_logger_does_not_propagate_to_root(capsys) -> None:
    configure_logging()
    root = logging.getLogger()
    sentinel: list[str] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            sentinel.append(record.getMessage())

    handler = _Capture()
    root.addHandler(handler)
    try:
        get_logger("cache").info("no-propagate")
    finally:
        root.removeHandler(handler)

    assert sentinel == []
