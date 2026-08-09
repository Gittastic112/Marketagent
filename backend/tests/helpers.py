from typing import Any

from httpx import Response


def response_data(response: Response) -> Any:
    body = response.json()
    assert set(body) >= {"data", "meta", "errors"}
    assert body["errors"] == []
    return body["data"]


def response_errors(response: Response) -> list[dict[str, Any]]:
    body = response.json()
    assert set(body) >= {"data", "meta", "errors"}
    return body["errors"]
