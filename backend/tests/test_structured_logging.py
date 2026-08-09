import json
import logging

from app.core.logging import JsonLogFormatter, RequestContextFilter
from app.core.request_context import request_id_context


def test_structured_log_includes_request_context_and_fields() -> None:
    token = request_id_context.set("550e8400-e29b-41d4-a716-446655440000")
    try:
        record = logging.LogRecord(
            name="app.test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="Provider request failed",
            args=(),
            exc_info=None,
        )
        record.provider = "test-provider"
        RequestContextFilter().filter(record)
        payload = json.loads(JsonLogFormatter().format(record))
    finally:
        request_id_context.reset(token)

    assert payload["level"] == "ERROR"
    assert payload["message"] == "Provider request failed"
    assert payload["request_id"] == "550e8400-e29b-41d4-a716-446655440000"
    assert payload["provider"] == "test-provider"
